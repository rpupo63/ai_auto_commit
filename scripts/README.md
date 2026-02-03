# Release & Deployment Scripts

This directory contains local CI/CD scripts for managing releases from your computer.

## Scripts Overview

### 🚀 `local-release.sh` - Complete Release Automation

**The main release script.** Automates the entire release process from your local machine.

```bash
# Patch release (0.1.0 → 0.1.1)
./scripts/local-release.sh patch

# Minor release (0.1.0 → 0.2.0)
./scripts/local-release.sh minor

# Major release (0.1.0 → 1.0.0)
./scripts/local-release.sh major

# Dry run (test without making changes)
./scripts/local-release.sh minor --dry-run
```

**What it does:**

1. ✅ **Pre-flight checks**
   - Validates git status (clean working directory)
   - Checks you're on main/master branch
   - Verifies sync with remote
   - Confirms GitHub CLI authentication
   - Checks for required tools (python, git, gh)

2. 🔧 **Setup**
   - Creates/updates virtual environment
   - Installs dependencies (jinja2, tomli, semver, build, twine)

3. 📊 **Version bump**
   - Calculates new version (semantic versioning)
   - Updates `pyproject.toml`
   - Regenerates all package manifests

4. 📝 **Release notes**
   - Prompts you to update release notes
   - Opens editor for `pyproject.toml`
   - Regenerates manifests with updated notes

5. 🧪 **Testing**
   - Runs pytest tests (if available)
   - Validates all generated manifests

6. 📦 **Build**
   - Builds Python package (sdist + wheel)
   - Calculates SHA256 checksums
   - Updates manifests with checksums

7. 🔍 **Review**
   - Shows git diff of changes
   - Prompts for confirmation

8. 💾 **Commit**
   - Stages all changes
   - Creates commit with standard message
   - Creates git tag with release notes

9. ⬆️ **Push**
   - Pushes commit to origin
   - Pushes tag to origin

10. 🎉 **GitHub Release**
    - Creates GitHub release via `gh` CLI
    - Uploads package artifacts
    - Uploads key manifest files (PKGBUILD, Formula, install scripts)

11. 📤 **PyPI Publication**
    - Publishes to PyPI via `twine`
    - Shows PyPI package URL

12. 📋 **Package Manager Instructions**
    - Provides step-by-step instructions for updating:
      - Homebrew
      - Arch Linux (AUR)
      - Chocolatey
      - Scoop
      - WinGet
      - Flatpak
      - Debian

13. 📄 **Release Summary**
    - Generates `release-{version}-summary.txt` with all details

### 🔍 `validate.sh` - Quick Validation

**Pre-release validation script.** Checks everything is ready without making changes.

```bash
./scripts/validate.sh
```

**Checks:**
- Git status (uncommitted changes)
- Current branch (main/master)
- Python availability
- Virtual environment exists
- pyproject.toml is valid TOML
- GitHub CLI authentication
- Required files present
- Templates exist
- Manifest generation works
- Package structure is valid

**Exit codes:**
- `0` - All checks passed or only warnings
- `1` - Errors found

### 🧹 `clean.sh` - Cleanup

**Removes build artifacts and temporary files.**

```bash
# Standard cleanup
./scripts/clean.sh

# Deep clean (removes venv, backups, generated files)
./scripts/clean.sh --all
```

**Standard cleanup removes:**
- `build/` directory
- `dist/` directory
- `*.egg-info` directories
- `__pycache__` directories
- `*.pyc`, `*.pyo` files
- `.pytest_cache/`
- `.coverage` files
- `htmlcov/`
- Release summary files
- Editor backups (`*~`, `*.swp`)

**Deep cleanup also removes:**
- `release_packaging/.venv/` (virtual environment)
- `release_packaging/backup/` (original file backups)
- `release_packaging/generated/` (generated manifests)

⚠️ **Warning:** Deep clean removes files that may take time to regenerate. Only use when you know what you're doing.

## Typical Workflow

### Making a Release

1. **Validate everything is ready:**
   ```bash
   ./scripts/validate.sh
   ```

2. **Run the release script:**
   ```bash
   ./scripts/local-release.sh minor
   ```

3. **Follow the prompts:**
   - Review and confirm version bump
   - Update release notes when prompted
   - Review changes before committing
   - Confirm push to remote
   - Confirm GitHub release creation
   - Confirm PyPI publication

