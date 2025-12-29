"""Model configurations and mappings for different AI providers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# Provider types
Provider = Literal["openai", "anthropic", "google", "mistral", "cohere"]


@dataclass
class ModelConfig:
    """Configuration for an AI model."""
    name: str
    provider: Provider
    display_name: str
    description: str
    default: bool = False


# Model configurations grouped by provider
MODELS: dict[str, ModelConfig] = {
    # OpenAI Models - Top Language & Reasoning Models
    "gpt-5.2": ModelConfig(
        name="gpt-5.2",
        provider="openai",
        display_name="GPT-5.2 (xHigh)",
        description="Often tied for #1, leads in coding/agentic tasks",
        default=True,
    ),
    "gpt-5.1": ModelConfig(
        name="gpt-5.1",
        provider="openai",
        display_name="GPT-5.1 (High)",
        description="High performance model",
    ),
    "gpt-5.1-codex": ModelConfig(
        name="gpt-5.1-codex",
        provider="openai",
        display_name="GPT-5.1 Codex (High)",
        description="Specialized for programming",
    ),
    "gpt-5.1-codex-max": ModelConfig(
        name="gpt-5.1-codex-max",
        provider="openai",
        display_name="GPT-5.1 Codex Max",
        description="Maximum performance codex model",
    ),
    "gpt-5-pro": ModelConfig(
        name="gpt-5-pro",
        provider="openai",
        display_name="GPT-5 Pro",
        description="Pro tier GPT-5 model",
    ),
    "gpt-5-mini-high": ModelConfig(
        name="gpt-5-mini-high",
        provider="openai",
        display_name="GPT-5 Mini High",
        description="High performance mini model",
    ),
    "gpt-5.2-no-thinking": ModelConfig(
        name="gpt-5.2-no-thinking",
        provider="openai",
        display_name="GPT-5.2 No Thinking",
        description="GPT-5.2 without thinking mode",
    ),
    "gpt-5.1-no-thinking": ModelConfig(
        name="gpt-5.1-no-thinking",
        provider="openai",
        display_name="GPT-5.1 No Thinking",
        description="GPT-5.1 without thinking mode",
    ),
    "gpt-5-nano": ModelConfig(
        name="gpt-5-nano",
        provider="openai",
        display_name="GPT-5 Nano",
        description="Smallest GPT-5 model",
    ),
    "gpt-oss-120b": ModelConfig(
        name="gpt-oss-120b",
        provider="openai",
        display_name="GPT OSS 120b",
        description="Open source 120B parameter model",
    ),
    "o3": ModelConfig(
        name="o3",
        provider="openai",
        display_name="o3",
        description="Reasoning specialist model",
    ),
    "o3-mini": ModelConfig(
        name="o3-mini",
        provider="openai",
        display_name="o3-mini",
        description="Mini reasoning specialist model",
    ),
    # Legacy OpenAI models
    "gpt-4o-mini": ModelConfig(
        name="gpt-4o-mini",
        provider="openai",
        display_name="GPT-4o Mini",
        description="Fast, cost-effective",
    ),
    "gpt-4o": ModelConfig(
        name="gpt-4o",
        provider="openai",
        display_name="GPT-4o",
        description="High quality, more expensive",
    ),
    "gpt-4-turbo": ModelConfig(
        name="gpt-4-turbo",
        provider="openai",
        display_name="GPT-4 Turbo",
        description="Balanced performance",
    ),
    "gpt-4": ModelConfig(
        name="gpt-4",
        provider="openai",
        display_name="GPT-4",
        description="High quality, slower",
    ),
    "gpt-3.5-turbo": ModelConfig(
        name="gpt-3.5-turbo",
        provider="openai",
        display_name="GPT-3.5 Turbo",
        description="Fastest, cheapest",
    ),
    
    # Anthropic Models - Top Language & Reasoning Models
    "claude-opus-4.5": ModelConfig(
        name="claude-opus-4.5",
        provider="anthropic",
        display_name="Claude Opus 4.5",
        description="Strongest for creative writing & long context",
    ),
    "claude-4.5-opus-thinking-high-effort": ModelConfig(
        name="claude-4.5-opus-thinking-high-effort",
        provider="anthropic",
        display_name="Claude 4.5 Opus Thinking (High Effort)",
        description="High effort thinking mode",
    ),
    "claude-sonnet-4.5-thinking": ModelConfig(
        name="claude-sonnet-4.5-thinking",
        provider="anthropic",
        display_name="Claude Sonnet 4.5 Thinking",
        description="Sonnet with thinking capabilities",
    ),
    "claude-haiku-4.5-thinking": ModelConfig(
        name="claude-haiku-4.5-thinking",
        provider="anthropic",
        display_name="Claude Haiku 4.5 Thinking",
        description="Haiku with thinking capabilities",
    ),
    "claude-4.1-opus-thinking": ModelConfig(
        name="claude-4.1-opus-thinking",
        provider="anthropic",
        display_name="Claude 4.1 Opus Thinking",
        description="Previous generation opus with thinking",
    ),
    "claude-4.1-opus": ModelConfig(
        name="claude-4.1-opus",
        provider="anthropic",
        display_name="Claude 4.1 Opus",
        description="Previous generation opus model",
    ),
    "claude-sonnet-4.5": ModelConfig(
        name="claude-sonnet-4.5",
        provider="anthropic",
        display_name="Claude Sonnet 4.5",
        description="Latest Sonnet model",
    ),
    "claude-4-sonnet": ModelConfig(
        name="claude-4-sonnet",
        provider="anthropic",
        display_name="Claude 4 Sonnet",
        description="Previous generation sonnet",
    ),
    "claude-haiku-4.5": ModelConfig(
        name="claude-haiku-4.5",
        provider="anthropic",
        display_name="Claude Haiku 4.5",
        description="Latest Haiku model",
    ),
    # Legacy Anthropic models
    "claude-3-5-sonnet-20241022": ModelConfig(
        name="claude-3-5-sonnet-20241022",
        provider="anthropic",
        display_name="Claude 3.5 Sonnet",
        description="Previous generation Sonnet",
    ),
    "claude-3-opus-20240229": ModelConfig(
        name="claude-3-opus-20240229",
        provider="anthropic",
        display_name="Claude 3 Opus",
        description="Previous generation Opus",
    ),
    "claude-3-sonnet-20240229": ModelConfig(
        name="claude-3-sonnet-20240229",
        provider="anthropic",
        display_name="Claude 3 Sonnet",
        description="Previous generation Sonnet",
    ),
    "claude-3-haiku-20240307": ModelConfig(
        name="claude-3-haiku-20240307",
        provider="anthropic",
        display_name="Claude 3 Haiku",
        description="Previous generation Haiku",
    ),
    
    # Google Models - Top Language & Reasoning Models
    "gemini-3-pro-preview-high": ModelConfig(
        name="gemini-3-pro-preview-high",
        provider="google",
        display_name="Gemini 3 Pro Preview (High)",
        description="Current #1 in Intelligence Index",
    ),
    "gemini-3-flash": ModelConfig(
        name="gemini-3-flash",
        provider="google",
        display_name="Gemini 3 Flash",
        description="Top efficient/reasoning model",
    ),
    "gemini-3-pro-preview-low": ModelConfig(
        name="gemini-3-pro-preview-low",
        provider="google",
        display_name="Gemini 3 Pro Preview (Low)",
        description="Lower cost Gemini 3 Pro",
    ),
    "gemini-2.5-pro-max-thinking": ModelConfig(
        name="gemini-2.5-pro-max-thinking",
        provider="google",
        display_name="Gemini 2.5 Pro (Max Thinking)",
        description="Gemini 2.5 Pro with max thinking",
    ),
    "gemini-2.5-flash-max-thinking": ModelConfig(
        name="gemini-2.5-flash-max-thinking",
        provider="google",
        display_name="Gemini 2.5 Flash (Max Thinking)",
        description="Gemini 2.5 Flash with max thinking",
    ),
    "gemini-2.5-flash-lite-max-thinking": ModelConfig(
        name="gemini-2.5-flash-lite-max-thinking",
        provider="google",
        display_name="Gemini 2.5 Flash Lite (Max Thinking)",
        description="Lite version with max thinking",
    ),
    # Legacy Google models
    "gemini-1.5-pro": ModelConfig(
        name="gemini-1.5-pro",
        provider="google",
        display_name="Gemini 1.5 Pro",
        description="Previous generation Pro model",
    ),
    "gemini-1.5-flash": ModelConfig(
        name="gemini-1.5-flash",
        provider="google",
        display_name="Gemini 1.5 Flash",
        description="Previous generation Flash model",
    ),
    "gemini-pro": ModelConfig(
        name="gemini-pro",
        provider="google",
        display_name="Gemini Pro",
        description="Previous generation Gemini",
    ),
    
    # Mistral Models
    "devstral-2": ModelConfig(
        name="devstral-2",
        provider="mistral",
        display_name="Devstral 2",
        description="Latest Devstral model",
    ),
    "mistral-large-latest": ModelConfig(
        name="mistral-large-latest",
        provider="mistral",
        display_name="Mistral Large",
        description="Most capable Mistral model",
    ),
    "mistral-medium-latest": ModelConfig(
        name="mistral-medium-latest",
        provider="mistral",
        display_name="Mistral Medium",
        description="Balanced Mistral model",
    ),
    "mistral-small-latest": ModelConfig(
        name="mistral-small-latest",
        provider="mistral",
        display_name="Mistral Small",
        description="Fastest Mistral model",
    ),
    
    # Cohere Models
    "command-r-plus": ModelConfig(
        name="command-r-plus",
        provider="cohere",
        display_name="Command R+",
        description="Most capable Cohere model",
    ),
    "command-r": ModelConfig(
        name="command-r",
        provider="cohere",
        display_name="Command R",
        description="Balanced Cohere model",
    ),
}


def get_model_config(model_name: str) -> ModelConfig | None:
    """Get configuration for a model by name."""
    return MODELS.get(model_name)


def get_models_by_provider(provider: Provider) -> list[ModelConfig]:
    """Get all models for a specific provider."""
    return [config for config in MODELS.values() if config.provider == provider]


def _get_config_path() -> Path:
    """Get the path to the config file."""
    config_dir = Path.home() / ".config" / "ai_auto_commit"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def _load_config() -> dict:
    """Load configuration from file."""
    config_path = _get_config_path()
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_config(config: dict) -> None:
    """Save configuration to file."""
    config_path = _get_config_path()
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        raise RuntimeError(f"Failed to save config: {e}")


def set_default_model(model_name: str) -> None:
    """
    Set the default AI model to use.
    
    Parameters
    ----------
    model_name : str
        The name of the model to set as default. Must be a valid model name
        from MODELS or a custom model name.
    
    Raises
    ------
    ValueError
        If the model name is invalid (only if it's in MODELS and doesn't exist).
    
    Examples
    --------
    >>> set_default_model("gpt-4o")
    >>> set_default_model("claude-3-5-sonnet-20241022")
    """
    # Validate model if it's in our known models
    if model_name in MODELS:
        config = _load_config()
        config["default_model"] = model_name
        _save_config(config)
    else:
        # Allow custom model names
        config = _load_config()
        config["default_model"] = model_name
        _save_config(config)


def get_default_model() -> str:
    """
    Get the default model name.
    
    Checks in this order:
    1. User-configured default (from config file)
    2. Model with default=True flag in MODELS
    3. Fallback to "gpt-4o-mini"
    """
    # First, check user-configured default
    config = _load_config()
    if "default_model" in config:
        user_default = config["default_model"]
        # Validate it exists in MODELS if it's a known model
        if user_default in MODELS or user_default:
            return user_default
    
    # Second, check for model with default=True flag
    for name, config_obj in MODELS.items():
        if config_obj.default:
            return name
    
    # Fallback
    return "gpt-4o-mini"


def get_provider_display_name(provider: Provider) -> str:
    """Get a human-readable provider name."""
    provider_names = {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "google": "Google (Gemini)",
        "mistral": "Mistral AI",
        "cohere": "Cohere",
    }
    return provider_names.get(provider, provider.title())


def get_all_providers() -> list[Provider]:
    """Get list of all available providers."""
    return list(set(config.provider for config in MODELS.values()))


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
    
    Examples
    --------
    >>> set_token_budget(500000)
    """
    if not isinstance(budget, int) or budget <= 0:
        raise ValueError("Token budget must be a positive integer")
    
    config = _load_config()
    config["token_budget"] = budget
    _save_config(config)


