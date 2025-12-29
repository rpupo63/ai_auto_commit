# Package Distribution System

This directory contains the template-based package distribution system for `ai-auto-commit`, which generates package manifests for 7 different package managers from a single source of truth.

## Overview

The packaging system eliminates redundancy by:
- Using `pyproject.toml` as the **single source of truth** for all metadata
- Generating package manifests from **Jinja2 templates**
- Providing a Python tool (`release_mgr.py`) for **automated version bumping** and **checksum calculation**

## Directory Structure

```
packaging/
├── __init__.py                  # Package initialization
├── release_mgr.py               # Release management tool (main script)
├── requirements.txt             # Python dependencies for tooling
├── README.md                    # This file
├── .venv/                       # Virtual environment (created automatically)
├── templates/                   # Jinja2 templates for all package managers
│   ├── PKGBUILD.j2
│   ├── Formula.rb.j2
│   ├── nuspec.xml.j2
│   ├── chocolatey-install.ps1.j2
│   ├── chocolatey-uninstall.ps1.j2
│   ├── scoop.json.j2
│   ├── winget-installer.yaml.j2
│   ├── winget-locale.yaml.j2
│   ├── winget-version.yaml.j2
│   ├── flatpak.yaml.j2
│   ├── flatpak-metainfo.xml.j2
│   ├── debian-control.j2
│   ├── debian-changelog.j2
│   ├── debian-postinst.j2
│   ├── install.sh.j2
│   └── install.ps1.j2
├── generated/                   # Generated manifests (git-tracked)
│   ├── PKGBUILD
│   ├── Formula/
│   ├── chocolatey/
│   ├── scoop/
│   ├── winget/
│   ├── flatpak/
│   ├── debian/
│   ├── install.sh
│   └── install.ps1
└── backup/                      # Backups of original files (for rollback)
```

## Usage

### Prerequisites

Install Python dependencies (automatic on first use):

```bash
python -m venv packaging/.venv
packaging/.venv/bin/pip install -r packaging/requirements.txt
```

Or use the tool directly (creates venv automatically):

```bash
python -m packaging.release_mgr --help
```

### Commands

#### Generate All Manifests

Generate all package manifests from templates:

```bash
python -m packaging.release_mgr generate
```

This reads metadata from `pyproject.toml` and renders all templates in `packaging/templates/` to `packaging/generated/`.

#### Bump Version

Bump the version using semantic versioning:

```bash
# Bump patch version: 0.1.0 → 0.1.1
python -m packaging.release_mgr bump patch

# Bump minor version: 0.1.0 → 0.2.0
python -m packaging.release_mgr bump minor

# Bump major version: 0.1.0 → 1.0.0
python -m packaging.release_mgr bump major
```

This will:
1. Update the version in `pyproject.toml`
2. Regenerate all package manifests with the new version
3. Display next steps for the release process

#### Build Package and Calculate Checksums

Build the Python package and automatically calculate SHA256 checksums:

```bash
python -m packaging.release_mgr build
```

This will:
1. Run `python -m build` to create the distribution package
2. Calculate the SHA256 checksum of the tarball
3. Update `pyproject.toml` with the checksum
4. Regenerate all manifests with the new checksum

#### Validate Manifests

Validate that all expected manifest files exist:

```bash
python -m packaging.release_mgr validate
```

## Metadata Configuration

All package metadata is centralized in `pyproject.toml` under the `[tool.package-metadata]` section:

```toml
[tool.package-metadata]
# Publisher information
publisher = "Your Name"
publisher_email = "your.email@example.com"
github_username = "yourusername"
github_repo = "ai_auto_commit"

# Descriptions
short_description = "AI-powered git commit and push tool"
long_description = """
Full description here...
"""

# Features (used in WinGet, Flatpak, Debian)
features = [
    "Feature 1: Description",
    "Feature 2: Description"
]

# Post-install message (unified across all package managers)
post_install_message = """
Message shown after installation...
"""

# Package-specific overrides
[tool.package-metadata.debian]
section = "utils"
priority = "optional"

# Release notes
[tool.package-metadata.release-notes]
version = "0.1.0"
date = "2025-12-27"
notes = """
Release notes here...
"""

# Checksums (auto-populated by build command)
[tool.package-metadata.checksums]
sha256 = "abc123..."
tarball_url = "https://..."
```

## Template System

Templates use Jinja2 syntax and have access to all metadata via the `{{ metadata }}` variable:

### Available Template Variables

