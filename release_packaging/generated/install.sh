#!/bin/bash
# Quick install script for ai-auto-commit
# Supports multiple platforms and package managers

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "  AI Auto Commit - Installation Script"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="windows"
else
    OS="unknown"
fi

echo "Detected OS: $OS"
echo ""

# Function to install via pip
install_via_pip() {
    echo "Installing via pip..."
    if command -v pip3 &> /dev/null; then
        pip3 install --user ai-auto-commit
    elif command -v pip &> /dev/null; then
        pip install --user ai-auto-commit
    else
        echo "Error: pip not found. Please install Python and pip first."
        exit 1
    fi
}

# Install based on OS and available package managers
if [[ "$OS" == "linux" ]]; then
    # Check for Flatpak first (universal)
    if command -v flatpak &> /dev/null; then
        echo "Flatpak detected. Installing via Flatpak..."
        flatpak install --user -y flathub com.github.yourusername.AIAutoCommit
    # Check for Arch Linux (yay/pacman)
    elif command -v yay &> /dev/null; then
        echo "Installing via yay (Arch Linux)..."
        yay -S ai-auto-commit
    elif command -v pacman &> /dev/null && [ -f /etc/arch-release ]; then
        echo "Arch Linux detected, but yay not found."
        echo "Please install yay first, or use pip:"
        install_via_pip
    # Check for apt (Debian/Ubuntu)
    elif command -v apt &> /dev/null; then
        echo "Debian/Ubuntu detected."
        echo "Installing via apt..."
        # Add repository (if applicable) or install .deb package
        # For now, use pip
        echo "Debian package will be available soon. Using pip for now..."
        install_via_pip
    # Check for dnf (Fedora)
    elif command -v dnf &> /dev/null; then
        echo "Fedora detected. Using pip..."
        install_via_pip
    else
        echo "No supported package manager found. Installing via pip..."
        install_via_pip
    fi
elif [[ "$OS" == "macos" ]]; then
    # Check for Homebrew
    if command -v brew &> /dev/null; then
        echo "Installing via Homebrew..."
        brew install yourusername/tap/ai-auto-commit
    else
        echo "Homebrew not found. Installing via pip..."
        install_via_pip
    fi
elif [[ "$OS" == "windows" ]]; then
    echo "For Windows, please use one of these methods:"
    echo "  1. Chocolatey: choco install ai-auto-commit"
    echo "  2. Scoop: scoop install ai-auto-commit"
    echo "  3. pip: pip install ai-auto-commit"
    exit 0
else
    echo "Unknown OS. Installing via pip..."
    install_via_pip
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Installation complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
To get started, run the interactive setup wizard:
  autocommit init

This will guide you through:
  • Configuring AI provider API keys
  • Setting your default model
  • Configuring token budget

For more information:
  autocommit --help

echo ""