def get_token_budget() -> int:
    """
    Get the token budget limit.
    
    Returns
    -------
    int
        The configured token budget, or 250000 if not set.
    """
    config = _load_config()
    return config.get("token_budget", 250_000)


def get_config() -> dict:
    """
    Get the full configuration dictionary.
    
    Returns
    -------
    dict
        The complete configuration dictionary.
    """
    return _load_config()


def get_config_path() -> Path:
    """
    Get the path to the configuration file.

    Returns
    -------
    Path
        The path to the config file.
    """
    return _get_config_path()


def set_api_key(provider: Provider, api_key: str) -> None:
    """
    Set the API key for a specific provider.

    Parameters
    ----------
    provider : Provider
        The AI provider (openai, anthropic, google, mistral, cohere).
    api_key : str
        The API key to store.

    Examples
    --------
    >>> set_api_key("openai", "sk-...")
    >>> set_api_key("anthropic", "sk-ant-...")
    """
    config = _load_config()
    if "api_keys" not in config:
        config["api_keys"] = {}
    config["api_keys"][provider] = api_key.strip()
    _save_config(config)


def get_api_key(provider: Provider) -> str | None:
    """
    Get the stored API key for a specific provider from config file.

    Parameters
    ----------
    provider : Provider
        The AI provider.

    Returns
    -------
    str | None
        The API key if found, None otherwise.
    """
    config = _load_config()
    api_keys = config.get("api_keys", {})
    return api_keys.get(provider)


def remove_api_key(provider: Provider) -> None:
    """
    Remove the stored API key for a specific provider.

    Parameters
    ----------
    provider : Provider
        The AI provider.
    """
    config = _load_config()
    if "api_keys" in config and provider in config["api_keys"]:
        del config["api_keys"][provider]
        _save_config(config)


def get_all_api_keys() -> dict[Provider, str]:
    """
    Get all stored API keys.

    Returns
    -------
    dict[Provider, str]
        Dictionary mapping providers to their API keys.
    """
    config = _load_config()
    return config.get("api_keys", {})