- `{{ metadata.version }}` - Version from `[project]`
- `{{ metadata.name }}` - Package name
- `{{ metadata.description }}` - Short description
- `{{ metadata.long_description }}` - Long description
- `{{ metadata.license }}` - License type
- `{{ metadata.homepage }}` - Homepage URL
- `{{ metadata.repository }}` - Repository URL
- `{{ metadata.publisher }}` - Publisher name
- `{{ metadata.publisher_email }}` - Publisher email
- `{{ metadata.github_username }}` - GitHub username
- `{{ metadata.post_install_message }}` - Post-install message
- `{{ metadata.features }}` - List of features
- `{{ metadata.keywords }}` - List of keywords
- `{{ metadata.checksums.sha256 }}` - Package checksum

### Custom Jinja2 Filters

- `{{ text | indent(width) }}` - Indent text by `width` spaces
- `{{ text | regex_replace(pattern, replacement) }}` - Regex replacement

### Example Template

```jinja2
# Maintainer: {{ metadata.publisher }} <{{ metadata.publisher_email }}>
pkgname=ai-auto-commit
pkgver={{ metadata.version }}
pkgdesc="{{ metadata.description }}"
url="{{ metadata.homepage }}"
sha256sums=('{{ metadata.checksums.sha256 or "SKIP" }}')
```

## Release Workflow

### Standard Release Process

1. **Update release notes** in `pyproject.toml`:
   ```toml
   [tool.package-metadata.release-notes]
   version = "0.2.0"
   date = "2025-12-28"
   notes = """
   - New feature X
   - Bug fix Y
   """
   ```

2. **Bump version**:
   ```bash
   python -m packaging.release_mgr bump minor
   ```

3. **Build package and calculate checksums**:
   ```bash
   python -m packaging.release_mgr build
   ```

4. **Review changes**:
   ```bash
   git diff
   ```

5. **Commit and tag**:
   ```bash
   git add -A
   git commit -m "chore: bump version to 0.2.0"
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin main --tags
   ```

6. **Create GitHub release** manually with generated manifests

7. **Publish to package managers** (see main PUBLISHING.md)

## Troubleshooting

### "Template not found" error

Make sure you're running from the project root directory:

```bash
cd /path/to/ai_auto_commit
python -m packaging.release_mgr generate
```

### "Module not found" error

Install dependencies in a virtual environment:

```bash
python -m venv packaging/.venv
packaging/.venv/bin/pip install -r packaging/requirements.txt
packaging/.venv/bin/python -m packaging.release_mgr generate
```

### Generated files differ from originals

This is expected! The generated files use the unified metadata from `pyproject.toml`, which may format things differently. Compare the content to ensure all important information is preserved.

To restore original files if needed:

```bash
cp -r packaging/backup/* .
```

## Maintenance

### Adding a New Package Manager

1. Create a new template in `packaging/templates/`
2. Add the template mapping to `release_mgr.py` in the `manifest_map` dictionary
3. Regenerate: `python -m packaging.release_mgr generate`

### Updating Metadata

Edit `pyproject.toml` and regenerate:

```bash
# Edit pyproject.toml
vim pyproject.toml

# Regenerate all manifests
python -m packaging.release_mgr generate
```

### Updating Templates

1. Edit templates in `packaging/templates/`
2. Regenerate to apply changes:
   ```bash
   python -m packaging.release_mgr generate
   ```
3. Review the diff:
   ```bash
   git diff
   ```

## Benefits

### Before (Manual Process)

- ❌ Version number hardcoded in 8-9 files
- ❌ Description duplicated in 6+ files with variations
- ❌ Post-install messages identical but separately maintained in 5 files
- ❌ Manual checksum calculation prone to errors
- ❌ Fragile sed-based version bumping script
- ❌ 15+ manual steps for each release

### After (Template System)

- ✅ Version in ONE file (pyproject.toml)
- ✅ Description from single source
- ✅ Post-install message unified
- ✅ Automated checksum calculation
- ✅ Type-safe Python tool with validation
- ✅ 3 commands for a complete release

## Architecture

```
┌─────────────────────────────────────────┐
│      pyproject.toml                     │
│  (Single Source of Truth)               │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Template Engine (Jinja2)           │
│  - PKGBUILD.j2                          │
│  - Formula.rb.j2                        │
│  - nuspec.xml.j2                        │
│  - ... (14 more templates)              │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Release Manager (release_mgr.py)   │
│  - MetadataLoader                       │
│  - TemplateRenderer                     │
│  - VersionBumper                        │
│  - ChecksumCalculator                   │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Generated Manifests                │
│  - packaging/generated/                 │
│    ├── PKGBUILD                         │
│    ├── Formula/ai-auto-commit.rb        │
│    ├── chocolatey/                      │
│    └── ... (7 package managers)         │
└─────────────────────────────────────────┘
```

## License

This packaging system is part of ai-auto-commit and is licensed under the same license (MIT).
