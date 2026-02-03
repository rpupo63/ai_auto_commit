
import pytest
from unittest.mock import MagicMock, patch
from ai_auto_commit.large_diff_handler import (
    get_model_context_limit,
    check_diff_exceeds_limit,
    truncate_diff_to_limit,
)

def test_get_model_context_limit():
    assert get_model_context_limit("gpt-4o") == 128_000
    assert get_model_context_limit("gpt-4") == 8_192
    assert get_model_context_limit("unknown-model") == 8_000
    assert get_model_context_limit("claude-3-5-sonnet") == 200_000

def test_check_diff_exceeds_limit():
    # Very small diff
    diff = "diff --git a/file.txt b/file.txt\n+hello"
    exceeds, count, limit = check_diff_exceeds_limit(diff, "gpt-4")
    assert not exceeds
    assert count > 0
    assert limit > count

    # Mock a large diff by using a model with very small limit if possible,
    # or just check the logic with a huge string.
    huge_diff = "a" * 100_000 # Roughly 25k-100k tokens
    exceeds, count, limit = check_diff_exceeds_limit(huge_diff, "gpt-4")
    assert exceeds
    assert count > limit

def test_truncate_diff_to_limit():
    diff = "diff --git a/a.txt b/a.txt\n+content a\n" * 10
    limit = 20 # very small limit
    truncated = truncate_diff_to_limit(diff, limit)
    assert "[... Diff truncated" in truncated
    assert len(truncated) < len(diff)
