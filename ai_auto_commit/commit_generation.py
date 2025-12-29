"""Commit message generation using hierarchical and smart approaches."""

from __future__ import annotations

import concurrent.futures
from typing import List

# Import modules - handle both package and direct script execution
try:
    from .api_client import check_network_connectivity, generate_fallback_commit_message
    from .llm_client import get_token_usage, invoke_llm
    from .prompts import PROMPT_HEADER
    from .token_budget import get_max_token_budget, refund_tokens, try_reserve_tokens
    from .token_utils import token_len
except ImportError:
    from api_client import check_network_connectivity, generate_fallback_commit_message
    from llm_client import get_token_usage, invoke_llm
    from prompts import PROMPT_HEADER
    from token_budget import get_max_token_budget, refund_tokens, try_reserve_tokens
    from token_utils import token_len


def split_diff_by_file(diff: str) -> List[str]:
    """Return list of 'diff --git ...' chunks."""
    CHUNK_HEADER = "diff --git "
    parts = diff.split(CHUNK_HEADER)
    # first element before the first header is '' – drop it
    return [CHUNK_HEADER + p for p in parts[1:]]


def summarise_file_diff(chunk: str, model: str, temperature: float) -> str:
    """Call OpenAI once for a single-file diff and return 1-line summary."""
    prompt = (
        "Summarise the following git diff in ONE bullet (max 20 words); "
        "start bullet with a verb (Add, Fix, Refactor …):\n\n" + chunk
    )

    # 🛡️ estimate: prompt tokens + ≤64 completion tokens
    est_prompt = token_len(prompt)
    est_completion = 64
    est_total = est_prompt + est_completion
    if not try_reserve_tokens(est_total):
        # Budget exhausted – fall back to a cheap, local summary
        if "diff --git" in chunk:
            file_path = chunk.splitlines()[0].split()[-1]
            return f"- Update {file_path}"
        return "- Update file"

    try:
        content = invoke_llm(
            model_name=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=est_completion,
        )
        
        # Estimate actual token usage
        prompt_tokens, completion_tokens = get_token_usage(model, prompt, content)
        real_spent = prompt_tokens + completion_tokens
        if real_spent < est_total:  # we over-estimated – refund the diff
            refund_tokens(est_total - real_spent)
        
        if content:
            return "- " + content.strip().lstrip("-• ")
        else:
            return "- Update file"

    except Exception as e:
        refund_tokens(est_total)  # nothing spent if request failed
        print(f"  → Warning: Failed to summarize file diff: {e}")
        # Same generic fallback as before …
        if "diff --git" in chunk:
            file_path = chunk.splitlines()[0].split()[-1]
            return f"- Update {file_path}"
        return "- Update file"


def estimate_stage1_budget(
    chunks: List[str], model: str, temperature: float
) -> tuple[int, int]:
    """
    Estimate the token budget needed for stage-1 processing.
    Returns (estimated_tokens, max_files_affordable)
    """
    # Sample a few chunks to estimate average tokens per file
    sample_size = min(10, len(chunks))
    sample_chunks = chunks[:sample_size]
    
    total_sample_tokens = 0
    for chunk in sample_chunks:
        prompt = (
            "Summarise the following git diff in ONE bullet (max 20 words); "
            "start bullet with a verb (Add, Fix, Refactor …):\n\n" + chunk
        )
        total_sample_tokens += token_len(prompt) + 64  # prompt + estimated completion
    
    avg_tokens_per_file = total_sample_tokens / sample_size
    
    # Reserve some budget for stage-2 (about 10% of total budget)
    from .token_budget import get_max_token_budget
    max_budget = get_max_token_budget()
    stage2_reserve = max_budget // 10
    available_for_stage1 = max_budget - stage2_reserve
    
    max_files_affordable = int(available_for_stage1 / avg_tokens_per_file)
    
    return int(avg_tokens_per_file), max_files_affordable


