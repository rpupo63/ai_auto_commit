# Quick Start Guide - Local Release Scripts

## 🚀 First Time Setup

1. **Install GitHub CLI:**
   ```bash
   # Arch Linux
   sudo pacman -S github-cli

   # Or from https://cli.github.com/
   ```

2. **Authenticate with GitHub:**
   ```bash
   gh auth login
   ```

3. **Create PyPI API token:**
   - Go to https://pypi.org/manage/account/token/
   - Create token with "Upload packages" scope
   - Save to `~/.pypirc`:
     ```ini
     [pypi]
     username = __token__
     password = pypi-AgEIcHlwaS5vcmcC...YOUR_TOKEN_HERE
     ```

4. **Initialize git repository (if not done):**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/ai_auto_commit.git
   git push -u origin main
   ```

## 📋 Quick Commands

### Validate before release
```bash
./scripts/validate.sh
```

### Release (interactive, guided)
```bash
# Patch: 0.1.0 → 0.1.1
./scripts/local-release.sh patch

# Minor: 0.1.0 → 0.2.0
./scripts/local-release.sh minor

# Major: 0.1.0 → 1.0.0
./scripts/local-release.sh major
```

### Test release (dry run)
```bash
./scripts/local-release.sh minor --dry-run
```

### Clean build artifacts
```bash
./scripts/clean.sh
```

### Deep clean (removes venv too)
```bash
./scripts/clean.sh --all
```

## 🎯 Typical Release Workflow

```bash
# 1. Make your changes
vim ai_auto_commit/cli.py

# 2. Test locally
python -m ai_auto_commit.cli --help

# 3. Commit your work
git add .
git commit -m "feat: add new feature"
git push

# 4. Validate everything
./scripts/validate.sh

# 5. Run release (it will prompt for confirmations)
./scripts/local-release.sh minor

# 6. Follow the prompts:
#    - Confirm version bump
#    - Update release notes when prompted
#    - Review git diff
#    - Confirm push to GitHub
#    - Confirm GitHub release
#    - Confirm PyPI publish

# 7. Update package managers (instructions printed by script)
```

## ⚡ What the Release Script Does

1. ✅ Checks git status, branch, and remote sync
2. 🔧 Sets up Python virtual environment
3. 📊 Bumps version in pyproject.toml
4. 📝 Prompts for release notes update
5. 🧪 Runs tests (if available)
6. 📦 Builds package + calculates checksums
7. 🔍 Shows changes for review
8. 💾 Commits changes + creates git tag
9. ⬆️ Pushes to GitHub
10. 🎉 Creates GitHub release with artifacts
11. 📤 Publishes to PyPI
12. 📋 Shows package manager update instructions

## 🆘 Troubleshooting

**"GitHub CLI not authenticated"**
```bash
gh auth login
```

**"PyPI credentials not found"**
Create `~/.pypirc` with your API token (see setup above)

**"Uncommitted changes"**
```bash
git status
git commit -am "your message"
```

**"Not on main branch"**
```bash
git checkout main
```

**Script fails partway through**
- Check the error message
- Run with `--dry-run` to test
- Check internet connection
- Verify GitHub/PyPI are accessible

## 📚 More Information

- Full documentation: `scripts/README.md`
- Packaging system: `release_packaging/README.md`
- Release plan: `.claude/plans/delightful-finding-phoenix.md`
