"""Handler for large diffs that exceed model token limits.

Provides strategies for handling oversized diffs:
1. Split & Summarize: Split diff into chunks, summarize each, recursively combine
2. Truncate: Cut off content to fit within token limit
"""

from __future__ import annotations

import sys
from typing import List, Literal, Optional

# Import modules - handle both package and direct script execution
try:
    from .commit_generation import split_diff_by_file
    from .llm_client import invoke_llm, get_token_usage
    from .prompts import PROMPT_HEADER
    from .token_budget import get_tokens_spent, get_max_token_budget, refund_tokens, try_reserve_tokens, reserve_tokens_soft, is_over_budget
    from .token_utils import token_len
except ImportError:
    from commit_generation import split_diff_by_file
    from llm_client import invoke_llm, get_token_usage
    from prompts import PROMPT_HEADER
    from token_budget import get_tokens_spent, get_max_token_budget, refund_tokens, try_reserve_tokens, reserve_tokens_soft, is_over_budget
    from token_utils import token_len


# Model context window sizes (in tokens)
# These are approximate and conservative estimates
MODEL_CONTEXT_LIMITS = {
    # OpenAI models
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4": 8_192,
    "gpt-3.5-turbo": 16_385,
    "o1": 200_000,
    "o1-mini": 128_000,
    "o1-preview": 128_000,
    "o3-mini": 200_000,
    # Anthropic models
    "claude-3-5-sonnet-20241022": 200_000,
    "claude-3-5-haiku-20241022": 200_000,
    "claude-3-opus-20240229": 200_000,
    "claude-3-sonnet-20240229": 200_000,
    "claude-3-haiku-20240307": 200_000,
    # Google models
    "gemini-pro": 32_000,
    "gemini-1.5-pro": 1_000_000,
    "gemini-1.5-flash": 1_000_000,
    "gemini-2.0-flash": 1_000_000,
    "gemini-3-flash-preview": 1_000_000,
    # Mistral models
    "mistral-large": 128_000,
    "mistral-medium": 32_000,
    "mistral-small": 32_000,
    "codestral": 32_000,
    "devstral": 128_000,
    # DeepSeek models
    "deepseek-chat": 64_000,
    "deepseek-coder": 64_000,
    # xAI models
    "grok-2": 128_000,
    # Meta/Llama models
    "llama-3-70b": 8_192,
    "llama-3-8b": 8_192,
    "llama-3.1-405b": 128_000,
    "llama-3.1-70b": 128_000,
    # Alibaba/Qwen models
    "qwen-turbo": 8_000,
    "qwen-plus": 32_000,
    "qwen-max": 32_000,
}

# Default context limit for unknown models
DEFAULT_CONTEXT_LIMIT = 8_000

# Reserve tokens for system prompt and response
RESERVED_TOKENS = 2_000


def get_model_context_limit(model_name: str) -> int:
    """
    Get the context window limit for a model.

    Parameters
    ----------
    model_name : str
        The model name to look up.

    Returns
    -------
    int
        The context window size in tokens.
    """
    # Try exact match first
    if model_name in MODEL_CONTEXT_LIMITS:
        return MODEL_CONTEXT_LIMITS[model_name]

    # Try prefix matching for versioned models
    model_lower = model_name.lower()
    for known_model, limit in MODEL_CONTEXT_LIMITS.items():
        if model_lower.startswith(known_model.lower()):
            return limit
        if known_model.lower() in model_lower:
            return limit

    # Infer from model family
    if "gpt-4" in model_lower:
        return 128_000
    if "gpt-3" in model_lower:
        return 16_385
    if "claude" in model_lower:
        return 200_000
    if "gemini" in model_lower:
        return 32_000
    if "mistral" in model_lower:
        return 32_000
    if "deepseek" in model_lower:
        return 64_000
    if "grok" in model_lower:
        return 128_000
    if "llama" in model_lower:
        return 8_192
    if "qwen" in model_lower:
        return 8_000

    return DEFAULT_CONTEXT_LIMIT


def estimate_diff_tokens(diff: str) -> int:
    """
    Estimate the number of tokens in a diff.

    Parameters
    ----------
    diff : str
        The git diff content.

    Returns
    -------
    int
        Estimated token count.
    """
    return token_len(diff)


def get_effective_token_limit(model_name: str) -> int:
    """
    Get the effective token limit for input (context limit minus reserved).

    Parameters
    ----------
    model_name : str
        The model name.

    Returns
    -------
    int
        The effective input token limit.
    """
    context_limit = get_model_context_limit(model_name)
    # Reserve space for system prompt and response
    return context_limit - RESERVED_TOKENS


