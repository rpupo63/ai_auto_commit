"""Model configurations and mappings for AI Auto Commit.

Delegates catalogs, keys, and preference handoff to ai_model_picker.
App-specific fields (token budget, commit prompt) stay local.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Re-export from ai_model_picker for backwards compatibility
from ai_model_picker import (
    get_available_providers as _get_available_providers,
    get_provider_display_name,
    get_provider_models,
    get_provider_env_var,
    get_api_key as _get_api_key,
    set_api_key as _set_api_key,
    remove_api_key as _remove_api_key,
    get_all_api_keys as _get_all_api_keys,
    get_api_key_with_fallback,
    get_default_model as _get_default_model,
    get_default_provider as _get_default_provider,
    set_default_model as _set_default_model,
    set_default_provider as _set_default_provider,
    get_model_api_id,
    load_config,
    save_config,
    get_config_path as _picker_get_config_path,
    build_preference,
    load_preference as _load_preference,
    save_preference as _save_preference,
    ModelPreference,
)

# App-specific config name
APP_NAME = "ai_auto_commit"

# Provider is a dynamic string from the live catalog (not a fixed Literal).
Provider = str


@dataclass
class ModelConfig:
    """Configuration for an AI model (backwards compatibility)."""
    name: str
    provider: str
    display_name: str
    description: str
    default: bool = False


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    """Get configuration for a model by name (backwards compatibility)."""
    providers = _get_available_providers()
    for provider_key, provider_data in providers.items():
        models = provider_data.get("models", [])
        model_api_ids = provider_data.get("model_api_ids", {})

        if model_name in models:
            return ModelConfig(
                name=model_api_ids.get(model_name, model_name),
                provider=provider_key,
                display_name=model_name,
                description="",
            )

        for display_name, api_id in model_api_ids.items():
            if api_id == model_name:
                return ModelConfig(
                    name=api_id,
                    provider=provider_key,
                    display_name=display_name,
                    description="",
                )

    return None


def get_models_by_provider(provider: str) -> list[ModelConfig]:
    """Get all models for a specific provider (backwards compatibility)."""
    models = get_provider_models(provider)
    providers = _get_available_providers()
    provider_data = providers.get(provider, {})
    model_api_ids = provider_data.get("model_api_ids", {})

    return [
        ModelConfig(
            name=model_api_ids.get(model, model),
            provider=provider,
            display_name=model,
            description="",
        )
        for model in models
    ]


def get_all_providers() -> list[str]:
    """Live provider keys from model_picker (excludes template-only 'none')."""
    providers = _get_available_providers()
    return [k for k in providers if k != "none"]


def get_preference() -> ModelPreference:
    """Load secrets-free model preference for this app."""
    return _load_preference(APP_NAME)


def set_preference(
    provider: str,
    model: str,
    *,
    instructions: str = "",
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> ModelPreference:
    """Persist provider/model (+ optional instructions) to preference.json."""
    existing = _load_preference(APP_NAME)
    pref = build_preference(
        provider=provider,
        model=model,
        instructions=instructions if instructions else existing.instructions,
        temperature=temperature if temperature is not None else existing.temperature,
        max_tokens=max_tokens if max_tokens is not None else existing.max_tokens,
        app_name=APP_NAME,
    )
    _save_preference(pref, APP_NAME)
    return pref


def sync_preference_from_model(model_name: str, provider: Optional[str] = None) -> None:
    """Update preference.json when the default model changes."""
    resolved_provider = provider
    if not resolved_provider:
        cfg = get_model_config(model_name)
        resolved_provider = cfg.provider if cfg else _get_default_provider(APP_NAME)
    set_preference(resolved_provider, model_name)


# Wrapper functions that use APP_NAME
def _get_config_path() -> Path:
    """Get the path to the config file."""
    return _picker_get_config_path(APP_NAME)


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return _picker_get_config_path(APP_NAME)


def _load_local_config() -> dict:
    """Load configuration from file (internal use for token budget)."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_local_config(config: dict) -> None:
    """Save configuration to file (internal use for token budget)."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        raise RuntimeError(f"Failed to save config: {e}")


def set_default_model(model_name: str) -> None:
    """Set the default AI model and sync preference handoff."""
    _set_default_model(model_name, APP_NAME)
    cfg = get_model_config(model_name)
    if cfg:
        _set_default_provider(cfg.provider, APP_NAME)
    sync_preference_from_model(model_name, cfg.provider if cfg else None)


def get_default_model() -> str:
    """Get the default model name."""
    return _get_default_model(APP_NAME)


def set_api_key(provider: str, api_key: str) -> None:
    """Set the API key for a specific provider."""
    _set_api_key(provider, api_key, APP_NAME)


def get_api_key(provider: str) -> Optional[str]:
    """Get the stored API key for a specific provider from config file."""
    return _get_api_key(provider, APP_NAME)


def remove_api_key(provider: str) -> None:
    """Remove the stored API key for a specific provider."""
    _remove_api_key(provider, APP_NAME)


def get_all_api_keys() -> dict[str, str]:
    """Get all stored API keys."""
    return _get_all_api_keys(APP_NAME)


def get_config() -> dict:
    """Get the full configuration dictionary."""
    return _load_local_config()


# Token budget functions (app-specific, kept locally)
def set_token_budget(budget: int) -> None:
    """
    Set the token budget limit.

    Parameters
    ----------
    budget : int
        The maximum number of tokens to use per commit operation.
        Must be a positive integer.

    Raises
    ------
    ValueError
        If budget is not a positive integer.
    """
    if not isinstance(budget, int) or budget <= 0:
        raise ValueError("Token budget must be a positive integer")

    config = _load_local_config()
    config["token_budget"] = budget
    _save_local_config(config)


def get_token_budget() -> int:
    """
    Get the token budget limit.

    Returns
    -------
    int
        The configured token budget, or 250000 if not set.
    """
    config = _load_local_config()
    return config.get("token_budget", 250_000)


def set_commit_prompt_template(prompt_template: str) -> None:
    """
    Set a custom prompt template used for commit message generation.

    Parameters
    ----------
    prompt_template : str
        Custom prompt template text. Must be a non-empty string.

    Raises
    ------
    ValueError
        If prompt_template is not a non-empty string.
    """
    if not isinstance(prompt_template, str) or not prompt_template.strip():
        raise ValueError("Commit prompt template must be a non-empty string")

    config = _load_local_config()
    config["commit_prompt_template"] = prompt_template
    _save_local_config(config)


def get_commit_prompt_template() -> Optional[str]:
    """
    Get the custom commit prompt template if configured.

    Returns
    -------
    Optional[str]
        The configured prompt template, or None if not set.
    """
    config = _load_local_config()
    value = config.get("commit_prompt_template")
    if isinstance(value, str) and value.strip():
        return value
    return None


def ensure_commit_prompt_template(default_prompt_template: str) -> str:
    """
    Ensure commit_prompt_template exists in config and return effective value.

    If no valid template is present, persists the provided default prompt into
    config so users can see and edit it explicitly.

    Parameters
    ----------
    default_prompt_template : str
        Built-in default prompt template.

    Returns
    -------
    str
        Effective commit prompt template from config.
    """
    if not isinstance(default_prompt_template, str) or not default_prompt_template.strip():
        raise ValueError("Default commit prompt template must be a non-empty string")

    config = _load_local_config()
    value = config.get("commit_prompt_template")
    if isinstance(value, str) and value.strip():
        return value

    config["commit_prompt_template"] = default_prompt_template
    _save_local_config(config)
    return default_prompt_template
