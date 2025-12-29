"""CLI interface and interactive prompts."""

from __future__ import annotations

import sys
from pathlib import Path

# Import git_operations - handle both package and direct script execution
try:
    from .git_operations import run_git_command_output
except ImportError:
    from git_operations import run_git_command_output


def prompt_for_files(target_dir: Path) -> str:
    """Prompt user for files to commit, default to '.' (all files)."""
    print("\n" + "=" * 60)
    print("📁 File Selection")
    print("=" * 60)
    
    # Show available changes
    try:
        import subprocess
        status_output = run_git_command_output(target_dir, "status", "--short")
        if status_output.strip():
            print("\nAvailable changes:")
            print(status_output)
        else:
            print("\nNo uncommitted changes found.")
    except Exception:
        pass
    
    print("\nEnter files/paths to commit (space-separated, or '.' for all files):")
    print("Examples:")
    print("  - Press Enter or type '.' for all files")
    print("  - 'file1.py file2.py' for specific files")
    print("  - 'src/' for a directory")
    print("  - '*.py' for all Python files")
    
    user_input = input("\nFiles to commit [default: '.']: ").strip()
    
    if not user_input or user_input == '.':
        return '.'
    
    return user_input


def prompt_for_model() -> str:
    """Prompt user for model selection with a dropdown-like interface grouped by provider."""
    print("\n" + "=" * 60)
    print("🤖 Model Selection")
    print("=" * 60)
    
    # Import models configuration
    try:
        from .models import (
            MODELS,
            Provider,
            get_all_providers,
            get_default_model,
            get_provider_display_name,
        )
    except ImportError:
        from models import (
            MODELS,
            Provider,
            get_all_providers,
            get_default_model,
            get_provider_display_name,
        )
    
    providers = sorted(get_all_providers())
    default_model = get_default_model()
    
    # Build model list grouped by provider
    all_models: list[tuple[str, str]] = []
    model_index = 1
    
    for provider in providers:
        provider_name = get_provider_display_name(provider)
        print(f"\n{provider_name}:")
        
        provider_models = [
            (name, config)
            for name, config in MODELS.items()
            if config.provider == provider
        ]
        provider_models.sort(key=lambda x: x[1].default, reverse=True)  # Default first
        
        for model_name, config in provider_models:
            marker = " ← DEFAULT" if model_name == default_model else ""
            print(f"  {model_index}. {config.display_name} - {config.description}{marker}")
            all_models.append((model_index, model_name))
            model_index += 1
    
    # Add custom option
    print(f"\n{model_index}. Enter custom model name")
    all_models.append((model_index, "custom"))
    max_choice = model_index
    
    while True:
        try:
            choice = input(f"\nSelect model [1-{max_choice}, default: 1]: ").strip()
            
            if not choice:
                return default_model
            
            choice_num = int(choice)
            if 1 <= choice_num <= max_choice:
                # Find the model name for this choice
                selected_model = None
                for idx, model_name in all_models:
                    if idx == choice_num:
                        selected_model = model_name
                        break
                
                if selected_model == "custom":
                    custom_model = input("Enter custom model name: ").strip()
                    if custom_model:
                        return custom_model
                    else:
                        print("Invalid model name. Please try again.")
                        continue
                
                if selected_model:
                    return selected_model
            else:
                print(f"Please enter a number between 1 and {max_choice}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(0)


def prompt_for_commit_comment(commit_msg: str) -> str:
    """
    Prompt user for optional comment to add to the commit message.
    
    Parameters
    ----------
    commit_msg : str
        The AI-generated commit message.
    
    Returns
    -------
    str
        The final commit message (with optional user comment added).
    """
    print("\n" + "=" * 60)
    print("📝 Generated Commit Message")
    print("=" * 60)
    print(commit_msg)
    print("=" * 60)
    
    print("\nYou can add a comment to the top of this commit message.")
    print("This is useful for adding context, notes, or special instructions.")
    print("Press Enter to proceed with the message as-is, or type a comment.")
    
    user_comment = input("\nEnter comment (or press Enter to skip): ").strip()
    
    if user_comment:
        # Add the user comment to the top of the commit message
        final_commit_msg = f"{user_comment}\n\n{commit_msg}"
        print("\n📋 Final commit message:")
        print("=" * 60)
        print(final_commit_msg)
        print("=" * 60)
        return final_commit_msg
    else:
        return commit_msg


def confirm_commit_and_push(
    target_dir: Path, commit_msg: str, remote: str
) -> tuple[bool, str]:
    """Ask user to confirm the commit message and path before pushing."""
    print(f"\nRepository path: {target_dir}")
    print(f"Commit message: {commit_msg}")
    
    while True:
        response = input(
            "\nIs this git commit and path correct? (Y/n/c for manual comment): "
        ).strip().lower()
        if response in ['y', 'yes', '']:  # Empty string means default (yes)
            return True, commit_msg
        elif response in ['n', 'no']:
            return False, commit_msg
        elif response in ['c', 'comment']:
            print("\n📝 Manual Comment Mode:")
            print("Your comment will be added to the TOP of the commit message.")
            print(
                "This is useful for adding context, notes, or special instructions."
            )
            manual_comment = input("\nEnter your manual comment: ").strip()
            if manual_comment:
                # Add the manual comment to the top of the commit message
                enhanced_commit_msg = f"{manual_comment}\n\n{commit_msg}"
                print(f"\n📋 Enhanced commit message:")
                print("=" * 50)
                print(enhanced_commit_msg)
                print("=" * 50)
                
                # Ask for final confirmation
                final_response = input(
                    "\nProceed with this enhanced commit message? (Y/n): "
                ).strip().lower()
                if final_response in ['y', 'yes', '']:
                    return True, enhanced_commit_msg
                elif final_response in ['n', 'no']:
                    return False, enhanced_commit_msg
                else:
                    print("Please enter 'y' or 'n'.")
            else:
                print("No comment provided. Please enter 'y', 'n', or 'c'.")
        else:
            print("Please enter 'y', 'n', or 'c' for manual comment.")


def main() -> None:
    """Main CLI entry point."""
    import argparse
    import os
    import subprocess
    # Import here to avoid circular imports
    try:
        from .ai_auto_commit import auto_commit_and_push
        from .api_client import init
        from .models import (
            get_config,
            get_config_path,
            get_default_model,
            get_model_config,
            get_token_budget,
            set_default_model,
            set_token_budget,
        )
    except ImportError:
        from ai_auto_commit import auto_commit_and_push
        from api_client import init
        from models import (
            get_config,
            get_config_path,
            get_default_model,
            get_model_config,
            get_token_budget,
            set_default_model,
            set_token_budget,
        )
    
    parser = argparse.ArgumentParser(
        description="AI-powered git commit and push tool with interactive prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s init                     # Run interactive setup wizard (first time)
  %(prog)s                          # Generate commit from staged files
  %(prog)s --model gpt-4o           # Use GPT-4o model (instead of default)
  %(prog)s config set model gpt-4o  # Set default model
  %(prog)s config set token-budget 500000  # Set token budget
  %(prog)s config get               # Show current configuration
  %(prog)s config edit              # Edit config file in default editor

Note: Run 'autocommit init' for first-time setup.
      Files must be staged first using 'git add <files>' before running this tool.
        """
    )
    
    # Add subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init subcommand
    init_parser = subparsers.add_parser(
        "init",
        help="Run interactive setup wizard",
        description="Configure AI Auto Commit with an interactive wizard"
    )

    # Config subcommand
    config_parser = subparsers.add_parser(
        "config",
        help="Manage configuration settings",
        description="Configure default model, token budget, and other settings"
    )
    config_subparsers = config_parser.add_subparsers(dest="config_action", help="Config actions")
    
    # config get
    config_get_parser = config_subparsers.add_parser(
        "get",
        help="Show current configuration"
    )
    
    # config set
    config_set_parser = config_subparsers.add_parser(
        "set",
        help="Set a configuration value"
    )
    config_set_parser.add_argument(
        "key",
        choices=["model", "token-budget"],
        help="Configuration key to set"
    )
    config_set_parser.add_argument(
        "value",
        help="Value to set"
    )
    
    # config edit
    config_edit_parser = config_subparsers.add_parser(
        "edit",
        help="Edit configuration file in default editor"
    )
    
    # Main command arguments (for when not using config subcommand)
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key for the selected provider (if not provided, uses environment variables)"
    )
    
    parser.add_argument(
        "--provider",
        type=str,
        default="openai",
        choices=["openai", "anthropic", "google", "mistral", "cohere"],
        help="AI provider to use (default: openai)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model to use (e.g., gpt-4o-mini, claude-3-5-sonnet-20241022). "
             "Default: uses configured default model"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for the completion (default: %(default)s)"
    )
    
    parser.add_argument(
        "--remote",
        type=str,
        default="origin",
        help="Git remote to push to (default: %(default)s)"
    )
    
    parser.add_argument(
        "--set-default-model",
        type=str,
        default=None,
        metavar="MODEL",
        help="Set the default model to use and exit. Example: --set-default-model gpt-4o"
    )
    
    args = parser.parse_args()

    # Handle init subcommand
    if args.command == "init":
        try:
            from .setup import setup_wizard
        except ImportError:
            from setup import setup_wizard
        setup_wizard()
        return

    # Handle config subcommand
    if args.command == "config":
        if args.config_action == "get":
            # Show current configuration
            config = get_config()
            default_model = get_default_model()
            token_budget = get_token_budget()
            config_path = get_config_path()
            
            print("📋 Current Configuration")
            print("=" * 60)
            print(f"Config file: {config_path}")
            print(f"Default model: {default_model}")
            model_config = get_model_config(default_model)
            if model_config:
                print(f"  → {model_config.display_name} ({model_config.description})")
            print(f"Token budget: {token_budget:,} tokens")
            if config:
                print("\nAll settings:")
                for key, value in sorted(config.items()):
                    print(f"  {key}: {value}")
            else:
                print("\n(Using default settings)")
            return
        
        elif args.config_action == "set":
            if args.key == "model":
                model_name = args.value
                model_config = get_model_config(model_name)
                if model_config:
                    print(f"✅ Setting default model to: {model_config.display_name} ({model_name})")
                else:
                    print(f"✅ Setting default model to: {model_name} (custom model)")
                set_default_model(model_name)
                print("Default model saved.")
            
            elif args.key == "token-budget":
                try:
                    budget = int(args.value)
                    if budget <= 0:
                        print("❌ Error: Token budget must be a positive integer")
                        sys.exit(1)
                    set_token_budget(budget)
                    print(f"✅ Token budget set to: {budget:,} tokens")
                except ValueError:
                    print("❌ Error: Token budget must be a valid integer")
                    sys.exit(1)
            return
        
        elif args.config_action == "edit":
            # Open config file in default editor
            config_path = get_config_path()
            
            # Ensure config file exists
            if not config_path.exists():
                # Create empty config
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, "w") as f:
                    import json
                    json.dump({}, f, indent=2)
            
            # Determine editor
            editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
            if not editor:
                # Try common editors
                for ed in ["nano", "vim", "vi", "code", "subl"]:
                    if subprocess.run(["which", ed], capture_output=True).returncode == 0:
                        editor = ed
                        break
            
            if not editor:
                print("❌ Error: No editor found. Please set EDITOR or VISUAL environment variable.")
                print(f"Config file location: {config_path}")
                sys.exit(1)
            
            # Open editor
            try:
                subprocess.run([editor, str(config_path)], check=True)
                print(f"✅ Configuration file opened in {editor}")
                print(f"Config file: {config_path}")
            except subprocess.CalledProcessError:
                print(f"❌ Error: Failed to open editor {editor}")
                print(f"Config file location: {config_path}")
                sys.exit(1)
            except FileNotFoundError:
                print(f"❌ Error: Editor '{editor}' not found")
                print(f"Config file location: {config_path}")
                sys.exit(1)
            return
        
        else:
            config_parser.print_help()
            return
    
    # Handle --set-default-model flag (exit early if set)
    if args.set_default_model:
        model_name = args.set_default_model
        # Validate model if it's a known model
        model_config = get_model_config(model_name)
        if model_config:
            print(f"✅ Setting default model to: {model_config.display_name} ({model_name})")
        else:
            print(f"✅ Setting default model to: {model_name} (custom model)")
        
        set_default_model(model_name)
        print(f"Default model saved. It will be used when no --model is specified.")
        return
    
    try:
        print("🚀 AI Auto Commit Tool")
        print("=" * 60)
        
        # Initialize API key
        if args.api_key:
            try:
                from .api_client import init
            except ImportError:
                from api_client import init
            init(api_key=args.api_key, provider=args.provider)
        else:
            # Try to initialize from environment (will be done lazily when model is used)
            pass
        
        commit_msg = auto_commit_and_push(
            model=args.model,
            temperature=args.temperature,
            remote=args.remote,
        )
        
        print("\n" + "=" * 60)
        print("✅ Success!")
        print("=" * 60)
        print(f"Commit message:\n{commit_msg}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

