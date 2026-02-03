"""Token budget management for controlling API usage."""

from __future__ import annotations

import threading

# Import config functions - handle both package and direct script execution
try:
    from .models import _load_local_config
except ImportError:
    from ai_auto_commit.models import _load_local_config

_tokens_spent: int = 0
_budget_lock = threading.Lock()

# Default token budget
_DEFAULT_TOKEN_BUDGET: int = 250_000


def _get_max_token_budget() -> int:
    """Get the maximum token budget from config or default."""
    config = _load_local_config()
    return config.get("token_budget", _DEFAULT_TOKEN_BUDGET)


def get_max_token_budget() -> int:
    """Get the maximum token budget (public API)."""
    return _get_max_token_budget()


def try_reserve_tokens(needed: int) -> bool:
    """
    Atomically check + reserve `needed` tokens.
    Returns False if the reservation would push us over MAX_TOKEN_BUDGET.
    """
    global _tokens_spent
    with _budget_lock:
        max_budget = _get_max_token_budget()
        if _tokens_spent + needed > max_budget:
            return False
        _tokens_spent += needed
        return True


def reserve_tokens_soft(needed: int) -> bool:
    """
    Reserve tokens without enforcing the budget (soft ceiling).
    Always succeeds; use during batched processing when the limit is advisory.
    """
    global _tokens_spent
    with _budget_lock:
        _tokens_spent += needed
        return True


def is_over_budget() -> bool:
    """Return True if current usage exceeds the configured token budget."""
    with _budget_lock:
        return _tokens_spent > _get_max_token_budget()


def refund_tokens(count: int) -> None:
    """Return tokens to the pool (only used if you abort before the call)."""
    global _tokens_spent
    with _budget_lock:
        _tokens_spent = max(0, _tokens_spent - count)


def reset_token_budget() -> None:
    """Reset the token budget at the start of a new run."""
    global _tokens_spent
    with _budget_lock:
        _tokens_spent = 0


def get_tokens_spent() -> int:
    """Get the current number of tokens spent."""
    global _tokens_spent
    with _budget_lock:
        return _tokens_spent