def sampled_commit_message(
    chunks: List[str], 
    model: str, 
    temperature: float, 
    max_files: int
) -> str:
    """Generate commit message using a smart sampling of files."""
    
    # Sort chunks by size (larger files are usually more important)
    chunk_sizes = [(i, len(chunk)) for i, chunk in enumerate(chunks)]
    chunk_sizes.sort(key=lambda x: x[1], reverse=True)
    
    # Take the largest files up to our budget limit
    selected_indices = [i for i, _ in chunk_sizes[:max_files]]
    selected_chunks = [chunks[i] for i in selected_indices]
    
    print(f"  → Selected {len(selected_chunks)} largest files for analysis")
    
    # Generate summaries for selected files
    bullets: List[str] = []
    
    def summarize_chunk(chunk: str) -> str:
        return summarise_file_diff(chunk, model, temperature)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for bullet in pool.map(summarize_chunk, selected_chunks):
            bullets.append(bullet)
    
    # Add a summary bullet for the remaining files
    remaining_count = len(chunks) - len(selected_chunks)
    if remaining_count > 0:
        bullets.append(f"- Update {remaining_count} additional files")
    
    # Stage 2: final commit message
    bullets_text = "\n".join(sorted(bullets))
    prompt = (
        PROMPT_HEADER
        + "\nBelow are per-file bullets (sampled from largest files). "
        "Write the final Conventional Commit message:\n\n"
        + bullets_text
    )

    est_prompt = token_len(prompt)
    est_completion = 192
    if not try_reserve_tokens(est_prompt + est_completion):
        raise RuntimeError(
            "Token budget exceeded while composing final commit message "
            "(>250 000 tokens used). Aborting."
        )

    content = invoke_llm(
        model_name=model,
        prompt=prompt,
        temperature=temperature,
        max_tokens=est_completion,
    )
    
    # Estimate actual token usage
    prompt_tokens, completion_tokens = get_token_usage(model, prompt, content)
    real_spent = prompt_tokens + completion_tokens
    if real_spent < est_prompt + est_completion:
        refund_tokens((est_prompt + est_completion) - real_spent)
    
    if content:
        commit_msg = content.strip()
        return commit_msg.strip("`").strip()
    else:
        return "chore: update files\n\nGeneral file updates and improvements"


def hierarchical_commit_message(
    full_diff: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
) -> str:
    """Stage-1 file bullets ➜ Stage-2 final Conventional Commit."""
    try:
        chunks = split_diff_by_file(full_diff)
        print(f"Summarising {len(chunks)} file diffs…")

        # Stage 1: parallel bullet generation (threadpool keeps it simple)
        bullets: List[str] = []
        
        def summarize_chunk(chunk: str) -> str:
            return summarise_file_diff(chunk, model, temperature)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            for bullet in pool.map(summarize_chunk, chunks):
                bullets.append(bullet)

        # Stage 2: final commit message
        bullets_text = "\n".join(sorted(bullets))  # crude grouping heuristic
        prompt = (
            PROMPT_HEADER
            + "\nBelow are per-file bullets. Write the final Conventional "
            "Commit message:\n\n"
            + bullets_text
        )

        est_prompt = token_len(prompt)
        est_completion = 192  # commit messages are tiny
        if not try_reserve_tokens(est_prompt + est_completion):
            raise RuntimeError(
                "Token budget exceeded while composing final commit message "
                "(>250 000 tokens used). Aborting."
            )

        content = invoke_llm(
            model_name=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=est_completion,
        )
        
        # Estimate actual token usage
        prompt_tokens, completion_tokens = get_token_usage(model, prompt, content)
        real_spent = prompt_tokens + completion_tokens
        if real_spent < est_prompt + est_completion:
            refund_tokens((est_prompt + est_completion) - real_spent)
        
        if content:
            commit_msg = content.strip()
            return commit_msg.strip("`").strip()
        else:
            return "chore: update files\n\nGeneral file updates and improvements"
    except Exception as e:
        print(f"  → Warning: Hierarchical approach failed: {e}")
        print("  → Falling back to traditional approach...")
        # Fallback to the old method with truncation
        MAX_CHARS = 400_000
        if len(full_diff) > MAX_CHARS:
            print(
                f"  → Truncating diff from {len(full_diff):,} to {MAX_CHARS:,} chars..."
            )
            full_diff = (
                full_diff[:MAX_CHARS] + "\n\n[... Diff truncated due to length ...]"
            )
        
        full_prompt = PROMPT_HEADER + "\n" + full_diff
        return generate_commit_message_with_retry(full_prompt, model, temperature)