def check_diff_exceeds_limit(diff: str, model_name: str) -> tuple[bool, int, int]:
    """
    Check if a diff exceeds the model's token limit.

    Parameters
    ----------
    diff : str
        The git diff content.
    model_name : str
        The model to check against.

    Returns
    -------
    tuple[bool, int, int]
        (exceeds_limit, diff_tokens, model_limit)
    """
    diff_tokens = estimate_diff_tokens(diff)
    effective_limit = get_effective_token_limit(model_name)

    # Account for prompt header
    prompt_overhead = token_len(PROMPT_HEADER) + 100  # Extra buffer
    available_for_diff = effective_limit - prompt_overhead

    return diff_tokens > available_for_diff, diff_tokens, available_for_diff


def prompt_large_diff_strategy() -> Literal["split", "truncate", "cancel"]:
    """
    Prompt the user to choose a strategy for handling a large diff.

    Returns
    -------
    Literal["split", "truncate", "cancel"]
        The chosen strategy.
    """
    print("\n" + "=" * 60)
    print("⚠️  Large Diff Detected")
    print("=" * 60)
    print("\nThe diff is too large for the model's context window.")
    print("Please choose how to handle this:\n")
    print("  1. Split & Summarize (Recommended)")
    print("     → Split diff into chunks, generate summaries for each,")
    print("       then recursively combine summaries into final commit message.")
    print("     → More accurate but uses more API tokens.\n")
    print("  2. Truncate")
    print("     → Cut off content beyond the token limit.")
    print("     → Faster and cheaper but may miss changes at the end.\n")
    print("  3. Cancel")
    print("     → Abort the operation.\n")

    while True:
        try:
            choice = input("Select strategy [1-3, default: 1]: ").strip()

            if not choice or choice == "1":
                return "split"
            elif choice == "2":
                return "truncate"
            elif choice == "3":
                return "cancel"
            else:
                print("Please enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
            return "cancel"


def truncate_diff_to_limit(diff: str, token_limit: int) -> str:
    """
    Truncate a diff to fit within the token limit.

    Tries to truncate at file boundaries when possible.

    Parameters
    ----------
    diff : str
        The git diff content.
    token_limit : int
        Maximum tokens allowed.

    Returns
    -------
    str
        Truncated diff with notice appended.
    """
    current_tokens = token_len(diff)

    if current_tokens <= token_limit:
        return diff

    # Try to truncate at file boundaries
    chunks = split_diff_by_file(diff)

    truncated_chunks: List[str] = []
    total_tokens = 0
    truncation_notice_tokens = token_len("\n\n[... Diff truncated due to token limit ...]")
    available_tokens = token_limit - truncation_notice_tokens

    for chunk in chunks:
        chunk_tokens = token_len(chunk)
        if total_tokens + chunk_tokens <= available_tokens:
            truncated_chunks.append(chunk)
            total_tokens += chunk_tokens
        else:
            # Can't fit this whole chunk, try to include partial
            remaining_tokens = available_tokens - total_tokens
            if remaining_tokens > 100:  # Only include if meaningful
                # Rough character estimate (4 chars per token average)
                char_limit = remaining_tokens * 4
                partial_chunk = chunk[:char_limit]
                # Try to end at a newline
                last_newline = partial_chunk.rfind('\n')
                if last_newline > len(partial_chunk) // 2:
                    partial_chunk = partial_chunk[:last_newline]
                truncated_chunks.append(partial_chunk)
            break

    truncated_diff = "".join(truncated_chunks)
    files_included = len(truncated_chunks)
    files_total = len(chunks)

    notice = (
        f"\n\n[... Diff truncated: showing {files_included}/{files_total} files "
        f"({token_len(truncated_diff):,}/{current_tokens:,} tokens) ...]"
    )

    return truncated_diff + notice


def split_and_summarize_diff(
    diff: str,
    model: str,
    temperature: float,
    max_chunk_tokens: int = 4000,
) -> str:
    """
    Split a large diff into manageable chunks, summarize each, then combine.

    Uses a recursive approach:
    1. Split diff by file
    2. Group files into chunks that fit within limit
    3. Summarize each chunk
    4. If summaries are still too large, recursively summarize
    5. Generate final commit message from summaries

    Parameters
    ----------
    diff : str
        The git diff content.
    model : str
        Model to use for summarization.
    temperature : float
        Sampling temperature.
    max_chunk_tokens : int
        Maximum tokens per chunk for summarization.

    Returns
    -------
    str
        The generated commit message.
    """
    import concurrent.futures

    print("  ⚠️  Token budget is a soft ceiling during batched processing; usage may exceed the configured limit.")
    chunks = split_diff_by_file(diff)
    print(f"  → Split into {len(chunks)} file diffs")

    # Group chunks into batches that fit within token limit
    batches: List[List[str]] = []
    current_batch: List[str] = []
    current_batch_tokens = 0

    for chunk in chunks:
        chunk_tokens = token_len(chunk)

        if chunk_tokens > max_chunk_tokens:
            # Single file is too large, will be truncated during summarization
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_batch_tokens = 0
            batches.append([chunk])
        elif current_batch_tokens + chunk_tokens <= max_chunk_tokens:
            current_batch.append(chunk)
            current_batch_tokens += chunk_tokens
        else:
            if current_batch:
                batches.append(current_batch)
            current_batch = [chunk]
            current_batch_tokens = chunk_tokens

    if current_batch:
        batches.append(current_batch)

    print(f"  → Grouped into {len(batches)} batches for summarization")

    # Summarize each batch
    batch_summaries: List[str] = []

    def summarize_batch(batch: List[str]) -> str:
        """Summarize a batch of file diffs."""
        combined = "\n".join(batch)

        # If batch is too large, truncate it
        if token_len(combined) > max_chunk_tokens:
            combined = truncate_diff_to_limit(combined, max_chunk_tokens)

        prompt = (
            "Summarize the following git diff changes in 2-5 bullet points. "
            "Each bullet should start with a verb (Add, Fix, Update, Remove, etc.) "
            "and be concise (max 15 words each):\n\n" + combined
        )

        est_prompt = token_len(prompt)
        est_completion = 200

        reserve_tokens_soft(est_prompt + est_completion)

        try:
            content = invoke_llm(
                model_name=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=est_completion,
            )

            prompt_tokens, completion_tokens = get_token_usage(model, prompt, content)
            real_spent = prompt_tokens + completion_tokens
            if real_spent < est_prompt + est_completion:
                refund_tokens((est_prompt + est_completion) - real_spent)

            return content.strip() if content else "- Update files"
        except Exception as e:
            refund_tokens(est_prompt + est_completion)
            print(f"  → Warning: Failed to summarize batch: {e}")
            # Fallback
            files = []
            for chunk in batch:
                if "diff --git" in chunk:
                    file_path = chunk.splitlines()[0].split()[-1]
                    files.append(file_path)
            return "- Update " + ", ".join(files[:5]) + ("..." if len(files) > 5 else "")

    # Parallel summarization
    print("  → Summarizing batches...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        batch_summaries = list(pool.map(summarize_batch, batches))

    # Combine summaries
    combined_summaries = "\n\n".join(batch_summaries)
    combined_tokens = token_len(combined_summaries)

    print(f"  → Generated {len(batch_summaries)} batch summaries ({combined_tokens:,} tokens)")

    # Check if we need recursive summarization
    effective_limit = get_effective_token_limit(model)
    if combined_tokens > effective_limit - 500:
        print("  → Summaries still too large, performing recursive summarization...")
        combined_summaries = recursive_summarize(
            combined_summaries, model, temperature, effective_limit - 500
        )

    # Generate final commit message
    msg = generate_final_commit_from_summaries(combined_summaries, model, temperature)
    if is_over_budget():
        spent = get_tokens_spent()
        ceiling = get_max_token_budget()
        print(f"\n  ⚠️  Token usage ({spent:,}) exceeded the soft ceiling ({ceiling:,}).")
    return msg


def recursive_summarize(
    text: str,
    model: str,
    temperature: float,
    target_tokens: int,
) -> str:
    """
    Recursively summarize text until it fits within target token count.

    Parameters
    ----------
    text : str
        Text to summarize.
    model : str
        Model to use.
    temperature : float
        Sampling temperature.
    target_tokens : int
        Target maximum tokens.

    Returns
    -------
    str
        Summarized text.
    """
    current_tokens = token_len(text)

    if current_tokens <= target_tokens:
        return text

    # Split into sections and summarize each
    lines = text.split('\n')
    chunk_size = max(10, len(lines) // 4)  # Split into ~4 chunks

    chunks = []
    for i in range(0, len(lines), chunk_size):
        chunk = '\n'.join(lines[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    summarized_chunks: List[str] = []

    for chunk in chunks:
        prompt = (
            "Condense the following change summaries into 2-3 key bullet points. "
            "Keep the most important changes, start each with a verb:\n\n" + chunk
        )

        est_prompt = token_len(prompt)
        est_completion = 150

        reserve_tokens_soft(est_prompt + est_completion)

        try:
            content = invoke_llm(
                model_name=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=est_completion,
            )

            prompt_tokens, completion_tokens = get_token_usage(model, prompt, content)
            real_spent = prompt_tokens + completion_tokens
            if real_spent < est_prompt + est_completion:
                refund_tokens((est_prompt + est_completion) - real_spent)

            summarized_chunks.append(content.strip() if content else chunk[:200])
        except Exception:
            refund_tokens(est_prompt + est_completion)
            summarized_chunks.append('\n'.join(chunk.split('\n')[:3]))

    combined = '\n\n'.join(summarized_chunks)

    # Check if we need another round
    if token_len(combined) > target_tokens:
        return recursive_summarize(combined, model, temperature, target_tokens)

    return combined


def _commit_message_from_summaries(summaries: str, max_lines: int = 25, max_chars: int = 1200) -> str:
    """Build a usable commit message from summary text when the LLM step fails or returns empty."""
    lines = [ln.strip() for ln in summaries.strip().splitlines() if ln.strip()][:max_lines]
    body = "\n".join(lines)
    if len(body) > max_chars:
        body = body[: max_chars - 3].rsplit("\n", 1)[0] + "\n..."
    if not body:
        return "chore: update multiple files\n\nVarious updates and improvements across the codebase."
    return "chore: batch updates from summaries\n\n" + body


def generate_final_commit_from_summaries(
    summaries: str,
    model: str,
    temperature: float,
) -> str:
    """
    Generate a final commit message from collected summaries.

    Parameters
    ----------
    summaries : str
        Combined summaries of changes.
    model : str
        Model to use.
    temperature : float
        Sampling temperature.

    Returns
    -------
    str
        The final commit message.
    """
    est_completion = 256
    header = (
        PROMPT_HEADER
        + "\nBelow are summaries of all changes in this commit. "
        "Write the final Conventional Commit message:\n\n"
    )
    header_tokens = token_len(header)
    effective_limit = get_effective_token_limit(model)
    max_summary_tokens = max(500, effective_limit - header_tokens - est_completion - 500)
    summary_tokens = token_len(summaries)
    if summary_tokens > max_summary_tokens:
        # Truncate summaries so the prompt fits in context (keep start + end)
        approx_chars_per_token = 4
        keep_chars = (max_summary_tokens // 2) * approx_chars_per_token
        first_part = summaries[:keep_chars].rsplit("\n", 1)[0]
        last_part = summaries[-keep_chars:].split("\n", 1)[-1]
        summaries = first_part + "\n\n[...]\n\n" + last_part
    prompt = header + summaries

    est_prompt = token_len(prompt)

    reserve_tokens_soft(est_prompt + est_completion)

    try:
        content = invoke_llm(
            model_name=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=est_completion,
        )

        prompt_tokens, completion_tokens = get_token_usage(model, prompt, content)
        real_spent = prompt_tokens + completion_tokens
        if real_spent < est_prompt + est_completion:
            refund_tokens((est_prompt + est_completion) - real_spent)

        if content:
            commit_msg = content.strip()
            return commit_msg.strip("`").strip()
        # LLM returned empty: build message from summaries
        return _commit_message_from_summaries(summaries)
    except Exception as e:
        refund_tokens(est_prompt + est_completion)
        print(f"  → Warning: Failed to generate final commit: {e}")
        return _commit_message_from_summaries(summaries)


def handle_large_diff(
    diff: str,
    model: str,
    temperature: float,
    strategy: Optional[Literal["split", "truncate", "cancel"]] = None,
) -> tuple[bool, str]:
    """
    Handle a large diff using the specified or user-chosen strategy.

    Parameters
    ----------
    diff : str
        The git diff content.
    model : str
        Model to use.
    temperature : float
        Sampling temperature.
    strategy : Literal["split", "truncate"], optional
        Strategy to use. If None, prompts user.

    Returns
    -------
    tuple[bool, str]
        (is_final_message, content)
        If is_final_message is True, content is the final commit message.
        If is_final_message is False, content is the (possibly truncated) diff.
    """
    exceeds, diff_tokens, limit = check_diff_exceeds_limit(diff, model)
    # Cap by user's token budget so we respect run limit
    remaining_budget = get_max_token_budget() - get_tokens_spent()
    effective_limit = min(limit, max(0, remaining_budget - 500))
    if not exceeds and diff_tokens <= effective_limit:
        # Diff fits within both model and budget
        return False, diff
    if diff_tokens > effective_limit:
        exceeds = True

    if not exceeds:
        return False, diff

    print(f"\n⚠️  Diff size: {diff_tokens:,} tokens (limit: {effective_limit:,} tokens)")

    # Get strategy from user if not provided
    if strategy is None:
        strategy = prompt_large_diff_strategy()

    if strategy == "cancel":
        raise RuntimeError("Operation cancelled by user due to large diff.")

    if strategy == "truncate":
        print("\n  → Using truncate strategy...")
        truncated = truncate_diff_to_limit(diff, effective_limit)
        print(f"  → Truncated to {token_len(truncated):,} tokens")
        return False, truncated

    # Split and summarize strategy
    print("\n  → Using split & summarize strategy...")
    commit_msg = split_and_summarize_diff(diff, model, temperature)
    return True, commit_msg
