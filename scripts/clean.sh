#!/bin/bash
#
# Cleanup Script
# Removes build artifacts, caches, and temporary files
#
# Usage:
#   ./scripts/clean.sh [--all]
#
# Options:
#   --all    Also remove virtual environments and backups
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

DEEP_CLEAN="${1:-}"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  🧹 Cleanup"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Standard cleanup
echo "Cleaning build artifacts..."

# Python build artifacts
if [ -d "build" ]; then
    rm -rf build/
    echo -e "${GREEN}✓${NC} Removed build/"
fi

if [ -d "dist" ]; then
    rm -rf dist/
    echo -e "${GREEN}✓${NC} Removed dist/"
fi

find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null && echo -e "${GREEN}✓${NC} Removed *.egg-info"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null && echo -e "${GREEN}✓${NC} Removed __pycache__"
find . -type f -name "*.pyc" -delete 2>/dev/null && echo -e "${GREEN}✓${NC} Removed *.pyc files"
find . -type f -name "*.pyo" -delete 2>/dev/null && echo -e "${GREEN}✓${NC} Removed *.pyo files"

# Test artifacts
if [ -d ".pytest_cache" ]; then
    rm -rf .pytest_cache/
    echo -e "${GREEN}✓${NC} Removed .pytest_cache/"
fi

if [ -d ".coverage" ]; then
    rm -rf .coverage
    echo -e "${GREEN}✓${NC} Removed .coverage"
fi

if [ -d "htmlcov" ]; then
    rm -rf htmlcov/
    echo -e "${GREEN}✓${NC} Removed htmlcov/"
fi

# Release summaries
if ls release-*-summary.txt 1> /dev/null 2>&1; then
    rm -f release-*-summary.txt
    echo -e "${GREEN}✓${NC} Removed release summaries"
fi

# Temporary files
find . -type f -name "*~" -delete 2>/dev/null && echo -e "${GREEN}✓${NC} Removed backup files (*~)"
find . -type f -name "*.swp" -delete 2>/dev/null && echo -e "${GREEN}✓${NC} Removed vim swap files"

if [ "$DEEP_CLEAN" = "--all" ]; then
    echo ""
    echo -e "${YELLOW}Deep cleaning...${NC}"

    # Remove virtual environment
    if [ -d "release_packaging/.venv" ]; then
        rm -rf release_packaging/.venv/
        echo -e "${GREEN}✓${NC} Removed release_packaging/.venv/"
    fi

    # Remove backups (be careful!)
    if [ -d "release_packaging/backup" ]; then
        echo -e "${YELLOW}⚠${NC} Removing release_packaging/backup/"
        rm -rf release_packaging/backup/
        echo -e "${GREEN}✓${NC} Removed release_packaging/backup/"
    fi

    # Remove generated files (they can be regenerated)
    if [ -d "release_packaging/generated" ]; then
        echo -e "${YELLOW}⚠${NC} Removing release_packaging/generated/"
        rm -rf release_packaging/generated/
        echo -e "${GREEN}✓${NC} Removed release_packaging/generated/"
    fi
fi

echo ""
echo -e "${GREEN}✓${NC} Cleanup complete!"

if [ "$DEEP_CLEAN" != "--all" ]; then
    echo ""
    echo "For deep clean (removes venv, backups, generated files):"
    echo "  ./scripts/clean.sh --all"
fi

echo ""
