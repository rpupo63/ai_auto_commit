"""Interactive setup wizard for AI Auto Commit.

This module delegates to ai_model_picker for the core setup logic,
with app-specific customizations for token budget configuration.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ai_model_picker import (
    setup_wizard as _base_setup_wizard,
    configure_api_keys,
    display_config as _display_config,
    get_config_path,
    load_config,
    save_config,
    get_provider_display_name,
    get_all_api_keys,
    UserConfig,
)

# App-specific config name
APP_NAME = "ai_auto_commit"

# Import local token budget functions
try:
    from .models import get_token_budget, set_token_budget
except ImportError:
    from models import get_token_budget, set_token_budget


def setup_wizard() -> None:
    """Run the interactive setup wizard for AI Auto Commit."""
    print("=" * 70)
    print("  AI Auto Commit - Interactive Setup Wizard")
    print("=" * 70)
    print()
    print("Welcome! This wizard will help you configure AI Auto Commit.")
    print()
    print("You'll need at least one AI provider API key to use this tool.")
    print("Don't worry - you can always change these settings later using:")
    print("  - autocommit config set <key> <value>")
    print("  - autocommit config edit")
    print()

    # Check if already configured
    existing_keys = get_all_api_keys(APP_NAME)
    if existing_keys:
        print("You already have API keys configured for:")
        for provider in existing_keys:
            print(f"  - {get_provider_display_name(provider)}")
        print()
        response = input("Do you want to reconfigure? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("\nSetup cancelled. Your existing configuration is unchanged.")
            return
        print()

    # Step 1: API Key Setup
    print("-" * 70)
    print("Step 1: Configure AI Provider API Keys")
    print("-" * 70)
    print()
    print("You can configure multiple providers. At least one is required.")

    configured_providers = configure_api_keys(
        app_name=APP_NAME,
        require_at_least_one=True
    )

    print()
    print("=" * 70)
    display_names = [get_provider_display_name(p) for p in configured_providers]
    print(f"  API keys configured for: {', '.join(display_names)}")
    print("=" * 70)

    # Step 2: Default Model Setup
    from ai_model_picker import select_provider, select_model

    config = load_config(APP_NAME)

    print()
    print("-" * 70)
    print("Step 2: Choose Default Model")
    print("-" * 70)
    print()

    current_default = config.model
    print(f"Current default model: {current_default}")
    print()
    print("You can choose a default model, or press Enter to keep the current default.")
    print()

    provider = select_provider("Select Provider for Default Model")
    if provider and provider != "none":
        model = select_model(provider, "Select Default Model")
        if model:
            config.provider = provider
            config.model = model
            save_config(config, APP_NAME)
            print(f"  Default model set to: {model}")
        else:
            print(f"  Keeping current default: {current_default}")
    else:
        print(f"  Keeping current default: {current_default}")

    # Step 3: Token Budget Setup (app-specific)
    print()
    print("-" * 70)
    print("Step 3: Configure Token Budget")
    print("-" * 70)
    print()

    current_budget = get_token_budget()
    print(f"Current token budget: {current_budget:,} tokens")
    print()
    print("The token budget limits API usage per commit to control costs.")
    print("Recommended values:")
    print("  - 100,000  (conservative, for small commits)")
    print("  - 250,000  (balanced, default)")
    print("  - 500,000  (generous, for large commits)")
    print()

    budget_input = input(f"Enter token budget [default: {current_budget:,}]: ").strip()
    if budget_input:
        try:
            budget = int(budget_input.replace(",", ""))
            if budget <= 0:
                print("  Error: Token budget must be positive. Keeping current value.")
            else:
                set_token_budget(budget)
                print(f"  Token budget set to: {budget:,} tokens")
        except ValueError:
            print("  Error: Invalid number. Keeping current value.")
    else:
        print(f"  Keeping current budget: {current_budget:,} tokens")

    # Summary
    print()
    print("=" * 70)
    print("  Setup Complete!")
    print("=" * 70)
    print()
    print("Configuration saved to:", get_config_path(APP_NAME))
    print()
    print("You're ready to use AI Auto Commit!")
    print()
    print("Quick start:")
    print("  1. Navigate to a git repository")
    print("  2. Stage your changes: git add <files>")
    print("  3. Run: autocommit")
    print()
    print("For more information:")
    print("  autocommit --help")
    print("  autocommit config get")
    print()


def display_config(show_keys: bool = False) -> None:
    """Display current configuration."""
    _display_config(app_name=APP_NAME, show_keys=show_keys)

    # Also show token budget (app-specific)
    current_budget = get_token_budget()
    print(f"Token budget: {current_budget:,} tokens")
    print()
