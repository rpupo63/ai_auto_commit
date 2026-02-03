"""API client utilities for multiple AI providers."""

from __future__ import annotations

import socket

from .llm_client import initialize_provider
from .models import Provider, get_all_providers, get_api_key


def init(
    api_key: str | None = None,
    provider: Provider = "openai",
    **kwargs: str,
) -> None:
    """
    Initialize AI provider API keys.

    Parameters
    ----------
    api_key : str, optional
        API key for the specified provider. If not provided, will attempt
        to load from config file.
    provider : Provider, optional
        Provider to initialize (default: "openai"). Can be one of:
        "openai", "anthropic", "google", "mistral", "cohere"
    **kwargs : str
        Additional provider API keys. Keys should be provider names,
        values should be API keys. Example: init(anthropic="key...", google="key...")

    Raises
    ------
    RuntimeError
        If API key is not provided and not found in config file.
    """
    from .models import get_all_api_keys

    # Initialize the main provider if explicit key provided
    if api_key is not None:
        initialize_provider(provider, api_key.strip())

    # Initialize additional providers from kwargs
    for prov, key in kwargs.items():
        if prov in get_all_providers():
            initialize_provider(prov, key.strip())

    # Initialize ALL providers that have API keys stored in config file
    # This ensures the default model's provider is always initialized
    stored_keys = get_all_api_keys()
    for prov, key in stored_keys.items():
        if key and prov in get_all_providers():
            initialize_provider(prov, key.strip())


def ensure_initialized() -> None:
    """Ensure at least one provider is initialized."""
    # This is a no-op now - providers are initialized lazily when needed
    pass


def check_network_connectivity(
    host: str = "api.openai.com", port: int = 443, timeout: int = 5
) -> bool:
    """Check if we can connect to OpenAI's API server."""
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except (socket.timeout, socket.error):
        return False


def generate_fallback_commit_message() -> str:
    """Generate a simple fallback commit message when OpenAI API fails."""
    print("\nOpenAI API failed. You can:")
    print("1. Press Enter to use a generic commit message")
    print("2. Type a custom commit message")
    
    user_input = input(
        "\nEnter custom commit message (or press Enter for default): "
    ).strip()
    
    if user_input:
        return user_input
    else:
        return "chore: update files\n\nGeneral file updates and improvements"

