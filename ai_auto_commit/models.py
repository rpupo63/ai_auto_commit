"""Model configurations and mappings for AI Auto Commit.

This module provides backwards-compatible access to model configurations
by delegating to ai_model_picker for core functionality. App-specific
features like token budget are maintained locally.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

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
    set_default_model as _set_default_model,
    get_model_api_id,
    load_config,
    save_config,
    get_config_path as _picker_get_config_path,
)
# App-specific config name
APP_NAME = "ai_auto_commit"

# Provider types - includes all supported providers
Provider = Literal[
    "openai", "anthropic", "google", "mistral", "cohere",
    "deepseek", "xai", "meta", "alibaba", "none"
]


@dataclass
class ModelConfig:
    """Configuration for an AI model (backwards compatibility)."""
    name: str
    provider: Provider
    display_name: str
    description: str
    default: bool = False


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    """Get configuration for a model by name (backwards compatibility)."""
    # Try to find the model in available providers
    providers = _get_available_providers()
    for provider_key, provider_data in providers.items():
        models = provider_data.get("models", [])
        model_api_ids = provider_data.get("model_api_ids", {})

        # Check if model_name matches a display name
        if model_name in models:
            return ModelConfig(
                name=model_api_ids.get(model_name, model_name),
                provider=provider_key,
                display_name=model_name,
                description="",
            )

        # Check if model_name matches an API ID
        for display_name, api_id in model_api_ids.items():
            if api_id == model_name:
                return ModelConfig(
                    name=api_id,
                    provider=provider_key,
                    display_name=display_name,
                    description="",
                )

    return None


def get_models_by_provider(provider: Provider) -> list[ModelConfig]:
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


def get_all_providers() -> list[Provider]:
    """Get list of all available providers from model_picker (provider_models.json)."""
    providers = _get_available_providers()
    return [k for k in providers if k != "none"]


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
    """Set the default AI model to use."""
    _set_default_model(model_name, APP_NAME)


def get_default_model() -> str:
    """Get the default model name."""
    return _get_default_model(APP_NAME)


def set_api_key(provider: Provider, api_key: str) -> None:
    """Set the API key for a specific provider."""
    _set_api_key(provider, api_key, APP_NAME)


def get_api_key(provider: Provider) -> Optional[str]:
    """Get the stored API key for a specific provider from config file."""
    return _get_api_key(provider, APP_NAME)


def remove_api_key(provider: Provider) -> None:
    """Remove the stored API key for a specific provider."""
    _remove_api_key(provider, APP_NAME)


def get_all_api_keys() -> dict[Provider, str]:
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
