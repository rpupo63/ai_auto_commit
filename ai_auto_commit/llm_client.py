"""LangChain-based LLM client for multiple AI providers.

Uses ai_model_picker for configuration and model resolution,
with LangChain as the execution backend.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ai_model_picker import (
    get_available_providers,
    get_model_api_id,
    get_api_key_with_fallback,
    get_provider_env_var,
)

# App name for config lookup
APP_NAME = "ai_auto_commit"

# All supported providers
SUPPORTED_PROVIDERS = [
    "openai", "anthropic", "google", "mistral", "cohere",
    "deepseek", "xai", "meta", "alibaba",
]

# Store initialized clients by provider
_providers_initialized: dict[str, bool] = {p: False for p in SUPPORTED_PROVIDERS}

# Store model instances by model name
_model_instances: dict[str, BaseChatModel] = {}


def initialize_provider(provider: str, api_key: str) -> None:
    """Initialize a provider with its API key."""
    global _providers_initialized

    if _providers_initialized.get(provider, False):
        return  # Already initialized

    # Set environment variable for the provider
    env_var = get_provider_env_var(provider)
    if env_var:
        os.environ[env_var] = api_key
        _providers_initialized[provider] = True
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _infer_provider_from_model_name(model_name: str) -> Optional[str]:
    """Infer the provider from a model name for custom/unknown models."""
    model_lower = model_name.lower()

    # OpenAI models
    if model_lower.startswith(("gpt-", "o1", "o3", "text-", "davinci", "curie", "babbage", "ada")):
        return "openai"

    # Anthropic models
    if model_lower.startswith("claude"):
        return "anthropic"

    # Google models
    if model_lower.startswith("gemini"):
        return "google"

    # Mistral models
    if model_lower.startswith(("mistral", "devstral", "codestral", "pixtral", "ministral")):
        return "mistral"

    # Cohere models
    if model_lower.startswith(("command", "embed", "rerank")):
        return "cohere"

    # DeepSeek models
    if model_lower.startswith("deepseek"):
        return "deepseek"

    # xAI / Grok models
    if model_lower.startswith("grok"):
        return "xai"

    # Meta / Llama models
    if model_lower.startswith(("llama", "meta")):
        return "meta"

    # Alibaba / Qwen models
    if model_lower.startswith("qwen"):
        return "alibaba"

    return None


def _get_provider_for_model(model_name: str) -> str:
    """Get the provider for a model, checking config then inferring."""
    # First check if it's a known model in provider_models.json
    providers = get_available_providers()
    for provider_key, provider_data in providers.items():
        if provider_key == "none":
            continue
        models = provider_data.get("models", [])
        model_api_ids = provider_data.get("model_api_ids", {})

        # Check display names
        if model_name in models:
            return provider_key

        # Check API IDs
        if model_name in model_api_ids.values():
            return provider_key

    # Try to infer from model name
    inferred = _infer_provider_from_model_name(model_name)
    if inferred:
        return inferred

    raise ValueError(
        f"Unknown model: {model_name}. "
        f"Could not determine provider. Use a model name starting with "
        f"'gpt-' (OpenAI), 'claude' (Anthropic), 'gemini' (Google), "
        f"'mistral' (Mistral), 'command' (Cohere), 'deepseek' (DeepSeek), "
        f"'grok' (xAI), 'llama' (Meta), or 'qwen' (Alibaba)."
    )


def _ensure_provider_initialized(provider: str) -> None:
    """Ensure a provider is initialized, loading key from config or env."""
    if _providers_initialized.get(provider, False):
        return

    key = get_api_key_with_fallback(provider, APP_NAME)
    if not key:
        env_var = get_provider_env_var(provider) or f"{provider.upper()}_API_KEY"
        raise RuntimeError(
            f"{provider.title()} API key not found. "
            f"Set {env_var} environment variable or run 'autocommit init'."
        )

    initialize_provider(provider, key)


def _create_openai_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Create OpenAI LLM instance."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        timeout=60,
    )


def _create_anthropic_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Create Anthropic LLM instance."""
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model=model_name,
        temperature=temperature,
        timeout=60,
    )


def _create_google_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Create Google LLM instance."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        timeout=60,
    )


def _create_mistral_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Create Mistral LLM instance."""
    from langchain_mistralai import ChatMistralAI
    return ChatMistralAI(
        model=model_name,
        temperature=temperature,
        timeout=60,
    )


def _create_cohere_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Create Cohere LLM instance (no timeout support)."""
    from langchain_cohere import ChatCohere
    return ChatCohere(
        model=model_name,
        temperature=temperature,
        # Cohere doesn't support timeout parameter
    )


