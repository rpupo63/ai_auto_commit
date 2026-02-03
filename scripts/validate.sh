#!/bin/bash
#
# Quick Validation Script
# Runs all pre-release checks without making any changes
#
# Usage:
#   ./scripts/validate.sh
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

CHECK="✓"
CROSS="✗"
WARN="⚠"

# Get to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  🔍 Pre-Release Validation"
echo "═══════════════════════════════════════════════════════════════"
echo ""

ERRORS=0
WARNINGS=0

# 1. Check git status
echo "Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}${WARN}${NC} Uncommitted changes found"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}${CHECK}${NC} Working directory clean"
fi

# 2. Check branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ] && [ "$BRANCH" != "master" ]; then
    echo -e "${YELLOW}${WARN}${NC} Not on main/master (current: $BRANCH)"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}${CHECK}${NC} On branch: $BRANCH"
fi

# 3. Check Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}${CROSS}${NC} Python not found"
    ERRORS=$((ERRORS + 1))
else
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}${CHECK}${NC} Python $PYTHON_VERSION"
fi

# 4. Check virtual environment
VENV_DIR="$PROJECT_ROOT/release_packaging/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}${WARN}${NC} Virtual environment not found (will be created on first run)"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}${CHECK}${NC} Virtual environment exists"
fi

# 5. Validate pyproject.toml
echo "Validating pyproject.toml..."
if python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))" 2>/dev/null; then
    echo -e "${GREEN}${CHECK}${NC} pyproject.toml is valid TOML"
elif python -c "import tomli; tomli.load(open('pyproject.toml', 'rb'))" 2>/dev/null; then
    echo -e "${GREEN}${CHECK}${NC} pyproject.toml is valid TOML"
else
    echo -e "${RED}${CROSS}${NC} pyproject.toml is invalid"
    ERRORS=$((ERRORS + 1))
fi

# 6. Check GitHub CLI
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}${WARN}${NC} GitHub CLI (gh) not installed"
    WARNINGS=$((WARNINGS + 1))
else
    if gh auth status &>/dev/null; then
        echo -e "${GREEN}${CHECK}${NC} GitHub CLI authenticated"
    else
        echo -e "${RED}${CROSS}${NC} GitHub CLI not authenticated (run: gh auth login)"
        ERRORS=$((ERRORS + 1))
    fi
fi

# 7. Check for required files
echo "Checking required files..."
REQUIRED_FILES=(
    "pyproject.toml"
    "README.md"
    "LICENSE"
    "release_packaging/release_mgr.py"
    "release_packaging/requirements.txt"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}${CHECK}${NC} $file"
    else
        echo -e "${RED}${CROSS}${NC} Missing: $file"
        ERRORS=$((ERRORS + 1))
    fi
done

# 8. Check templates
echo "Checking templates..."
TEMPLATE_COUNT=$(find release_packaging/templates -name "*.j2" 2>/dev/null | wc -l)
if [ "$TEMPLATE_COUNT" -ge 14 ]; then
    echo -e "${GREEN}${CHECK}${NC} Found $TEMPLATE_COUNT templates"
else
    echo -e "${YELLOW}${WARN}${NC} Only $TEMPLATE_COUNT templates found (expected 14+)"
    WARNINGS=$((WARNINGS + 1))
fi

# 9. Dry run manifest generation
if [ -d "$VENV_DIR" ]; then
    echo "Testing manifest generation..."
    if "$VENV_DIR/bin/python" -m release_packaging.release_mgr validate 2>/dev/null; then
        echo -e "${GREEN}${CHECK}${NC} Manifests can be generated"
    else
        echo -e "${RED}${CROSS}${NC} Manifest generation failed"
        ERRORS=$((ERRORS + 1))
    fi
fi

# 10. Check package structure
echo "Checking package structure..."
if [ -d "ai_auto_commit" ]; then
    if [ -f "ai_auto_commit/__init__.py" ]; then
        echo -e "${GREEN}${CHECK}${NC} Package structure valid"
    else
        echo -e "${RED}${CROSS}${NC} Missing ai_auto_commit/__init__.py"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}${CROSS}${NC} Package directory not found"
    ERRORS=$((ERRORS + 1))
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════════"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}${CHECK} All checks passed!${NC}"
    echo "Ready to release."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}${WARN} $WARNINGS warning(s) found${NC}"
    echo "You can proceed, but review the warnings above."
    exit 0
else
    echo -e "${RED}${CROSS} $ERRORS error(s) and $WARNINGS warning(s) found${NC}"
    echo "Fix errors before releasing."
    exit 1
fi
