#!/bin/bash
# Wrapper for new Python-based release management tool
# The old bash script has been moved to packaging/backup/bump-version.sh.old

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/packaging/.venv"

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up virtual environment..."
    python -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -q -r "$SCRIPT_DIR/packaging/requirements.txt"
fi

# Run the new release manager tool
"$VENV_DIR/bin/python" -m packaging.release_mgr bump "$@"