4. **Update package managers:**
   - Follow the instructions printed by the script
   - Update Homebrew tap
   - Update AUR package
   - Submit PRs to other package managers

### Quick Development Cycle

```bash
# Make changes to code
vim ai_auto_commit/cli.py

# Test locally
python -m ai_auto_commit.cli

# Validate release_packaging system
./scripts/validate.sh

# Clean build artifacts
./scripts/clean.sh
```

### Testing Release Process

Use dry-run mode to test without making changes:

```bash
./scripts/local-release.sh patch --dry-run
```

This will:
- Show what would be done
- Not modify any files
- Not create commits or tags
- Not push to remote
- Not create GitHub releases
- Not publish to PyPI

## Prerequisites

### Required Tools

1. **Python 3.8+**
   ```bash
   python --version
   ```

2. **Git**
   ```bash
   git --version
   ```

3. **GitHub CLI (`gh`)**
   ```bash
   # Install
   # macOS: brew install gh
   # Arch: sudo pacman -S github-cli
   # Debian/Ubuntu: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md

   # Authenticate
   gh auth login
   ```

4. **PyPI API Token** (for publishing)
   - Create token at: https://pypi.org/manage/account/token/
   - Create `~/.pypirc`:
     ```ini
     [pypi]
     username = __token__
     password = pypi-AgEIcHlwaS...
     ```

### Environment Setup

All dependencies are automatically installed in a virtual environment on first run. However, you can set it up manually:

```bash
python -m venv release_packaging/.venv
release_packaging/.venv/bin/pip install -r release_packaging/requirements.txt
release_packaging/.venv/bin/pip install build twine
```

## Troubleshooting

### "GitHub CLI not authenticated"

Run:
```bash
gh auth login
```

### "PyPI credentials not found"

Create `~/.pypirc` with your API token (see Prerequisites above).

### "Working directory has uncommitted changes"

Either:
1. Commit your changes: `git commit -am "your message"`
2. Stash them: `git stash`
3. Continue anyway when prompted (not recommended)

### "Not on main/master branch"

Switch to main:
```bash
git checkout main
```

### "Local branch not in sync with remote"

Pull latest changes:
```bash
git pull origin main
```

### Script hangs or fails

1. Check internet connection
2. Verify GitHub is accessible
3. Check PyPI is accessible
4. Run with dry-run to see where it fails:
   ```bash
   ./scripts/local-release.sh patch --dry-run
   ```

### Want to undo a failed release

If you pushed to remote but want to undo:
```bash
# Delete local tag
git tag -d v0.2.0

# Delete remote tag
git push --delete origin v0.2.0

# Reset to previous commit
git reset --hard HEAD~1

# Force push (careful!)
git push --force origin main
```

If you published to PyPI, you **cannot** delete or replace the version. You must bump to a new version (e.g., 0.2.1).

## Customization

### Modify Release Script

Edit `scripts/local-release.sh` to:
- Change commit message format
- Add additional validation steps
- Customize GitHub release notes
- Add/remove package manager instructions

### Skip Steps

Comment out sections you don't need. For example, to skip PyPI publication, comment out Step 13.

### Add Pre/Post Hooks

Add custom hooks before/after steps:

```bash
# After Step 5 (tests)
if [ -f "scripts/custom-checks.sh" ]; then
    ./scripts/custom-checks.sh
fi
```

## Integration with CI/CD

While these scripts are designed for **local use**, you can adapt them for CI/CD:

### GitHub Actions

```yaml
name: Release
on:
  workflow_dispatch:
    inputs:
      version:
        required: true
        type: choice
        options:
          - patch
          - minor
          - major

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run release script
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
        run: |
          ./scripts/local-release.sh ${{ inputs.version }}
```

But since you chose local scripts, this is just for reference.

## Best Practices

1. **Always run validation first:**
   ```bash
   ./scripts/validate.sh && ./scripts/local-release.sh minor
   ```

2. **Use dry-run for testing:**
   ```bash
   ./scripts/local-release.sh patch --dry-run
   ```

3. **Review changes carefully** before confirming the commit step

4. **Keep main branch clean** - only release from main/master

5. **Test before releasing:**
   - Run tests locally
   - Test installation from built package
   - Verify manifests are correct

6. **Update release notes** with meaningful information, not just "bug fixes"

7. **Clean up regularly:**
   ```bash
   ./scripts/clean.sh
   ```

## License

These scripts are part of ai-auto-commit and follow the same license (MIT).
