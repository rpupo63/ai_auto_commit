"""LangChain-based LLM client for multiple AI providers."""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage

from .models import ModelConfig, Provider, get_model_config


# Store initialized clients by provider
_providers_initialized: dict[Provider, bool] = {
    "openai": False,
    "anthropic": False,
    "google": False,
    "mistral": False,
    "cohere": False,
}

# Store model instances by model name
_model_instances: dict[str, BaseChatModel] = {}


def initialize_provider(provider: Provider, api_key: str) -> None:
    """Initialize a provider with its API key."""
    global _providers_initialized
    
    if _providers_initialized.get(provider, False):
        return  # Already initialized
    
    if provider == "openai":
        try:
            import os
            os.environ["OPENAI_API_KEY"] = api_key
            _providers_initialized["openai"] = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI: {e}")
    
    elif provider == "anthropic":
        try:
            import os
            os.environ["ANTHROPIC_API_KEY"] = api_key
            _providers_initialized["anthropic"] = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Anthropic: {e}")
    
    elif provider == "google":
        try:
            import os
            os.environ["GOOGLE_API_KEY"] = api_key
            _providers_initialized["google"] = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Google: {e}")
    
    elif provider == "mistral":
        try:
            import os
            os.environ["MISTRAL_API_KEY"] = api_key
            _providers_initialized["mistral"] = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Mistral: {e}")
    
    elif provider == "cohere":
        try:
            import os
            os.environ["COHERE_API_KEY"] = api_key
            _providers_initialized["cohere"] = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Cohere: {e}")
    
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _infer_provider_from_model_name(model_name: str) -> Provider | None:
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
    if model_lower.startswith(("mistral", "devstral", "codestral", "pixtral")):
        return "mistral"

    # Cohere models
    if model_lower.startswith(("command", "embed", "rerank")):
        return "cohere"

    return None


def get_llm(model_name: str, temperature: float = 0.2) -> BaseChatModel:
    """Get a LangChain LLM instance for the specified model."""
    global _model_instances

    # Check cache
    cache_key = f"{model_name}_{temperature}"
    if cache_key in _model_instances:
        return _model_instances[cache_key]

    config = get_model_config(model_name)
    if config:
        provider = config.provider
    else:
        # Try to infer provider from model name for custom models
        provider = _infer_provider_from_model_name(model_name)
        if not provider:
            raise ValueError(
                f"Unknown model: {model_name}. "
                f"Could not infer provider. Use a model name starting with "
                f"'gpt-' (OpenAI), 'claude' (Anthropic), 'gemini' (Google), "
                f"'mistral' (Mistral), or 'command' (Cohere)."
            )
    
    # Ensure provider is initialized
    if not _providers_initialized.get(provider, False):
        # Try to initialize from environment
        import os
        
        env_keys = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "cohere": "COHERE_API_KEY",
        }
        
        key = os.getenv(env_keys[provider])
        if not key:
            raise RuntimeError(
                f"{provider.title()} API key not found. "
                f"Set {env_keys[provider]} environment variable or call init_provider()."
            )
        initialize_provider(provider, key)
    
    # Create model instance based on provider
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            timeout=60,
        )
    
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            model=model_name,
            temperature=temperature,
            timeout=60,
        )
    
    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            timeout=60,
        )
    
    elif provider == "mistral":
        from langchain_mistralai import ChatMistralAI
        llm = ChatMistralAI(
            model=model_name,
            temperature=temperature,
            timeout=60,
        )
    
    elif provider == "cohere":
        from langchain_cohere import ChatCohere
        llm = ChatCohere(
            model=model_name,
            temperature=temperature,
        )
    
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    
    # Cache the instance
    _model_instances[cache_key] = llm
    return llm


def invoke_llm(
    model_name: str,
    prompt: str,
    temperature: float = 0.2,
    max_tokens: Optional[int] = None,
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
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])

        # Handle different response content formats
        if hasattr(response, "content"):
            content = response.content
            # Google models may return a list of content parts
            if isinstance(content, list):
                # Join text parts together
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
    except Exception as e:
        raise RuntimeError(f"Error invoking {model_name}: {e}")


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
    
    # For now, use tiktoken estimation (works for OpenAI models)
    # For other models, this is an approximation
    prompt_tokens = token_len(prompt)
    completion_tokens = token_len(response)
    
    return prompt_tokens, completion_tokens

