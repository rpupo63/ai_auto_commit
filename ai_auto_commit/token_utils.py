"""Token counting utilities."""

from __future__ import annotations

import tiktoken

# Initialize tiktoken encoder for token counting
ENC = tiktoken.encoding_for_model("gpt-4o-mini")


def token_len(text: str) -> int:
    """Get token count for text using tiktoken."""
    return len(ENC.encode(text))