def _create_deepseek_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Create DeepSeek LLM instance (OpenAI-compatible)."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        timeout=60,
        base_url="https://api.deepseek.com",
        api_key=os.environ.get("DEEPSEEK_API_KEY"),
    )


def _create_xai_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Create xAI (Grok) LLM instance (OpenAI-compatible)."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        timeout=60,
        base_url="https://api.x.ai/v1",
        api_key=os.environ.get("XAI_API_KEY"),
    )


def _create_meta_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Create Meta (Llama) LLM instance via Together.ai (OpenAI-compatible)."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        timeout=60,
        base_url="https://api.together.xyz/v1",
        api_key=os.environ.get("META_AI_API_KEY"),
    )


def _create_alibaba_llm(model_name: str, temperature: float) -> BaseChatModel:
    """Create Alibaba (Qwen) LLM instance via DashScope."""
    # DashScope doesn't have official LangChain integration,
    # use OpenAI-compatible endpoint
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        timeout=60,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=os.environ.get("DASHSCOPE_API_KEY"),
    )


# Provider to LLM factory mapping
_LLM_FACTORIES = {
    "openai": _create_openai_llm,
    "anthropic": _create_anthropic_llm,
    "google": _create_google_llm,
    "mistral": _create_mistral_llm,
    "cohere": _create_cohere_llm,
    "deepseek": _create_deepseek_llm,
    "xai": _create_xai_llm,
    "meta": _create_meta_llm,
    "alibaba": _create_alibaba_llm,
}


def get_llm(model_name: str, temperature: float = 0.2) -> BaseChatModel:
    """Get a LangChain LLM instance for the specified model."""
    global _model_instances

    # Check cache
    cache_key = f"{model_name}_{temperature}"
    if cache_key in _model_instances:
        return _model_instances[cache_key]

    # Get provider for this model
    provider = _get_provider_for_model(model_name)

    # Ensure provider is initialized
    _ensure_provider_initialized(provider)

    # Resolve model name to API ID
    api_model = get_model_api_id(model_name, provider, APP_NAME)

    # Create model instance
    if provider not in _LLM_FACTORIES:
        raise ValueError(f"Unsupported provider: {provider}")

    llm = _LLM_FACTORIES[provider](api_model, temperature)

    # Cache the instance
    _model_instances[cache_key] = llm
    return llm


def invoke_llm(
    model_name: str,
    prompt: str,
    temperature: float = 0.2,
    max_tokens: Optional[int] = None,
    system_prompt: Optional[str] = None,
) -> str:
    """
    Invoke an LLM with a prompt and return the response text.

    Parameters
    ----------
    model_name : str
        Name of the model to use.
    prompt : str
        The prompt to send to the model.
    temperature : float
        Sampling temperature.
    max_tokens : int, optional
        Maximum tokens in the response.
    system_prompt : str, optional
        Optional system message to set context.

    Returns
    -------
    str
        The model's response text.
    """
    llm = get_llm(model_name, temperature)

    # Set max_tokens if provided (not all models support this)
    if max_tokens:
        try:
            if hasattr(llm, "max_tokens"):
                llm.max_tokens = max_tokens
        except Exception:
            pass  # Some models don't support max_tokens parameter

    try:
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        response = llm.invoke(messages)

        # Handle different response content formats
        return _extract_response_content(response)

    except Exception as e:
        raise RuntimeError(f"Error invoking {model_name}: {e}")


def _extract_response_content(response: Any) -> str:
    """Extract text content from LangChain response."""
    if hasattr(response, "content"):
        content = response.content
        # Google models may return a list of content parts
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, str):
                    text_parts.append(part)
                elif hasattr(part, "text"):
                    text_parts.append(part.text)
                elif isinstance(part, dict) and "text" in part:
                    text_parts.append(part["text"])
            return "".join(text_parts)
        elif isinstance(content, str):
            return content
        else:
            return str(content)
    return str(response)


def get_token_usage(
    model_name: str,
    prompt: str,
    response: str,
) -> tuple[int, int]:
    """
    Estimate token usage for a prompt and response.

    Returns
    -------
    tuple[int, int]
        (prompt_tokens, completion_tokens)
    """
    from .token_utils import token_len

    # Use tiktoken estimation (approximation for all providers)
    prompt_tokens = token_len(prompt)
    completion_tokens = token_len(response)

    return prompt_tokens, completion_tokens
