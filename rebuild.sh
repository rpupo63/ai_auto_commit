#!/bin/bash
# Rebuild and install ai-auto-commit as a pacman package
set -e

cd "$(dirname "$0")"

echo "Cleaning build artifacts..."
rm -rf dist build pkg src *.egg-info *.pkg.tar.zst

echo "Building and installing..."
makepkg -sf --noconfirm
sudo pacman -U --noconfirm ai-auto-commit-*.pkg.tar.zst

echo "Installed: $(pacman -Q ai-auto-commit)"
