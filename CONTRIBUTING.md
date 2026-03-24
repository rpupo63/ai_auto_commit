# Contributing to AI Auto Commit

Thank you for your interest in contributing to AI Auto Commit! This guide will help you set up the development environment and understand the project structure.

## Developer Setup

### Prerequisites

- Python 3.8 or higher
- Git
- pip or pipx
- (Optional) An AI provider API key for testing

### Installation for Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/ai_auto_commit.git
   cd ai_auto_commit
   ```

2. **Install in editable mode:**
   ```bash
   pip install -e .
   ```

3. **Verify installation:**
   ```bash
   autocommit --help
   ```

4. **Run the setup wizard:**
   ```bash
   autocommit init
   ```

### Project Structure

```
ai_auto_commit/
├── ai_auto_commit/           # Main Python package
│   ├── __init__.py
│   ├── cli.py                # CLI interface and argument parsing
│   ├── setup_wizard.py       # Interactive setup wizard (autocommit init)
│   ├── models.py             # Model configurations and config management
│   ├── api_client.py         # API client initialization
│   ├── llm_client.py         # LLM provider implementations
│   ├── git_operations.py     # Git command wrappers
│   ├── commit_generation.py  # Commit message generation logic
│   ├── token_budget.py       # Token budget management
│   └── ...
│
├── docs/                     # Documentation
│   ├── QUICKSTART.md         # Quick start guide
│   ├── PACKAGE_MANAGERS.md   # Package manager installation guide
│   ├── PUBLISHING.md         # Publishing guide for maintainers
│   └── ...
│
├── debian/                   # Debian/Ubuntu package files
├── flatpak/                  # Flatpak manifest files
├── Formula/                  # Homebrew formula
├── chocolatey/               # Chocolatey package files
├── scoop/                    # Scoop manifest
├── winget/                   # winget manifest files
│
├── README.md                 # User documentation
├── CONTRIBUTING.md           # This file (developer guide)
├── LICENSE                   # MIT License
├── pyproject.toml            # Python package configuration
└── PKGBUILD                  # Arch Linux (AUR) package file
```

## Development Workflow

### Making Changes

1. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** to the Python code in `ai_auto_commit/`

3. **Test your changes:**
   ```bash
   # Test the CLI
   autocommit --help

   # Test in a git repository
   cd /path/to/test/repo
   git add .
   autocommit
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

### Configuration System

The tool uses a config file at `~/.config/ai_auto_commit/config.json`:

```json
{
  "api_keys": {
    "openai": "sk-...",
    "anthropic": "sk-ant-...",
    "google": "...",
    "mistral": "...",
    "cohere": "..."
  },
  "default_model": "gpt-4o",
  "token_budget": 250000
}
```

Key functions in `models.py`:
- `set_api_key(provider, api_key)` - Store API key
- `get_api_key(provider)` - Retrieve API key
- `set_default_model(model)` - Set default model
- `get_default_model()` - Get default model

### Adding a New AI Provider

To add support for a new AI provider:

1. **Add provider type** to `models.py`:
   ```python
   Provider = Literal["openai", "anthropic", "google", "mistral", "cohere", "newprovider"]
   ```

2. **Add model configurations** to `MODELS` dict in `models.py`:
   ```python
   "new-model-name": ModelConfig(
       name="new-model-name",
       provider="newprovider",
       display_name="New Model Display Name",
       description="Model description",
   ),
   ```

3. **Implement provider initialization** in `llm_client.py`:
   ```python
   def initialize_provider(provider: Provider, api_key: str) -> None:
       if provider == "newprovider":
           # Initialize new provider
           pass
   ```

4. **Update setup wizard** in `setup_wizard.py` to prompt for the new provider's API key

### Version Management

When releasing a new version:

1. **Run the version bump script:**
   ```bash
   ./bump-version.sh 0.2.0
   ```

   This updates:
   - `pyproject.toml`
   - `PKGBUILD`
   - `Formula/ai-auto-commit.rb`
   - `chocolatey/ai-auto-commit.nuspec`
   - `scoop/ai-auto-commit.json`

2. **Review changes:**
   ```bash
   git diff
   ```

