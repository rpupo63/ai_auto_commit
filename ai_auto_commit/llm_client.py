"""LangChain-based LLM client for multiple AI providers.

Uses ai_model_picker for configuration, live catalogs, and preference
instructions, with LangChain as the execution backend.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Dict, Optional, Tuple

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ai_model_picker import (
    get_available_providers,
    get_model_api_id,
    get_api_key_with_fallback,
    get_provider_env_var,
    load_preference,
)

# App name for config lookup
APP_NAME = "ai_auto_commit"

# OpenAI-compatible endpoints (aligned with ai_model_picker.client)
_OPENAI_COMPAT_ENDPOINTS: Dict[str, Tuple[str, Optional[str], Optional[str]]] = {
    # provider -> (default_base_url, base_url_env, api_key_env_override)
    "deepseek": ("https://api.deepseek.com", "DEEPSEEK_BASE_URL", "DEEPSEEK_API_KEY"),
    "xai": ("https://api.x.ai/v1", "XAI_BASE_URL", "XAI_API_KEY"),
    "meta": ("https://api.together.xyz/v1", "META_BASE_URL", "META_AI_API_KEY"),
    "moonshot": ("https://api.moonshot.ai/v1", "MOONSHOT_BASE_URL", "MOONSHOT_API_KEY"),
    "zai": ("https://api.z.ai/api/paas/v4/", "ZAI_BASE_URL", "ZAI_API_KEY"),
    "minimax": ("https://api.minimax.io/v1", "MINIMAX_BASE_URL", "MINIMAX_API_KEY"),
    "perplexity": ("https://api.perplexity.ai", "PERPLEXITY_BASE_URL", "PERPLEXITY_API_KEY"),
    "nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_BASE_URL", "NVIDIA_API_KEY"),
    "bytedance": ("https://ark.cn-beijing.volces.com/api/v3", "BYTEDANCE_BASE_URL", "ARK_API_KEY"),
    "tencent": ("https://api.hunyuan.cloud.tencent.com/v1", "TENCENT_BASE_URL", "HUNYUAN_API_KEY"),
    "xiaomi": ("https://api.xiaomimimo.com/v1", "XIAOMI_BASE_URL", "XIAOMI_API_KEY"),
    "amazon": (
        "https://bedrock-runtime.us-east-1.amazonaws.com/openai/v1",
        "AMAZON_BASE_URL",
        "AMAZON_API_KEY",
    ),
    "stepfun": ("https://api.stepfun.com/v1", "STEPFUN_BASE_URL", "STEPFUN_API_KEY"),
    "alibaba": (
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "ALIBABA_BASE_URL",
        "DASHSCOPE_API_KEY",
    ),
}

# Store initialized clients by provider
_providers_initialized: dict[str, bool] = {}

# Store model instances by model name
_model_instances: dict[str, BaseChatModel] = {}


def get_supported_providers() -> list[str]:
    """Dynamic provider list from the live model_picker catalog."""
    return [k for k in get_available_providers() if k != "none"]


def initialize_provider(provider: str, api_key: str) -> None:
    """Initialize a provider with its API key."""
    if _providers_initialized.get(provider, False):
        return

    env_var = get_provider_env_var(provider)
    if not env_var and provider in _OPENAI_COMPAT_ENDPOINTS:
        env_var = _OPENAI_COMPAT_ENDPOINTS[provider][2]
    if env_var:
        os.environ[env_var] = api_key
        _providers_initialized[provider] = True
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _infer_provider_from_model_name(model_name: str) -> Optional[str]:
    """Infer the provider from a model name for custom/unknown models."""
    model_lower = model_name.lower()

    if model_lower.startswith(("gpt-", "o1", "o3", "o4", "text-", "davinci", "curie", "babbage", "ada")):
        return "openai"
    if model_lower.startswith("claude"):
        return "anthropic"
    if model_lower.startswith("gemini"):
        return "google"
    if model_lower.startswith(("mistral", "devstral", "codestral", "pixtral", "ministral")):
        return "mistral"
    if model_lower.startswith(("command", "embed", "rerank", "north")):
        return "cohere"
    if model_lower.startswith("deepseek"):
        return "deepseek"
    if model_lower.startswith("grok"):
        return "xai"
    if model_lower.startswith(("llama", "meta", "muse")):
        return "meta"
    if model_lower.startswith("qwen"):
        return "alibaba"
    if model_lower.startswith("kimi"):
        return "moonshot"
    if model_lower.startswith("glm"):
        return "zai"
    if model_lower.startswith("minimax"):
        return "minimax"
    if model_lower.startswith("sonar"):
        return "perplexity"
    if model_lower.startswith("nemotron"):
        return "nvidia"
    if model_lower.startswith("seed"):
        return "bytedance"
    if model_lower.startswith(("hy3", "hunyuan")):
        return "tencent"
    if model_lower.startswith("mimo"):
        return "xiaomi"
    if model_lower.startswith("nova"):
        return "amazon"
    if model_lower.startswith("step"):
        return "stepfun"

    return None


def _get_provider_for_model(model_name: str) -> str:
    """Get the provider for a model, checking catalog then inferring."""
    providers = get_available_providers()
    for provider_key, provider_data in providers.items():
        if provider_key == "none":
            continue
        models = provider_data.get("models", [])
        model_api_ids = provider_data.get("model_api_ids", {})

        if model_name in models:
            return provider_key
        if model_name in model_api_ids.values():
            return provider_key

    inferred = _infer_provider_from_model_name(model_name)
    if inferred:
        return inferred

    known = ", ".join(get_supported_providers())
    raise ValueError(
        f"Unknown model: {model_name}. "
        f"Could not determine provider from the live catalog. "
        f"Known providers: {known}."
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


def _create_openai_compat_llm(
    provider: str,
    model_name: str,
    temperature: float,
) -> BaseChatModel:
    """Create an OpenAI-compatible ChatOpenAI client for a provider."""
    from langchain_openai import ChatOpenAI

    default_base, base_env, key_env = _OPENAI_COMPAT_ENDPOINTS[provider]
    base_url = os.getenv(base_env, default_base) if base_env else default_base
    api_key = os.environ.get(key_env) if key_env else None
    if not api_key:
        env_var = get_provider_env_var(provider)
        if env_var:
            api_key = os.environ.get(env_var)

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        timeout=60,
        base_url=base_url,
        api_key=api_key,
    )


def _make_compat_factory(provider: str) -> Callable[[str, float], BaseChatModel]:
    def factory(model_name: str, temperature: float) -> BaseChatModel:
        return _create_openai_compat_llm(provider, model_name, temperature)

    factory.__name__ = f"_create_{provider}_llm"
    return factory


# Provider to LLM factory mapping (native SDKs + OpenAI-compatible)
_LLM_FACTORIES: Dict[str, Callable[[str, float], BaseChatModel]] = {
    "openai": _create_openai_llm,
    "anthropic": _create_anthropic_llm,
    "google": _create_google_llm,
    "mistral": _create_mistral_llm,
    "cohere": _create_cohere_llm,
}
for _compat_provider in _OPENAI_COMPAT_ENDPOINTS:
    _LLM_FACTORIES[_compat_provider] = _make_compat_factory(_compat_provider)


def get_llm(model_name: str, temperature: float = 0.2) -> BaseChatModel:
    """Get a LangChain LLM instance for the specified model."""
    cache_key = f"{model_name}_{temperature}"
    if cache_key in _model_instances:
        return _model_instances[cache_key]

    provider = _get_provider_for_model(model_name)
    _ensure_provider_initialized(provider)
    api_model = get_model_api_id(model_name, provider, APP_NAME)

    if provider not in _LLM_FACTORIES:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Supported: {', '.join(sorted(_LLM_FACTORIES))}."
        )

    llm = _LLM_FACTORIES[provider](api_model, temperature)
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

    When ``system_prompt`` is omitted, uses instructions from the app's
    ModelPreference (``preference.json``) if set.
    """
    llm = get_llm(model_name, temperature)

    if max_tokens:
        try:
            if hasattr(llm, "max_tokens"):
                llm.max_tokens = max_tokens
        except Exception:
            pass

    effective_system = system_prompt
    if effective_system is None:
        pref = load_preference(APP_NAME)
        if pref.instructions:
            effective_system = pref.instructions

    try:
        messages = []
        if effective_system:
            messages.append(SystemMessage(content=effective_system))
        messages.append(HumanMessage(content=prompt))

        response = llm.invoke(messages)
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
