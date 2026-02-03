#!/bin/bash
#
# Local CI/CD Script for ai-auto-commit
# Automates the entire release process from your local machine
#
# Usage:
#   ./scripts/local-release.sh [patch|minor|major]
#
# Example:
#   ./scripts/local-release.sh minor
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emoji support (works on most modern terminals)
CHECK="✓"
CROSS="✗"
ARROW="→"
ROCKET="🚀"
PACKAGE="📦"
TAG="🏷️"
UPLOAD="⬆️"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/release_packaging/.venv"

# Helper functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}${CHECK}${NC} $1"
}

error() {
    echo -e "${RED}${CROSS}${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

step() {
    echo -e "\n${CYAN}${ARROW}${NC} ${BOLD}$1${NC}"
}

prompt() {
    echo -e "${YELLOW}?${NC} $1"
}

header() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
}

# Check if we're in the project root
if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    error "Must be run from the project root or scripts directory"
    exit 1
fi

cd "$PROJECT_ROOT"

# Parse arguments
VERSION_PART="${1:-}"
DRY_RUN="${2:-}"

if [ -z "$VERSION_PART" ]; then
    error "Usage: $0 [patch|minor|major] [--dry-run]"
    echo ""
    echo "Examples:"
    echo "  $0 patch         # 0.1.0 → 0.1.1"
    echo "  $0 minor         # 0.1.0 → 0.2.0"
    echo "  $0 major         # 0.1.0 → 1.0.0"
    echo "  $0 patch --dry-run  # Test without making changes"
    exit 1
fi

if [ "$VERSION_PART" != "patch" ] && [ "$VERSION_PART" != "minor" ] && [ "$VERSION_PART" != "major" ]; then
    error "Invalid version part: $VERSION_PART (must be patch, minor, or major)"
    exit 1
fi

# Banner
header "${ROCKET} AI Auto Commit - Local Release Pipeline"

if [ "$DRY_RUN" = "--dry-run" ]; then
    warning "DRY RUN MODE - No changes will be made"
    echo ""
fi

# Step 1: Pre-flight checks
step "Step 1: Pre-flight Checks"

# Check for required tools
info "Checking required tools..."
MISSING_TOOLS=()

for tool in python git gh; do
    if ! command -v $tool &> /dev/null; then
        MISSING_TOOLS+=("$tool")
        error "$tool is not installed"
    else
        success "$tool found"
    fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    error "Missing required tools: ${MISSING_TOOLS[*]}"
    echo ""
    echo "Install instructions:"
    echo "  - python: https://www.python.org/downloads/"
    echo "  - git: https://git-scm.com/downloads"
    echo "  - gh (GitHub CLI): https://cli.github.com/"
    exit 1
fi

# Check git status
info "Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    warning "Working directory has uncommitted changes"
    git status --short
    echo ""
    prompt "Continue anyway? [y/N] "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        error "Aborted by user"
        exit 1
    fi
else
    success "Working directory is clean"
fi

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    warning "Not on main/master branch (current: $CURRENT_BRANCH)"
    prompt "Continue anyway? [y/N] "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        error "Aborted by user"
        exit 1
    fi
else
    success "On branch: $CURRENT_BRANCH"
fi

# Check if we're in sync with remote
info "Checking sync with remote..."
git fetch origin --quiet
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")

if [ -n "$REMOTE" ]; then
    if [ "$LOCAL" != "$REMOTE" ]; then
        warning "Local branch is not in sync with remote"
        prompt "Continue anyway? [y/N] "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            error "Aborted by user"
            exit 1
        fi
    else
        success "In sync with remote"
    fi
else
    warning "No remote tracking branch found"
fi

# Check GitHub CLI authentication
info "Checking GitHub CLI authentication..."
if gh auth status &>/dev/null; then
    success "GitHub CLI authenticated"
else
    error "GitHub CLI not authenticated"
    echo ""
    echo "Run: gh auth login"
    exit 1
fi

# Step 2: Setup virtual environment
step "Step 2: Setup Virtual Environment"

