#!/usr/bin/env bash
# Install autocommit globally from this repo (editable). Stays in sync with repo—no reinstall after pull.
set -e
cd "$(dirname "$0")"
if ! command -v pipx &>/dev/null; then
  echo "pipx is required. Install it first:"
  echo "  https://pypa.github.io/pipx/"
  echo "  e.g. pacman -S python-pipx  (Arch) or pip install pipx"
  exit 1
fi
if [ -n "${PIPX_FORCE:-}" ]; then
  pipx install -e . --force
else
  pipx install -e .
fi
echo ""
echo "Done. Run 'autocommit' from any directory; it uses this repo's latest code."
