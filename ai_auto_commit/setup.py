"""Interactive setup wizard for AI Auto Commit."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Provider

try:
    from .models import (
        get_all_api_keys,
        get_all_providers,
        get_api_key,
        get_config_path,
        get_default_model,
        get_provider_display_name,
        get_token_budget,
        set_api_key,
        set_default_model,
        set_token_budget,
    )
except ImportError:
    from models import (
        get_all_api_keys,
        get_all_providers,
        get_api_key,
        get_config_path,
        get_default_model,
        get_provider_display_name,
        get_token_budget,
        set_api_key,
        set_default_model,
        set_token_budget,
    )


def setup_wizard() -> None:
    """Run the interactive setup wizard."""
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
    existing_keys = get_all_api_keys()
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

    # API Key Setup
    print("-" * 70)
    print("Step 1: Configure AI Provider API Keys")
    print("-" * 70)
    print()
    print("You can configure multiple providers. At least one is required.")
    print()

    providers = get_all_providers()
    configured_providers = []

    for provider in sorted(providers):
        provider_name = get_provider_display_name(provider)
        print(f"\n{provider_name}:")
        print("-" * 40)

        # Show existing key if any
        existing_key = get_api_key(provider)
        if existing_key:
            masked_key = existing_key[:8] + "..." + existing_key[-4:] if len(existing_key) > 12 else "***"
            print(f"Current key: {masked_key}")
            response = input("Update this key? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                configured_providers.append(provider)
                continue

        # Prompt for new key
        api_key = input(f"Enter {provider_name} API key (or press Enter to skip): ").strip()

        if api_key:
            set_api_key(provider, api_key)
            configured_providers.append(provider)
            print(f"✓ {provider_name} API key saved")
        else:
            print(f"  Skipped {provider_name}")

    if not configured_providers:
        print("\n❌ Error: You must configure at least one API provider to use this tool.")
        print("Please run 'autocommit init' again and configure at least one provider.")
        sys.exit(1)

    print()
    print("=" * 70)
    print(f"✓ API keys configured for: {', '.join(get_provider_display_name(p) for p in configured_providers)}")
    print("=" * 70)

    # Default Model Setup
    print()
    print("-" * 70)
    print("Step 2: Choose Default Model")
    print("-" * 70)
    print()

    current_default = get_default_model()
    print(f"Current default model: {current_default}")
    print()
    print("You can choose a default model, or press Enter to keep the current default.")
    print("Popular models:")
    print("  OpenAI:     gpt-4o, gpt-4o-mini, gpt-5.2")
    print("  Anthropic:  claude-sonnet-4.5, claude-opus-4.5")
    print("  Google:     gemini-3-pro-preview-high, gemini-3-flash")
    print()

    model = input(f"Enter default model name [default: {current_default}]: ").strip()
    if model:
        set_default_model(model)
        print(f"✓ Default model set to: {model}")
    else:
        print(f"  Keeping current default: {current_default}")

    # Token Budget Setup
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
                print("❌ Error: Token budget must be positive. Keeping current value.")
            else:
                set_token_budget(budget)
                print(f"✓ Token budget set to: {budget:,} tokens")
        except ValueError:
            print("❌ Error: Invalid number. Keeping current value.")
    else:
        print(f"  Keeping current budget: {current_budget:,} tokens")

    # Summary
    print()
    print("=" * 70)
    print("  Setup Complete!")
    print("=" * 70)
    print()
    print("Configuration saved to:", get_config_path())
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