if [ ! -d "$VENV_DIR" ]; then
    info "Creating virtual environment..."
    python -m venv "$VENV_DIR"
    success "Virtual environment created"
fi

info "Installing/updating dependencies..."
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q -r "$PROJECT_ROOT/release_packaging/requirements.txt"
"$VENV_DIR/bin/pip" install -q build twine
success "Dependencies installed"

# Step 3: Get current version and calculate new version
step "Step 3: Version Bump ($VERSION_PART)"

CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
info "Current version: $CURRENT_VERSION"

# Calculate new version using Python
NEW_VERSION=$("$VENV_DIR/bin/python" -c "
import semver
v = semver.VersionInfo.parse('$CURRENT_VERSION')
if '$VERSION_PART' == 'major':
    new = v.bump_major()
elif '$VERSION_PART' == 'minor':
    new = v.bump_minor()
else:
    new = v.bump_patch()
print(str(new))
")

info "New version: $NEW_VERSION"
echo ""
prompt "Proceed with version bump to $NEW_VERSION? [Y/n] "
read -r response
if [[ "$response" =~ ^[Nn]$ ]]; then
    error "Aborted by user"
    exit 1
fi

if [ "$DRY_RUN" != "--dry-run" ]; then
    info "Bumping version in pyproject.toml and regenerating manifests..."
    "$VENV_DIR/bin/python" -m release_packaging.release_mgr bump "$VERSION_PART"
    success "Version bumped to $NEW_VERSION"
else
    success "Would bump version to $NEW_VERSION (dry run)"
fi

# Step 4: Update release notes
step "Step 4: Release Notes"

if [ "$DRY_RUN" != "--dry-run" ]; then
    warning "Please update release notes in pyproject.toml"
    echo "  [tool.package-metadata.release-notes]"
    echo ""
    prompt "Open pyproject.toml in editor? [Y/n] "
    read -r response
    if [[ ! "$response" =~ ^[Nn]$ ]]; then
        ${EDITOR:-vim} pyproject.toml
    fi

    prompt "Have you updated the release notes? [y/N] "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        warning "Skipping release notes update"
    else
        success "Release notes updated"
        # Regenerate manifests with new release notes
        info "Regenerating manifests with updated release notes..."
        "$VENV_DIR/bin/python" -m release_packaging.release_mgr generate
        success "Manifests regenerated"
    fi
else
    success "Would prompt for release notes update (dry run)"
fi

# Step 5: Run tests (if they exist)
step "Step 5: Run Tests"

if [ -f "pytest.ini" ] || [ -d "tests" ]; then
    info "Running tests..."
    if [ "$DRY_RUN" != "--dry-run" ]; then
        if "$VENV_DIR/bin/python" -m pytest tests/ 2>/dev/null; then
            success "All tests passed"
        else
            error "Tests failed"
            prompt "Continue anyway? [y/N] "
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        success "Would run tests (dry run)"
    fi
else
    warning "No tests found (skipping)"
fi

# Step 6: Validate manifests
step "Step 6: Validate Manifests"

if [ "$DRY_RUN" != "--dry-run" ]; then
    info "Validating generated manifests..."
    "$VENV_DIR/bin/python" -m release_packaging.release_mgr validate
    success "Manifests validated"
else
    success "Would validate manifests (dry run)"
fi

# Step 7: Build package
step "Step 7: Build Package"

if [ "$DRY_RUN" != "--dry-run" ]; then
    info "Building Python package..."
    "$VENV_DIR/bin/python" -m release_packaging.release_mgr build
    success "Package built and checksums calculated"

    # Show built files
    info "Built packages:"
    ls -lh dist/*$NEW_VERSION* 2>/dev/null || warning "No dist files found with version $NEW_VERSION"
else
    success "Would build package and calculate checksums (dry run)"
fi

# Step 8: Review changes
step "Step 8: Review Changes"

if [ "$DRY_RUN" != "--dry-run" ]; then
    info "Showing changes to be committed..."
    git diff --stat
    echo ""
    git diff pyproject.toml | head -30
    echo ""

    prompt "Review full diff? [y/N] "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git diff | less
    fi

    prompt "Proceed with commit and tag? [Y/n] "
    read -r response
    if [[ "$response" =~ ^[Nn]$ ]]; then
        error "Aborted by user"
        exit 1
    fi
else
    success "Would show git diff (dry run)"
fi

# Step 9: Commit changes
step "Step 9: Commit Changes"

if [ "$DRY_RUN" != "--dry-run" ]; then
    info "Staging changes..."
    git add -A

    info "Creating commit..."
    git commit -m "chore: bump version to $NEW_VERSION

- Updated version in pyproject.toml
- Regenerated all package manifests
- Updated checksums

🤖 Generated with local release script"

    success "Changes committed"
else
    success "Would commit changes (dry run)"
fi

# Step 10: Create git tag
step "Step 10: Create Git Tag"

TAG_NAME="v$NEW_VERSION"

if [ "$DRY_RUN" != "--dry-run" ]; then
    info "Creating tag: $TAG_NAME"

    # Extract release notes from pyproject.toml
    RELEASE_NOTES=$(python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
notes = data.get('tool', {}).get('package-metadata', {}).get('release-notes', {}).get('notes', 'Release $NEW_VERSION')
print(notes.strip())
" 2>/dev/null || echo "Release $NEW_VERSION")

    git tag -a "$TAG_NAME" -m "Release $NEW_VERSION

$RELEASE_NOTES"

    success "Tag created: $TAG_NAME"
else
    success "Would create tag: $TAG_NAME (dry run)"
fi

# Step 11: Push to remote
step "Step 11: Push to Remote"

if [ "$DRY_RUN" != "--dry-run" ]; then
    prompt "Push commit and tag to remote? [Y/n] "
    read -r response
    if [[ ! "$response" =~ ^[Nn]$ ]]; then
        info "Pushing to origin..."
        git push origin "$CURRENT_BRANCH"
        git push origin "$TAG_NAME"
        success "Pushed to origin"
    else
        warning "Skipped push to remote"
        echo "  Run manually: git push origin $CURRENT_BRANCH --tags"
    fi
else
    success "Would push to origin (dry run)"
fi

# Step 12: Create GitHub Release
step "Step 12: Create GitHub Release"

if [ "$DRY_RUN" != "--dry-run" ]; then
    prompt "Create GitHub release? [Y/n] "
    read -r response
    if [[ ! "$response" =~ ^[Nn]$ ]]; then
        info "Creating GitHub release..."

        # Create release with artifacts
        gh release create "$TAG_NAME" \
            --title "Release $NEW_VERSION" \
            --notes-file <(echo "$RELEASE_NOTES") \
            dist/*$NEW_VERSION* \
            release_packaging/generated/PKGBUILD \
            release_packaging/generated/Formula/ai-auto-commit.rb \
            release_packaging/generated/install.sh \
            release_packaging/generated/install.ps1

        success "GitHub release created"
        info "View at: $(gh release view $TAG_NAME --json url -q .url)"
    else
        warning "Skipped GitHub release creation"
        echo "  Run manually: gh release create $TAG_NAME"
    fi
else
    success "Would create GitHub release (dry run)"
fi

# Step 13: Publish to PyPI
step "Step 13: Publish to PyPI"

if [ "$DRY_RUN" != "--dry-run" ]; then
    prompt "Publish to PyPI? [y/N] "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        info "Publishing to PyPI..."

        # Check if PyPI credentials are configured
        if [ -f ~/.pypirc ]; then
            success "PyPI credentials found"
        else
            warning "No ~/.pypirc found"
            echo ""
            echo "Set up PyPI authentication:"
            echo "  1. Create API token at https://pypi.org/manage/account/token/"
            echo "  2. Create ~/.pypirc with your token"
            echo ""
            prompt "Continue with manual upload? [y/N] "
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                warning "Skipped PyPI upload"
                echo "  Run manually: twine upload dist/*$NEW_VERSION*"
                exit 0
            fi
        fi

        "$VENV_DIR/bin/twine" upload dist/*$NEW_VERSION*
        success "Published to PyPI"
        info "View at: https://pypi.org/project/ai-auto-commit/$NEW_VERSION/"
    else
        warning "Skipped PyPI publication"
        echo "  Run manually: twine upload dist/*$NEW_VERSION*"
    fi
else
    success "Would publish to PyPI (dry run)"
fi

# Step 14: Package Manager Instructions
step "Step 14: Update Package Managers"

header "${PACKAGE} Package Manager Updates"

echo "The release is complete! Here's what to do next for each package manager:"
echo ""

echo "${CYAN}Homebrew:${NC}"
echo "  1. Fork/clone: https://github.com/$GITHUB_USERNAME/homebrew-tap"
echo "  2. Update Formula with new version and SHA256"
echo "  3. Submit PR"
echo "  OR: cp release_packaging/generated/Formula/ai-auto-commit.rb ../homebrew-tap/Formula/"
echo ""

echo "${CYAN}Arch Linux (AUR):${NC}"
echo "  1. Clone AUR repo: git clone ssh://aur@aur.archlinux.org/ai-auto-commit.git"
echo "  2. cp release_packaging/generated/PKGBUILD aur-repo/"
echo "  3. cd aur-repo && makepkg --printsrcinfo > .SRCINFO"
echo "  4. git commit -am 'Update to $NEW_VERSION' && git push"
echo ""

echo "${CYAN}Chocolatey:${NC}"
echo "  1. Update package at https://push.chocolatey.org/"
echo "  2. Upload release_packaging/generated/chocolatey/"
echo ""

echo "${CYAN}Scoop:${NC}"
echo "  1. Fork/clone scoop bucket"
echo "  2. cp release_packaging/generated/scoop/ai-auto-commit.json bucket/"
echo "  3. Submit PR"
echo ""

echo "${CYAN}WinGet:${NC}"
echo "  1. Fork: https://github.com/microsoft/winget-pkgs"
echo "  2. Create manifests in manifests/y/YourPublisher/AIAutoCommit/$NEW_VERSION/"
echo "  3. Copy files from release_packaging/generated/winget/manifests/"
echo "  4. Submit PR"
echo ""

echo "${CYAN}Flatpak:${NC}"
echo "  Note: Flatpak requires significant manual work to generate dependency sources"
echo "  Generated base files are in release_packaging/generated/flatpak/"
echo ""

echo "${CYAN}Debian:${NC}"
echo "  Generated files are in release_packaging/generated/debian/"
echo "  Consider setting up a PPA or providing .deb files via GitHub releases"
echo ""

# Final summary
header "${ROCKET} Release Complete!"

echo -e "${GREEN}Version:${NC}    $NEW_VERSION"
echo -e "${GREEN}Tag:${NC}        $TAG_NAME"
echo -e "${GREEN}Commit:${NC}     $(git rev-parse --short HEAD)"
echo -e "${GREEN}GitHub:${NC}     https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/releases/tag/$TAG_NAME"
echo -e "${GREEN}PyPI:${NC}       https://pypi.org/project/ai-auto-commit/$NEW_VERSION/"
echo ""

success "All done! ${ROCKET}"
echo ""

# Save release summary
SUMMARY_FILE="release-$NEW_VERSION-summary.txt"
cat > "$SUMMARY_FILE" <<EOF
Release Summary for $NEW_VERSION
Generated: $(date)

Version: $NEW_VERSION
Tag: $TAG_NAME
Commit: $(git rev-parse HEAD)

Release Notes:
$RELEASE_NOTES

Files Built:
$(ls -lh dist/*$NEW_VERSION* 2>/dev/null || echo "None")

Next Steps:
- Update package managers (see script output)
- Announce release
- Update documentation if needed

---
Generated by local-release.sh
EOF

info "Release summary saved to: $SUMMARY_FILE"