3. **Commit and tag:**
   ```bash
   git add -A
   git commit -m "Bump version to 0.2.0"
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin main
   git push origin v0.2.0
   ```

4. **Create GitHub release** and follow publishing guides in `docs/PUBLISHING.md`

## Package Manager Development

### Testing Package Builds

#### PyPI (pip)
```bash
python -m build
pip install dist/ai-auto-commit-0.1.0.tar.gz
```

#### Arch Linux (PKGBUILD)
```bash
makepkg -si
```

#### Debian (apt)
```bash
dpkg-buildpackage -us -uc
sudo dpkg -i ../ai-auto-commit_0.1.0-1_all.deb
```

#### Homebrew
```bash
brew install --build-from-source Formula/ai-auto-commit.rb
```

#### Flatpak
```bash
flatpak-builder --user --install build-dir flatpak/com.github.yourusername.AIAutoCommit.yaml
```

### Updating Package Files

When you update the version or dependencies:

1. **Update `pyproject.toml`** - Main source of truth
2. **Run `bump-version.sh`** - Updates package manager files
3. **Calculate new checksums:**
   ```bash
   # For source tarball
   sha256sum ai-auto-commit-0.1.0.tar.gz

   # Update in:
   # - PKGBUILD
   # - Formula/ai-auto-commit.rb
   # - scoop/ai-auto-commit.json
   # - winget manifests
   ```

## Code Style

- Follow PEP 8 style guide
- Use type hints where possible
- Add docstrings to functions using NumPy style
- Keep functions focused and single-purpose
- Avoid over-engineering - keep it simple

## Testing

Currently, the project uses manual testing. To test:

1. **Test setup wizard:**
   ```bash
   autocommit init
   ```

2. **Test configuration:**
   ```bash
   autocommit config get
   autocommit config set model gpt-4o
   autocommit config edit
   ```

3. **Test commit generation:**
   ```bash
   cd /path/to/git/repo
   git add .
   autocommit
   ```

## Documentation

### User Documentation

- **README.md** - Primary user documentation
- **docs/QUICKSTART.md** - 2-minute quick start guide
- **docs/PACKAGE_MANAGERS.md** - Installation methods for all platforms

### Developer Documentation

- **CONTRIBUTING.md** (this file) - Development setup and workflow
- **docs/PUBLISHING.md** - Publishing to package managers
- **docs/SETUP_SUMMARY.md** - Technical implementation overview

### Updating Documentation

When you add a feature:

1. Update relevant sections in README.md
2. Update help text in `cli.py` if adding CLI options
3. Update docs/QUICKSTART.md if it affects getting started
4. Add examples showing the new feature

## Commit Message Convention

Follow conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

**Examples:**
```
feat(cli): add support for custom commit templates
fix(api): handle rate limit errors gracefully
docs(readme): update installation instructions
refactor(config): simplify API key storage
```

## Release Process

See `docs/PUBLISHING.md` for detailed publishing instructions.

Quick overview:

1. **Bump version:** `./bump-version.sh X.Y.Z`
2. **Update CHANGELOG** (if you create one)
3. **Commit and tag:** `git tag -a vX.Y.Z`
4. **Push:** `git push origin main --tags`
5. **Create GitHub release**
6. **Publish to PyPI:** `python -m build && twine upload dist/*`
7. **Update package managers:** Follow docs/PUBLISHING.md

## Getting Help

- Check existing documentation in `docs/`
- Look at similar code in the project
- Open an issue for questions
- Review `models.py` for configuration system
- Review `cli.py` for command handling

## Before Submitting

Replace placeholder values:
- `yourusername` → Your GitHub username
- `YourPublisher` → Your publisher name (for winget)
- `your.email@example.com` → Your email
- Update LICENSE if needed

## Key Files to Know

- **cli.py** - Entry point, argument parsing, commands
- **setup_wizard.py** - Interactive setup wizard
- **models.py** - Configuration management, API key storage
- **api_client.py** - Provider initialization
- **commit_generation.py** - Core commit message logic
- **pyproject.toml** - Package metadata, dependencies

## Questions?

- Open an issue on GitHub
- Check documentation in `docs/`
- Read the code - it's well-commented!

---

Happy contributing! 🚀
