"""Heuristic-based commit message generation (token-light approach)."""

from __future__ import annotations

# Import modules - handle both package and direct script execution
try:
    from .llm_client import get_token_usage, invoke_llm
    from .prompts import PROMPT_HEADER
    from .token_budget import refund_tokens, try_reserve_tokens
    from .token_utils import token_len
except ImportError:
    from llm_client import get_token_usage, invoke_llm
    from prompts import PROMPT_HEADER
    from token_budget import refund_tokens, try_reserve_tokens
    from token_utils import token_len


def parse_name_status(output: str) -> dict[str, str]:
    """Parse `git diff --cached --name-status` into {path: status}.
    Status values: 'A', 'M', 'D', 'R', 'C', etc.
    """
    mapping: dict[str, str] = {}
    for line in output.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split('\t')
        if not parts:
            continue
        status = parts[0].strip()
        # Handle renames which look like: R100\told\tnew
        if status.startswith('R') or status.startswith('C'):
            if len(parts) >= 3:
                new_path = parts[2].strip()
                mapping[new_path] = status[0]
        else:
            if len(parts) >= 2:
                path = parts[1].strip()
                mapping[path] = status[0]
    return mapping


def parse_numstat(output: str) -> dict[str, tuple[int, int]]:
    """Parse `git diff --cached --numstat` into {path: (added, deleted)}."""
    stats: dict[str, tuple[int, int]] = {}
    for line in output.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) >= 3:
            added_str, deleted_str, path = parts[0], parts[1], parts[2]
            try:
                added = int(added_str) if added_str.isdigit() else 0
                deleted = int(deleted_str) if deleted_str.isdigit() else 0
            except ValueError:
                added, deleted = 0, 0
            stats[path] = (added, deleted)
    return stats


def categorize_path(path: str) -> str:
    """Rough category for Conventional Commit scope/type heuristics."""
    p = path.lower()
    if "test" in p or p.endswith("_test.go") or "/tests/" in p:
        return "test"
    if any(seg in p for seg in ["readme", "docs/", "/doc/", ".md"]):
        return "docs"
    if any(p.endswith(ext) for ext in [
        ".lock", "bun.lockb", "yarn.lock", "pnpm-lock.yaml", "package-lock.json"
    ]):
        return "chore"
    if any(seg in p for seg in ["config/", "/config", ".toml", ".yaml", ".yml", ".json"]):
        return "chore"
    return "code"


def build_heuristic_bullets(
    file_status: dict[str, str], file_stats: dict[str, tuple[int, int]]
) -> list[str]:
    """Create short, informative bullets without sending diffs to the model."""
    bullets: list[str] = []
    for path, status in file_status.items():
        added, deleted = file_stats.get(path, (0, 0))
        category = categorize_path(path)
        scope = path.split('/', 1)[0] if '/' in path else path
        # Choose a verb based on status
        if status == 'A':
            verb = "Add"
        elif status == 'D':
            verb = "Remove"
        elif status == 'R':
            verb = "Rename"
        elif status == 'C':
            verb = "Copy"
        else:
            verb = "Update"
        # Short file label for readability
        short_name = path.split('/')[-1]
        size_note = f"(+{added} -{deleted})" if (added or deleted) else ""
        if category == "test":
            bullets.append(
                f"- {verb} tests in {scope}: {short_name} {size_note}".strip()
            )
        elif category == "docs":
            bullets.append(
                f"- {verb} docs in {scope}: {short_name} {size_note}".strip()
            )
        elif category == "chore":
            bullets.append(
                f"- {verb} tooling/config in {scope}: {short_name} {size_note}".strip()
            )
        else:
            bullets.append(
                f"- {verb} code in {scope}: {short_name} {size_note}".strip()
            )
    # De-duplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for b in bullets:
        if b not in seen:
            seen.add(b)
            deduped.append(b)
    return deduped


def compose_commit_from_bullets(
    bullets: list[str], model: str, temperature: float
) -> str:
    """Compose the final Conventional Commit from bullets with a single small call."""
    bullets_text = "\n".join(bullets[:200])  # hard cap
    prompt = (
        PROMPT_HEADER
        + "\nBelow are summarized staged changes (no raw diffs). "
        "Write the final Conventional Commit message:\n\n"
        + bullets_text
    )

    est_prompt = token_len(prompt)
    est_completion = 192
    if not try_reserve_tokens(est_prompt + est_completion):
        # If we cannot afford even this, return a local deterministic message
        return compose_commit_from_bullets_local(bullets)

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
    return compose_commit_from_bullets_local(bullets)


def compose_commit_from_bullets_local(bullets: list[str]) -> str:
    """Deterministic Conventional Commit if the API is unavailable/budgeted out."""
    # Decide type by majority category hints in bullets
    counts = {"test": 0, "docs": 0, "chore": 0, "code": 0}
    for b in bullets:
        if "tests" in b:
            counts["test"] += 1
        elif "docs" in b:
            counts["docs"] += 1
        elif "tooling/config" in b:
            counts["chore"] += 1
        else:
            counts["code"] += 1
    # Use lambda to avoid Optional[int] from dict.get typing
    commit_type = max(counts.keys(), key=lambda k: counts[k])
    type_map = {"code": "chore", "chore": "chore", "docs": "docs", "test": "test"}
    cc_type = type_map.get(commit_type, "chore")
    title = {
        "test": "update tests",
        "docs": "update docs",
        "chore": "maintenance updates",
        "code": "update code",
    }[commit_type]
    body_lines = bullets[:10]
    if len(bullets) > 10:
        body_lines.append(f"- and {len(bullets) - 10} more changes")
    body = "\n".join(body_lines)
    return f"{cc_type}: {title}\n\nSummary of changes\n{body}"

