# AI Auto Commit

An intelligent, AI-powered git commit and push tool that automatically generates meaningful commit messages from your staged changes. Works with multiple AI providers including OpenAI, Anthropic, Google, Mistral, and Cohere.

> **🚀 Quick Start:** New to AI Auto Commit? See [docs/QUICKSTART.md](docs/QUICKSTART.md) for a 2-minute setup guide.
> **🔧 Contributing:** Want to contribute? See [CONTRIBUTING.md](CONTRIBUTING.md) for developer setup.

## Features

- 🤖 **AI-Powered Commit Messages**: Automatically generates conventional commit messages from your code changes
- 🔄 **Multi-Provider Support**: Works with OpenAI, Anthropic (Claude), Google (Gemini), Mistral, and Cohere
- 💰 **Token Budget Management**: Configurable token limits to control API costs
- 🎯 **Smart Diff Analysis**: Uses hierarchical analysis to understand complex changes
- 🛡️ **Safety Features**: Creates backups and verifies changes before committing
- ⚙️ **Flexible Configuration**: Easy-to-use config system for models and settings
- 📦 **Works Anywhere**: Install once, use from any git repository on your system

## Table of Contents

- [Installation](#installation)
- [Initial Setup](#initial-setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)

## Installation

### Quick Install (Recommended)

Choose the method for your platform:

#### macOS / Linux (One-line Install)
```bash
curl -fsSL https://raw.githubusercontent.com/yourusername/ai_auto_commit/main/install.sh | bash
```

#### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/yourusername/ai_auto_commit/main/install.ps1 | iex
```

### Package Manager Installation

#### Linux (Flatpak) - Universal
```bash
flatpak install flathub com.github.yourusername.AIAutoCommit
```

#### Arch Linux (yay/AUR)
```bash
yay -S ai-auto-commit
```

#### Debian/Ubuntu (apt)
```bash
sudo apt install ai-auto-commit
```

#### macOS (Homebrew)
```bash
brew tap yourusername/tap
brew install ai-auto-commit
```

#### Windows (winget) - Recommended
```powershell
winget install YourPublisher.AIAutoCommit
```

#### Windows (Chocolatey)
```powershell
choco install ai-auto-commit
```

#### Windows (Scoop)
```powershell
scoop bucket add extras
scoop install ai-auto-commit
```

#### Universal (pip)
```bash
pip install ai-auto-commit
```

#### Universal (pipx) - Recommended for CLI tools
```bash
pipx install ai-auto-commit
```

### After Installation

After installing via any method above, run the interactive setup wizard:

```bash
autocommit init
```

The wizard will guide you through configuring your AI provider API keys, default model, and token budget. All settings are stored securely in `~/.config/ai_auto_commit/config.json`.

---

### Install from Source (Development)

1. Clone or navigate to the project directory:

```bash
cd /path/to/ai_auto_commit
```

2. Install the package (recommended: use editable mode for development):

```bash
pip install -e .
```

Or for a regular installation:

```bash
pip install .
```

3. Verify installation:

```bash
autocommit --help
```

The `autocommit` command should now be available globally from any directory.

4. Run the interactive setup wizard:

```bash
autocommit init
```

## Initial Setup

After installation, run the interactive setup wizard to configure your API keys and preferences:

```bash
autocommit init
```

The wizard will guide you through:

1. **API Key Configuration**: Add API keys for one or more AI providers (OpenAI, Anthropic, Google, Mistral, Cohere)
2. **Default Model Selection**: Choose your preferred AI model
3. **Token Budget**: Set a token limit to control API costs

All configuration is stored in `~/.config/ai_auto_commit/config.json`. Your API keys are stored locally and never transmitted anywhere except to your chosen AI provider.

### Manual Configuration (Alternative)

If you prefer not to use the interactive wizard, you can configure settings manually:

```bash
# Set default model
autocommit config set model gpt-4o

# Set token budget (default: 250,000)
autocommit config set token-budget 500000

# View current configuration
autocommit config get

# Edit config file directly
autocommit config edit
```

## Configuration

The tool stores configuration in `~/.config/ai_auto_commit/config.json`. You can manage it in three ways:

### 1. View Current Configuration

```bash
autocommit config get
```

This displays:

- Config file location
- Default model
- Token budget
- All other settings

### 2. Set Configuration Values

#### Set Default Model

```bash
# Using a predefined model
autocommit config set model gpt-4o

# Using a custom model name
autocommit config set model my-custom-model
```

**Available Models by Provider:**

- **OpenAI**: `gpt-5.2`, `gpt-5.1`, `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-4`, `gpt-3.5-turbo`, `o3`, `o3-mini`
- **Anthropic**: `claude-opus-4.5`, `claude-sonnet-4.5`, `claude-haiku-4.5`, `claude-3-5-sonnet-20241022`
- **Google**: `gemini-3-pro-preview-high`, `gemini-3-flash`, `gemini-1.5-pro`, `gemini-1.5-flash`
- **Mistral**: `devstral-2`, `mistral-large-latest`, `mistral-medium-latest`, `mistral-small-latest`
- **Cohere**: `command-r-plus`, `command-r`

#### Set Token Budget

The token budget limits how many tokens can be used per commit operation. This helps control API costs.

```bash
# Set to 500,000 tokens
autocommit config set token-budget 500000

# Set to 100,000 tokens (more conservative)
autocommit config set token-budget 100000
```

**Default**: 250,000 tokens

### 3. Edit Configuration File Directly

Open the config file in your default editor:

```bash
autocommit config edit
```

This will:

- Create the config file if it doesn't exist
- Open it in your default editor (respects `$EDITOR` or `$VISUAL`)
- Fall back to common editors (`nano`, `vim`, `vi`, `code`, `subl`) if no editor is set

The config file format is JSON:

```json
{
  "default_model": "gpt-4o",
  "token_budget": 250000
}
```

## Usage

### Basic Workflow

1. **Stage your changes:**

```bash
git add file1.py file2.py
# or stage all changes
git add .
```

2. **Run autocommit:**

```bash
autocommit
```

The tool will:

- Analyze your staged changes
- Generate an AI-powered commit message
- Show you the message for review
- Ask for confirmation before committing and pushing

### Command-Line Options

```bash
# Use a specific model for this commit
autocommit --model gpt-4o

# Use a different provider
autocommit --provider anthropic --model claude-sonnet-4.5

# Adjust temperature (0.0-1.0, default: 0.2)
autocommit --temperature 0.5

# Push to a different remote
autocommit --remote upstream

# Provide API key inline
autocommit --api-key "sk-..." --provider openai
```

### Interactive Features

When you run `autocommit`, you'll see:

1. **Repository Status**: Shows what changes will be committed
2. **Generated Commit Message**: AI-generated message based on your changes
3. **Comment Prompt**: Option to add a comment to the top of the commit message
4. **Confirmation**: Final confirmation before committing and pushing

**Example Interaction:**

```
🚀 AI Auto Commit Tool
============================================================
Operating on repository: /path/to/repo
Checking repository status...

📝 Generated Commit Message
============================================================
feat: add user authentication system

- Add login endpoint with JWT tokens
- Implement password hashing with bcrypt
- Add user registration flow
- Update API documentation
============================================================

You can add a comment to the top of this commit message.
Press Enter to proceed with the message as-is, or type a comment.

Enter comment (or press Enter to skip):

Repository path: /path/to/repo
Commit message: feat: add user authentication system...

Is this git commit and path correct? (Y/n/c for manual comment): y
```

### What Gets Committed

The tool commits **only staged files**. It will:

- ✅ Commit all staged changes
- ✅ Generate a commit message from the staged diff
- ✅ Push to the configured remote (default: `origin`)
- ✅ Push to the current branch

**Important**: Files must be staged first using `git add` before running `autocommit`.

## Advanced Features

### Token Budget Management

The tool uses a token budget system to control API costs:

- **Reservation System**: Tokens are reserved before API calls
- **Automatic Refunds**: Unused tokens are refunded
- **Budget Tracking**: See token usage in the output
- **Configurable Limits**: Set your budget via config

Example output:

```
Final token usage: 15,234/250,000 tokens
```

### Safety Features

1. **Backup Creation**: Creates a backup before making changes
2. **Working Directory Verification**: Checks repository state
3. **File Deletion Detection**: Warns if files might be affected
4. **Confirmation Prompts**: Multiple checkpoints before committing

### Smart Commit Generation

The tool uses two strategies:

1. **Heuristic Approach** (Token-Light): For simple changes, uses file statistics without sending full diffs
2. **Hierarchical Approach**: For complex changes, analyzes diffs in stages

This balances quality with cost efficiency.

### Multiple Providers

You can switch between providers easily:

```bash
# Use OpenAI
autocommit --provider openai --model gpt-4o

# Use Anthropic
autocommit --provider anthropic --model claude-sonnet-4.5

# Use Google
autocommit --provider google --model gemini-1.5-pro
```

You can configure multiple API keys in the setup wizard to easily switch between providers.

## Troubleshooting

### "No staged files found"

**Problem**: The tool can't find any staged changes.

**Solution**: Stage your files first:

```bash
git add <files>
# or
git add .
```

### "API key not found"

**Problem**: The tool can't find your API key.

**Solutions**:

1. Run the interactive setup wizard:

   ```bash
   autocommit init
   ```

2. Or provide it via command line:
   ```bash
   autocommit --api-key "sk-..." --provider openai
   ```

### "Not in a git repository"

**Problem**: You're not in a git repository.

**Solution**: Navigate to a git repository directory:

```bash
cd /path/to/your/git/repo
autocommit
```

The tool automatically detects the git repository root from any subdirectory.

### "Token budget exceeded"

**Problem**: Your changes are too large for the current token budget.

**Solutions**:

1. Increase the token budget:

   ```bash
   autocommit config set token-budget 500000
   ```

2. Commit changes in smaller chunks:
   ```bash
   git add file1.py file2.py
   autocommit
   git add file3.py file4.py
   autocommit
   ```

### "Editor not found" (config edit)

**Problem**: `autocommit config edit` can't find an editor.

**Solutions**:

1. Set the `EDITOR` environment variable:

   ```bash
   export EDITOR="nano"  # or vim, code, etc.
   ```

2. Or manually edit the config file:
   ```bash
   nano ~/.config/ai_auto_commit/config.json
   ```

### Commit message quality issues

**Problem**: Generated commit messages aren't accurate.

**Solutions**:

1. Use a more capable model:

   ```bash
   autocommit config set model gpt-4o
   # or
   autocommit --model claude-opus-4.5
   ```

2. Add a comment when prompted to provide context

3. Stage related changes together for better context

## Configuration File Location

All configuration is stored in:

```
~/.config/ai_auto_commit/config.json
```

You can view, edit, or manually modify this file. The tool will automatically create it with defaults on first use.

## Security

### API Key Storage

Your API keys are stored locally in the config file (`~/.config/ai_auto_commit/config.json`) with standard file permissions (readable only by your user account). The keys are stored in plain text in the config file, so ensure your home directory has appropriate permissions.

**Best Practices:**

- Never commit your config file to version control
- Ensure your home directory and config file have restrictive permissions
- Regularly rotate your API keys
- On shared systems, ensure proper file permissions on the config directory

**The tool:**
- Only stores keys locally (never transmitted to any third party)
- Only sends API requests to your chosen AI provider
- Never collects telemetry or analytics
- Is completely open source for your review

## Examples

### Example 1: First Time Setup

```bash
# Install (Arch Linux)
yay -S ai-auto-commit

# Run interactive setup
autocommit init

# Navigate to your git repo and use it
cd ~/my-project
git add .
autocommit
```

### Example 2: Quick Commit

```bash
# Make some changes
vim src/main.py

# Stage and commit
git add src/main.py
autocommit
```

### Example 3: Using a Specific Model

```bash
git add .
autocommit --model gpt-4o --temperature 0.3
```

### Example 4: Configure and Use

```bash
# Set up defaults
autocommit config set model claude-sonnet-4.5
autocommit config set token-budget 300000

# Use with defaults
git add .
autocommit
```

### Example 5: Reconfigure API Keys

```bash
# Run setup wizard again to change API keys
autocommit init

# Or edit config file directly
autocommit config edit
```

## Best Practices

1. **Review Before Committing**: Always review the generated commit message
2. **Stage Related Changes**: Group related changes together for better context
3. **Use Appropriate Models**: Use faster/cheaper models for simple changes, more capable models for complex changes
4. **Monitor Token Usage**: Keep an eye on token usage to control costs
5. **Set Sensible Budgets**: Configure token budgets based on your typical change sizes
6. **Use Comments**: Add comments when you need to provide additional context

## Requirements

- Python 3.8+
- Git
- One or more AI provider API keys:
  - OpenAI API key
  - Anthropic API key
  - Google API key
  - Mistral API key
  - Cohere API key

## License

MIT

## Support

For issues, questions, or contributions, please open an issue on the project repository.

---

**Happy Committing! 🚀**
