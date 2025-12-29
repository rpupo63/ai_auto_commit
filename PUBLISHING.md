# Publishing Guide

This guide covers how to publish ai-auto-commit to all supported package managers.

## Table of Contents

- [PyPI (pip/pipx)](#pypi-pippipx)
- [Arch Linux (AUR/yay)](#arch-linux-auryay)
- [Debian/Ubuntu (apt)](#debianubuntu-apt)
- [Flatpak (Linux)](#flatpak-linux)
- [Homebrew (macOS/Linux)](#homebrew-macoslinux)
- [Chocolatey (Windows)](#chocolatey-windows)
- [Scoop (Windows)](#scoop-windows)
- [Winget (Windows)](#winget-windows)
- [Version Bumping](#version-bumping)

---

## PyPI (pip/pipx)

PyPI is the Python Package Index. Publishing here makes the package available via `pip` and `pipx`.

### Prerequisites

1. Create accounts on:

   - PyPI: https://pypi.org/account/register/
   - TestPyPI: https://test.pypi.org/account/register/

2. Install build tools:

   ```bash
   pip install build twine
   ```

3. Create API token on PyPI:
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token
   - Save it securely

### Publishing Steps

1. **Update version** in `pyproject.toml`

2. **Build the package**:

   ```bash
   python -m build
   ```

3. **Test on TestPyPI** (optional but recommended):

   ```bash
   twine upload --repository testpypi dist/*
   pip install --index-url https://test.pypi.org/simple/ ai-auto-commit
   ```

4. **Upload to PyPI**:

   ```bash
   twine upload dist/*
   # Enter your username: __token__
   # Enter your password: <your-api-token>
   ```

5. **Verify installation**:
   ```bash
   pip install ai-auto-commit
   autocommit --help
   ```

### Automation with GitHub Actions

Create `.github/workflows/publish-pypi.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Add `PYPI_API_TOKEN` to your GitHub repository secrets.

---

## Arch Linux (AUR/yay)

The Arch User Repository (AUR) allows Arch Linux users to install via `yay` or other AUR helpers.

### Prerequisites

1. Create an account at https://aur.archlinux.org/
2. Set up SSH keys for AUR

### Publishing Steps

1. **Create a release on GitHub**:

   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```

2. **Create source tarball**:

   ```bash
   git archive --format=tar.gz --prefix=ai-auto-commit-0.1.0/ v0.1.0 > ai-auto-commit-0.1.0.tar.gz
   ```

3. **Calculate SHA256**:

   ```bash
   sha256sum ai-auto-commit-0.1.0.tar.gz
   ```

4. **Update PKGBUILD**:

   - Update `pkgver`, `pkgrel`
   - Update `sha256sums` with the calculated hash
   - Update `url` and `source` with your GitHub URL

5. **Clone AUR repository**:

   ```bash
   git clone ssh://aur@aur.archlinux.org/ai-auto-commit.git aur-ai-auto-commit
   cd aur-ai-auto-commit
   ```

6. **Copy PKGBUILD**:

   ```bash
   cp ../PKGBUILD .
   ```

7. **Generate .SRCINFO**:

   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```

8. **Test build locally**:

   ```bash
   makepkg -si
   autocommit --help
   ```

9. **Publish to AUR**:
   ```bash
   git add PKGBUILD .SRCINFO
   git commit -m "Update to v0.1.0"
   git push
   ```

### Updating

For updates, increment `pkgrel` for packaging changes, or `pkgver` for new releases.

---

## Debian/Ubuntu (apt)

Debian packages (.deb) can be distributed via Personal Package Archives (PPA), direct .deb downloads, or Debian repositories.

### Prerequisites

1. Install build tools:

   ```bash
   sudo apt-get install devscripts debhelper dh-python python3-all python3-setuptools python3-pip
   ```

2. For PPA (optional):
   - Create a Launchpad account: https://launchpad.net/
   - Set up GPG key and upload to Launchpad
   - Create a PPA

### Publishing Steps

1. **Use generated Debian files** from `packaging/generated/debian/`:

   ```bash
   cp -r packaging/generated/debian debian/
   ```

2. **Update changelog** with new version:

   ```bash
   dch -v 0.2.0-1 "Release version 0.2.0"
   dch -r ""  # Remove release notes, keep just version
   ```

3. **Build the package**:

   ```bash
   dpkg-buildpackage -us -uc -b
   ```

   This creates:

   - `../ai-auto-commit_0.2.0-1_all.deb` - The installable package
   - `../ai-auto-commit_0.2.0-1_amd64.buildinfo` - Build info
   - `../ai-auto-commit_0.2.0-1_amd64.changes` - Changes file

4. **Test installation locally**:

   ```bash
   sudo dpkg -i ../ai-auto-commit_0.2.0-1_all.deb
   autocommit --help
   ```

5. **Distribution options**:

   **Option A: GitHub Releases (Easiest)**

   - Upload `.deb` files to GitHub releases
   - Users can download and install:
     ```bash
     wget https://github.com/yourusername/ai_auto_commit/releases/download/v0.2.0/ai-auto-commit_0.2.0-1_all.deb
     sudo dpkg -i ai-auto-commit_0.2.0-1_all.deb
     sudo apt-get install -f  # Fix dependencies if needed
     ```

   **Option B: Personal Package Archive (PPA)**

   ```bash
   # Build source package
   debuild -S

   # Upload to PPA
   dput ppa:yourusername/ppa ../ai-auto-commit_0.2.0-1_source.changes
   ```

   **Option C: Debian Repository**

   - Set up your own APT repository
   - Host packages and provide repository configuration

6. **Sign the package** (for official distribution):
   ```bash
   debuild -kYOUR_GPG_KEY_ID
   ```

### Automation

Create `.github/workflows/publish-debian.yml`:

```yaml
name: Build Debian Package

on:
  release:
    types: [published]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y devscripts debhelper dh-python python3-all
      - name: Setup Debian files
        run: cp -r packaging/generated/debian debian/
      - name: Build package
        run: dpkg-buildpackage -us -uc -b
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: debian-package
          path: ../*.deb
```

### Resources

- **Debian Packaging Guide**: https://www.debian.org/doc/manuals/debmake-doc/
- **Launchpad PPA**: https://launchpad.net/
- **PPA Guide**: https://help.launchpad.net/Packaging/PPA

---

## Flatpak (Linux)

Flatpak provides a universal package format for Linux distributions.

### Prerequisites

1. Install Flatpak build tools:

   ```bash
   # On Ubuntu/Debian
   sudo apt-get install flatpak flatpak-builder

   # On Fedora
   sudo dnf install flatpak flatpak-builder

   # On Arch Linux
   sudo pacman -S flatpak flatpak-builder
   ```

2. Add Flathub repository (if publishing to Flathub):
   ```bash
   flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
   ```

### Publishing Steps

1. **Use generated Flatpak files** from `packaging/generated/flatpak/`:

   ```bash
   cp packaging/generated/flatpak/com.github.yourusername.AIAutoCommit.yaml flatpak/
   cp packaging/generated/flatpak/com.github.yourusername.AIAutoCommit.metainfo.xml flatpak/
   ```

2. **Update version and checksums** in the YAML file:

   - Update version in source URL
   - Update SHA256 checksum for the source tarball
   - Update Python dependency checksums (if needed)

3. **Build locally** (for testing):

   ```bash
   flatpak-builder --user --install build-dir flatpak/com.github.yourusername.AIAutoCommit.yaml
   ```

4. **Test the Flatpak**:

   ```bash
   flatpak run com.github.yourusername.AIAutoCommit --help
   ```

5. **Create a Flatpak repository** (for self-hosting):

   ```bash
   flatpak-builder --repo=myrepo --force-clean build-dir flatpak/com.github.yourusername.AIAutoCommit.yaml
   flatpak build-export myrepo build-dir
   ```

6. **Distribution options**:

   **Option A: Flathub (Official)**

   - Fork https://github.com/flathub/flathub
   - Add your application manifest
   - Submit PR with:
     - `com.github.yourusername.AIAutoCommit.yaml`
     - `com.github.yourusername.AIAutoCommit.metainfo.xml`
   - Follow Flathub guidelines: https://docs.flathub.org/
   - Once approved, users can install:
     ```bash
     flatpak install flathub com.github.yourusername.AIAutoCommit
     ```

   **Option B: Self-hosted Repository**

   - Host your Flatpak repository
   - Users add it with:
     ```bash
     flatpak remote-add --if-not-exists myapp https://yourdomain.com/flatpak/repo
     flatpak install myapp com.github.yourusername.AIAutoCommit
     ```

7. **Update existing Flatpak**:
   ```bash
   flatpak-builder --user --install --force-clean build-dir flatpak/com.github.yourusername.AIAutoCommit.yaml
   ```

### Important Notes

- Flatpak requires all Python dependencies to be included as sources
- You need to manually update dependency checksums in the YAML
- Flathub has strict policies about permissions and security
- Review the generated manifest carefully before submitting

### Resources

- **Flatpak Documentation**: https://docs.flatpak.org/
- **Flathub Guidelines**: https://docs.flathub.org/
- **Flathub Applications**: https://github.com/flathub/flathub

---

## Homebrew (macOS/Linux)

Homebrew is the package manager for macOS and Linux.

### Option 1: Personal Tap (Easier)

1. **Create a tap repository** on GitHub named `homebrew-tap`

2. **Copy the formula**:

   ```bash
   mkdir -p Formula
   cp Formula/ai-auto-commit.rb homebrew-tap/Formula/
   ```

3. **Update the formula**:

   - Update `url` with actual PyPI package URL
   - Calculate and update `sha256`:
     ```bash
     curl -L https://files.pythonhosted.org/packages/source/a/ai-auto-commit/ai-auto-commit-0.1.0.tar.gz | shasum -a 256
     ```

4. **Push to GitHub**:

   ```bash
   cd homebrew-tap
   git add Formula/ai-auto-commit.rb
   git commit -m "Add ai-auto-commit formula"
   git push
   ```

5. **Install via tap**:
   ```bash
   brew tap yourusername/tap
   brew install ai-auto-commit
   ```

### Option 2: Submit to homebrew-core (Official)

This makes it available via `brew install ai-auto-commit` without tap.

1. **Requirements**:

   - Must be on PyPI
   - Must have stable releases
   - Must have decent popularity

2. **Submit PR**:
   - Fork https://github.com/Homebrew/homebrew-core
   - Add your formula to `Formula/`
   - Follow Homebrew's contribution guidelines
   - Submit PR

### Testing

```bash
brew install --build-from-source Formula/ai-auto-commit.rb
brew test ai-auto-commit
brew audit --strict ai-auto-commit
```

---

## Chocolatey (Windows)

Chocolatey is the package manager for Windows.

### Prerequisites

1. Create account at https://community.chocolatey.org/
2. Get API key from https://community.chocolatey.org/account

### Publishing Steps

1. **Install Chocolatey packaging tools**:

   ```powershell
   choco install checksum
   ```

2. **Update package files** in `chocolatey/`:

   - Update version in `ai-auto-commit.nuspec`
   - Ensure `chocolateyinstall.ps1` is correct
   - Test the package locally

3. **Pack the package**:

   ```powershell
   cd chocolatey
   choco pack
   ```

4. **Test locally** (optional):

   ```powershell
   choco install ai-auto-commit -source .
   ```

5. **Publish to Chocolatey**:

   ```powershell
   choco push ai-auto-commit.0.1.0.nupkg --source https://push.chocolatey.org/ --api-key YOUR_API_KEY
   ```

6. **Wait for approval**:
   - New packages are moderated
   - Check status at https://community.chocolatey.org/packages/ai-auto-commit

### Automation

Create `.github/workflows/publish-chocolatey.yml`:

```yaml
name: Publish to Chocolatey

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Pack Chocolatey package
        run: |
          cd chocolatey
          choco pack
      - name: Push to Chocolatey
        run: |
          cd chocolatey
          choco push *.nupkg --source https://push.chocolatey.org/ --api-key ${{ secrets.CHOCO_API_KEY }}
```

---

## Scoop (Windows)

Scoop is another Windows package manager, simpler than Chocolatey.

### Prerequisites

None required - you just need a GitHub repository.

### Publishing Steps

1. **Create a scoop bucket** (GitHub repo named `scoop-bucket`)

2. **Create manifest** `bucket/ai-auto-commit.json`:

```json
{
  "version": "0.1.0",
  "description": "AI-powered git commit and push tool with interactive setup",
  "homepage": "https://github.com/yourusername/ai_auto_commit",
  "license": "MIT",
  "depends": ["python", "git"],
  "url": "https://files.pythonhosted.org/packages/source/a/ai-auto-commit/ai-auto-commit-0.1.0.tar.gz",
  "hash": "sha256:REPLACE_WITH_ACTUAL_HASH",
  "installer": {
    "script": [
      "python -m pip install --user \"$dir\\ai-auto-commit-$version.tar.gz\"",
      "Write-Host 'Run autocommit init to get started' -ForegroundColor Green"
    ]
  },
  "uninstaller": {
    "script": "python -m pip uninstall -y ai-auto-commit"
  },
  "bin": "autocommit",
  "checkver": {
    "url": "https://pypi.org/pypi/ai-auto-commit/json",
    "jsonpath": "$.info.version"
  },
  "autoupdate": {
    "url": "https://files.pythonhosted.org/packages/source/a/ai-auto-commit/ai-auto-commit-$version.tar.gz"
  }
}
```

3. **Push to GitHub**:

   ```bash
   git add bucket/ai-auto-commit.json
   git commit -m "Add ai-auto-commit manifest"
   git push
   ```

4. **Users install via**:
   ```powershell
   scoop bucket add yourusername https://github.com/yourusername/scoop-bucket
   scoop install ai-auto-commit
   ```

### Submit to Main Bucket (Optional)

For official Scoop distribution:

1. Fork https://github.com/ScoopInstaller/Main
2. Add your manifest to `bucket/`
3. Submit PR

---

## Winget (Windows)

Windows Package Manager (winget) is Microsoft's official package manager for Windows.

### Prerequisites

1. Create a Microsoft/Azure account
2. Fork the winget-pkgs repository: https://github.com/microsoft/winget-pkgs
3. Install winget (included in Windows 10 1809+ and Windows 11)

### Publishing Steps

1. **Use generated Winget manifests** from `packaging/generated/winget/manifests/`:

   ```bash
   cp -r packaging/generated/winget/manifests/* winget/manifests/
   ```

2. **Update manifest files**:
   - `YourPublisher.AIAutoCommit.installer.yaml` - Installer configuration
   - `YourPublisher.AIAutoCommit.locale.en-US.yaml` - Metadata and descriptions
   - `ai-auto-commit.yaml` - Version manifest
3. **Ensure all required fields are correct**:

   - PackageIdentifier (e.g., `YourPublisher.AIAutoCommit`)
   - PackageVersion (must match your release version)
   - InstallerSha256 (SHA256 of installer script)
   - All URLs and checksums

4. **Create manifest directory structure**:

   ```bash
   mkdir -p manifests/y/YourPublisher/AIAutoCommit/0.2.0
   ```

   Winget uses this structure:

   - First letter of publisher (`y`)
   - Publisher name (`YourPublisher`)
   - Package name (`AIAutoCommit`)
   - Version (`0.2.0`)

5. **Copy manifest files**:

   ```bash
   cp YourPublisher.AIAutoCommit.installer.yaml manifests/y/YourPublisher/AIAutoCommit/0.2.0/
   cp YourPublisher.AIAutoCommit.locale.en-US.yaml manifests/y/YourPublisher/AIAutoCommit/0.2.0/
   cp ai-auto-commit.yaml manifests/y/YourPublisher/AIAutoCommit/0.2.0/
   ```

6. **Test manifests locally**:

   ```bash
   winget validate manifests/y/YourPublisher/AIAutoCommit/0.2.0/
   ```

7. **Submit to winget-pkgs**:

   ```bash
   cd winget-pkgs
   git checkout -b add-ai-auto-commit-0.2.0
   git add manifests/y/YourPublisher/AIAutoCommit/0.2.0/
   git commit -m "Add AI Auto Commit 0.2.0"
   git push origin add-ai-auto-commit-0.2.0
   ```

   Then create a Pull Request on GitHub.

8. **Wait for review and merge**:

   - Winget team will review your PR
   - Automated checks will validate manifests
   - Once merged, package becomes available via winget

9. **Users can install**:
   ```powershell
   winget install YourPublisher.AIAutoCommit
   ```

### Updating Existing Package

For updates, create a new version directory:

```bash
mkdir manifests/y/YourPublisher/AIAutoCommit/0.3.0
# Copy and update manifest files
# Submit PR with new version
```

### Important Notes

- Manifest format must follow winget schema exactly
- All SHA256 checksums must be correct
- PackageIdentifier must be consistent across versions
- Installer URL must be publicly accessible
- Review winget manifest guidelines before submitting

### Automation

Create `.github/workflows/publish-winget.yml`:

```yaml
name: Prepare Winget Manifests

on:
  release:
    types: [published]

jobs:
  prepare:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup manifests
        run: |
          mkdir -p winget-output/manifests/y/YourPublisher/AIAutoCommit/${{ github.event.release.tag_name }}
          cp packaging/generated/winget/manifests/* winget-output/manifests/y/YourPublisher/AIAutoCommit/${{ github.event.release.tag_name }}/
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: winget-manifests
          path: winget-output/
```

### Resources

- **Winget Repository**: https://github.com/microsoft/winget-pkgs
- **Winget Manifest Schema**: https://aka.ms/winget-manifest.schema.json
- **Winget Documentation**: https://learn.microsoft.com/en-us/windows/package-manager/
- **Submission Guidelines**: https://github.com/microsoft/winget-pkgs/blob/master/CONTRIBUTING.md

---

## Version Bumping

When releasing a new version, update these files:

1. **`pyproject.toml`**: Update `version = "0.2.0"` (source of truth)
2. **`PKGBUILD`**: Update `pkgver=0.2.0` and `pkgrel=1` (Arch Linux)
3. **`debian/changelog`**: Add new version entry (Debian/Ubuntu)
4. **`Formula/ai-auto-commit.rb`**: Update `version "0.2.0"` (Homebrew)
5. **`chocolatey/ai-auto-commit.nuspec`**: Update `<version>0.2.0</version>` (Chocolatey)
6. **`scoop/ai-auto-commit.json`**: Update `"version": "0.2.0"` (Scoop)
7. **`flatpak/com.github.yourusername.AIAutoCommit.yaml`**: Update version and checksums (Flatpak)
8. **`winget/manifests/*.yaml`**: Update `PackageVersion: 0.2.0` (Winget)

**Note**: Use the packaging system's `release_mgr.py` to automatically update most files:

```bash
cd packaging
python release_mgr.py bump-version 0.2.0
```

### Automated Version Bump Script

Create `bump-version.sh`:

```bash
#!/bin/bash
NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: ./bump-version.sh 0.2.0"
    exit 1
fi

# Update pyproject.toml
sed -i "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Update PKGBUILD
sed -i "s/pkgver=.*/pkgver=$NEW_VERSION/" PKGBUILD
sed -i "s/pkgrel=.*/pkgrel=1/" PKGBUILD

# Update Homebrew formula
sed -i "s/version \".*\"/version \"$NEW_VERSION\"/" Formula/ai-auto-commit.rb

# Update Chocolatey
sed -i "s/<version>.*<\/version>/<version>$NEW_VERSION<\/version>/" chocolatey/ai-auto-commit.nuspec

echo "Version bumped to $NEW_VERSION"
echo "Now update checksums and create git tag:"
echo "  git tag -a v$NEW_VERSION -m \"Release v$NEW_VERSION\""
echo "  git push origin v$NEW_VERSION"
```

---

## Quick Release Checklist

- [ ] Update version in all files (or use `release_mgr.py`)
- [ ] Update CHANGELOG.md
- [ ] Run tests: `pytest`
- [ ] Build and test locally: `pip install -e .`
- [ ] Create git tag: `git tag -a v0.2.0 -m "Release v0.2.0"`
- [ ] Push tag: `git push origin v0.2.0`
- [ ] Create GitHub release
- [ ] Publish to PyPI
- [ ] Update AUR PKGBUILD
- [ ] Build and publish Debian package
- [ ] Update Flatpak manifest (if applicable)
- [ ] Update Homebrew formula
- [ ] Update Chocolatey package
- [ ] Update Scoop manifest
- [ ] Update Winget manifests and submit PR
- [ ] Announce release

---

## Resources

- **PyPI**: https://pypi.org/
- **AUR**: https://aur.archlinux.org/
- **Debian Packaging**: https://www.debian.org/doc/manuals/debmake-doc/
- **Flatpak**: https://docs.flatpak.org/
- **Flathub**: https://flathub.org/
- **Homebrew**: https://brew.sh/
- **Chocolatey**: https://community.chocolatey.org/
- **Scoop**: https://scoop.sh/
- **Winget**: https://learn.microsoft.com/en-us/windows/package-manager/

For questions or issues, see the project's GitHub repository.
