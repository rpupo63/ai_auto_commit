"""Interactive first-time setup (``autocommit init``)."""

from __future__ import annotations

import os

from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from ai_model_picker import get_provider_display_name, get_provider_env_var

from ai_auto_commit.cli import prompt_for_model
from ai_auto_commit.models import (
    Provider,
    get_all_providers,
    get_api_key,
    get_config_path,
    get_token_budget,
    remove_api_key,
    set_api_key,
    set_default_model,
    set_token_budget,
)


def _configure_api_keys() -> None:
    while True:
        choices: list[Choice] = [Choice(value="__done", name="Done — continue")]
        for p in get_all_providers():
            env_var = get_provider_env_var(p)
            env_set = bool(env_var and os.environ.get(env_var, "").strip())
            stored = bool(get_api_key(p))
            parts: list[str] = []
            if stored:
                parts.append("saved in config")
            if env_set:
                parts.append(f"env {env_var}" if env_var else "env set")
            suffix = f" ({', '.join(parts)})" if parts else " (not set)"
            name = f"{get_provider_display_name(p)}{suffix}"
            choices.append(Choice(value=p, name=name))

        pick = inquirer.select(
            message="Set or clear API keys (env vars still work if set):",
            choices=choices,
        ).execute()

        if pick == "__done":
            break

        provider = pick  # type: Provider
        display = get_provider_display_name(provider)
        if get_api_key(provider) and inquirer.confirm(
            message=f"Remove saved API key for {display} from config?",
            default=False,
        ).execute():
            remove_api_key(provider)
            print("Removed saved key.")
            continue

        env_var = get_provider_env_var(provider)
        hint = f" (optional: {env_var})" if env_var else ""
        key = inquirer.secret(
            message=f"API key for {display}{hint} (Enter to skip):",
        ).execute()
        key = (key or "").strip()
        if key:
            set_api_key(provider, key)
            print("API key saved.")


def setup_wizard() -> None:
    print("\n" + "=" * 60)
    print("AI Auto Commit — setup wizard")
    print("=" * 60)
    print(f"\nConfig file: {get_config_path()}\n")

    if inquirer.confirm(
        message="Configure API keys for providers now?",
        default=True,
    ).execute():
        _configure_api_keys()

    if inquirer.confirm(
        message="Choose default model now?",
        default=True,
    ).execute():
        model = prompt_for_model()
        set_default_model(model)
        if model == "template":
            print("Default set to template / heuristic mode.")
        else:
            print(f"Default model set to: {model}")

    default_budget = get_token_budget()
    raw = inquirer.text(
        message="Token budget per commit (tokens):",
        default=str(default_budget),
    ).execute().strip()
    try:
        budget = int(raw.replace(",", "").replace("_", ""))
        if budget <= 0:
            raise ValueError
        set_token_budget(budget)
        print(f"Token budget set to {budget:,}.")
    except ValueError:
        print("Invalid number; token budget unchanged.")

    print("\nSetup complete. Run `autocommit --help` for usage.\n")