def generate_commit_message_with_retry(
    full_prompt: str, model: str, temperature: float, max_retries: int = 3
) -> str:
    """Generate commit message with retry logic for network issues."""
    import time
    
    # Check network connectivity first (using OpenAI as a default check)
    print("Checking network connectivity...")
    if not check_network_connectivity():
        print("Warning: Cannot connect to API server. Network may be down.")
        print("Using fallback commit message.")
        return generate_fallback_commit_message()
    
    for attempt in range(max_retries):
        prompt_tokens: int = 0
        est_completion: int = 192
        try:
            print(
                f"Attempting to generate commit message "
                f"(attempt {attempt + 1}/{max_retries})..."
            )
            
            prompt_tokens = token_len(full_prompt)
            if not try_reserve_tokens(prompt_tokens + est_completion):
                return generate_fallback_commit_message()
            
            content = invoke_llm(
                model_name=model,
                prompt=full_prompt,
                temperature=temperature,
                max_tokens=est_completion,
            )
            
            # Estimate actual token usage
            actual_prompt_tokens, actual_completion_tokens = get_token_usage(
                model, full_prompt, content
            )
            real_spent = actual_prompt_tokens + actual_completion_tokens
            if real_spent < prompt_tokens + est_completion:
                refund_tokens((prompt_tokens + est_completion) - real_spent)
            
            if content:
                commit_msg = content.strip()
                
                # Remove markdown code block markers if present
                if commit_msg.startswith("```") and commit_msg.endswith("```"):
                    commit_msg = commit_msg[3:-3].strip()
                elif commit_msg.startswith("```"):
                    commit_msg = commit_msg[3:].strip()
                elif commit_msg.endswith("```"):
                    commit_msg = commit_msg[:-3].strip()
                
                print("Successfully generated commit message!")
                return commit_msg
            else:
                return generate_fallback_commit_message()
            
        except Exception as e:
            # Check if it's a connection/timeout error
            error_str = str(e).lower()
            is_network_error = "connection" in error_str or "timeout" in error_str
            
            refund_tokens(prompt_tokens + est_completion)  # refund on failure
            error_type = "Network error" if is_network_error else "Error"
            print(f"{error_type} on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("All retry attempts failed. Using fallback commit message.")
                return generate_fallback_commit_message()
    
    # This should never be reached, but just in case
    return generate_fallback_commit_message()


def smart_hierarchical_commit_message(
    full_diff: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
) -> str:
    """Smart hierarchical approach that handles large repositories efficiently."""
    try:
        chunks = split_diff_by_file(full_diff)
        print(f"Summarising {len(chunks)} file diffs…")
        
        # Estimate budget requirements
        avg_tokens_per_file, max_files_affordable = estimate_stage1_budget(
            chunks, model, temperature
        )
        print(f"  → Estimated {avg_tokens_per_file:,} tokens per file")
        print(f"  → Can afford ~{max_files_affordable} files within budget")
        
        if len(chunks) > max_files_affordable:
            print(
                f"  → Too many files ({len(chunks)}) for hierarchical approach"
            )
            print("  → Using sampling strategy...")
            
            # Use sampling strategy for large repositories
            return sampled_commit_message(
                chunks, model, temperature, max_files_affordable
            )
        
        # Original hierarchical approach for manageable repositories
        return hierarchical_commit_message(full_diff, model, temperature)
        
    except Exception as e:
        print(f"  → Warning: Smart hierarchical approach failed: {e}")
        print("  → Falling back to traditional approach...")
        # Fallback to the old method with truncation
        MAX_CHARS = 400_000
        if len(full_diff) > MAX_CHARS:
            print(
                f"  → Truncating diff from {len(full_diff):,} to {MAX_CHARS:,} chars..."
            )
            full_diff = (
                full_diff[:MAX_CHARS] + "\n\n[... Diff truncated due to length ...]"
            )
        
        full_prompt = PROMPT_HEADER + "\n" + full_diff
        return generate_commit_message_with_retry(full_prompt, model, temperature)

