#!/usr/bin/env python3

"""Main orchestrator for AI-powered git commit and push."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

# Import modules - handle both package and direct script execution
try:
    # Try relative imports first (when used as a package)
    from .api_client import ensure_initialized, init
    from .cli import prompt_for_commit_comment
    from .commit_generation import smart_hierarchical_commit_message
    from .git_operations import (
        clear_git_cache,
        get_target_directory,
        has_changes,
        has_unpushed_commits,
        run_git_command,
        run_git_command_output,
        show_changes_summary,
    )
    from .git_safety import (
        cleanup_backup,
        create_safety_backup,
        verify_no_files_deleted,
        verify_working_directory_safety,
    )
    from .heuristic_commits import (
        build_heuristic_bullets,
        compose_commit_from_bullets,
        parse_name_status,
        parse_numstat,
    )
    from .token_budget import get_max_token_budget, get_tokens_spent, reset_token_budget
    from .token_utils import token_len
    from .models import get_default_model
except ImportError:
    # Fall back to absolute imports (when running as a script)
    from api_client import ensure_initialized, init
    from cli import prompt_for_commit_comment
    from commit_generation import smart_hierarchical_commit_message
    from git_operations import (
        clear_git_cache,
        get_target_directory,
        has_changes,
        has_unpushed_commits,
        run_git_command,
        run_git_command_output,
        show_changes_summary,
    )
    from git_safety import (
        cleanup_backup,
        create_safety_backup,
        verify_no_files_deleted,
        verify_working_directory_safety,
    )
    from heuristic_commits import (
        build_heuristic_bullets,
        compose_commit_from_bullets,
        parse_name_status,
        parse_numstat,
    )
    from token_budget import get_max_token_budget, get_tokens_spent, reset_token_budget
    from token_utils import token_len
    from models import get_default_model


def auto_commit_and_push(
    *,
    model: Optional[str] = None,
    temperature: float = 0.2,
    remote: str = "origin",
) -> str:
    """
    Generate a commit message from already staged files, commit, and push.

    Note: Files must be staged first using `git add`. This function will
    use the files that are already in the staging area.

    Parameters
    ----------
    model : str, optional
        Chat model name to use. If None, uses the default model.
    temperature : float
        Sampling temperature for the completion.
    remote : str
        Git remote to push to (default 'origin').

    Returns
    -------
    str
        The commit message used.

    Raises
    ------
    RuntimeError
        If the API key is not initialized, or no files are staged.
    subprocess.CalledProcessError
        Propagates if any git command fails.
    """

    # ── Get the target directory ───────────────────────────────────────
    target_dir = get_target_directory()
    print(f"Operating on repository: {target_dir}")
    
    # ── Use default model (no prompting) ───────────────────────────────
    if model is None:
        model = get_default_model()

    # ── Safety verification ─────────────────────────────────────────────
    if not verify_working_directory_safety(target_dir):
        raise RuntimeError("Working directory safety verification failed")

    # ── Check if there are any changes to commit or unpushed commits ─────
    print("Checking repository status...")
    
    has_local_changes = has_changes(target_dir)
    has_unpushed_commits_var = has_unpushed_commits(target_dir, remote)
    
    if not has_local_changes and not has_unpushed_commits_var:
        print("Repository is clean and up to date. Nothing to commit or push.")
        return "Repository up to date - no changes needed"
    
    if has_unpushed_commits_var and not has_local_changes:
        print("Found unpushed commits. Proceeding to push...")
        # Skip the commit generation and staging, just push
        branch = run_git_command_output(
            target_dir, "rev-parse", "--abbrev-ref", "HEAD"
        ).strip()
        run_git_command(target_dir, "push", remote, branch)
        return "Pushed existing commits"

    # ── Show changes summary ─────────────────────────────────────────────
    show_changes_summary(target_dir)

    # ── Store original status for safety verification ────────────────────
    original_status = run_git_command_output(target_dir, "status", "--porcelain")

    # ── Ensure API key is initialized ─────────────────────────────────────
    ensure_initialized()
    
    # ── Reset token budget for this run ─────────────────────────────────────
    reset_token_budget()
    
    # ── Create safety backup ─────────────────────────────────────────────
    backup_dir = create_safety_backup(target_dir)
    
    # ── 1. Check for already staged files ───────────────────────────────
    # Get staged files from git status (files with first char indicating staged status)
    result = run_git_command_output(target_dir, "status", "--porcelain")
    staged_files: List[str] = []
    
    print("\nChecking for staged files...")
    
    for line in result.strip().split("\n"):
        if not line:
            continue
            
        status = line[:2]
        filename = line[2:].lstrip()  # Skip the 2-char status and any leading spaces
        
        # First char indicates staging area status:
        # A = Added, M = Modified, D = Deleted, R = Renamed, C = Copied
        # Space means not staged
        if status[0] in ['A', 'M', 'D', 'R', 'C']:
            staged_files.append(filename)
            print(f"  → Found staged file: {filename} ({status[0]})")
    
    if not staged_files:
        raise RuntimeError(
            "No staged files found. Please stage files first using:\n"
            "  git add <files>    # Stage specific files\n"
            "  git add .          # Stage all files in current directory\n"
            "Then run this tool again."
        )

    print(f"\nFound {len(staged_files)} staged file(s):")
    for file in staged_files:
        print(f"  - {file}")

    # ── 2. Get staged diff with optimizations ─────────────────────────────
    # Use optimized diff command: minimal context, exclude lock files, no binary diffs
    diff_args = [
        "diff", "--cached", "-U0",  # Minimal context lines
        "--",  # End of options
        ".",  # Current directory
    ]
    
    try:
        diff = run_git_command_output(target_dir, *diff_args).strip()
    except subprocess.CalledProcessError:
        # Fallback to basic diff if optimized version fails
        print("  → Optimized diff failed, using basic diff...")
        diff = run_git_command_output(target_dir, "diff", "--cached").strip()
    
    # Filter out binary files and lock files from the diff
    if diff:
        lines = diff.split('\n')
        filtered_lines: List[str] = []
        skip_file = False
        
        for line in lines:
            if line.startswith('diff --git'):
                # Check if this is a file we want to skip
                file_path = line.split()[-1] if len(line.split()) > 2 else ""
                skip_file = any(skip_pattern in file_path for skip_pattern in [
                    'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 
                    'Cargo.lock', 'composer.lock', '.png', '.jpg', '.jpeg', 
                    '.gif', '.ico', '.pdf'
                ])
                if not skip_file:
                    filtered_lines.append(line)
            elif not skip_file:
                filtered_lines.append(line)
        
        diff = '\n'.join(filtered_lines)
    
    if not diff:
        raise RuntimeError("No staged changes to commit.")

    print(f"Diff size: {len(diff):,} characters ({token_len(diff):,} tokens)")

    # ── 3. Prefer token-light heuristic bullets → single small LLM call ─────
    try:
        name_status_out = run_git_command_output(
            target_dir, "diff", "--cached", "--name-status"
        )
        numstat_out = run_git_command_output(
            target_dir, "diff", "--cached", "--numstat"
        )
        file_status = parse_name_status(name_status_out)
        file_stats = parse_numstat(numstat_out)
        bullets = build_heuristic_bullets(file_status, file_stats)
    except subprocess.CalledProcessError:
        bullets = []

    if bullets:
        print("Composing commit from summarized staged changes (no raw diffs)...")
        commit_msg = compose_commit_from_bullets(
            bullets, model=model, temperature=temperature
        )
    else:
        # Fallback: use hierarchical diff-based approach if bullets couldn't be built
        print("Using smart hierarchical commit message generation...")
        commit_msg = smart_hierarchical_commit_message(
            diff, model=model, temperature=temperature
        )
    
    # Show final token usage
    from .token_budget import get_max_token_budget
    print(f"Final token usage: {get_tokens_spent():,}/{get_max_token_budget():,} tokens")

    # ── 4. Ask for user comment on commit message ───────────────────────
    final_commit_msg = prompt_for_commit_comment(commit_msg)

    # ── 5. Commit ───────────────────────────────────────────────────────
    run_git_command(target_dir, "commit", "-m", final_commit_msg)

    # ── 6. Push ─────────────────────────────────────────────────────────
    # Determine current branch (detached HEAD will just push HEAD)
    branch = run_git_command_output(
        target_dir, "rev-parse", "--abbrev-ref", "HEAD"
    ).strip()
    run_git_command(target_dir, "push", remote, branch)

    # ── 7. Final safety verification ─────────────────────────────────────
    print("\nPerforming final safety verification...")
    if not verify_no_files_deleted(target_dir, original_status):
        print(
            "  → Warning: Some files may have been affected. "
            "Check your working directory."
        )
    
    # ── 8. Cleanup ─────────────────────────────────────────────────────
    cleanup_backup(backup_dir)

    return final_commit_msg


def main() -> None:
    """Main CLI entry point."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="AI-powered git commit and push tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Generate commit from staged files
  %(prog)s --model gpt-4o           # Use GPT-4o model (instead of default)
  %(prog)s --set-default-model gpt-4o  # Set default model for future runs

Note: Files must be staged first using 'git add <files>' or 'git add .' before running this tool.
        """
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key for the selected provider (if not provided, uses environment variables)"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key for the selected provider (if not provided, uses environment variables)"
    )
    
    parser.add_argument(
        "--provider",
        type=str,
        default="openai",
        choices=["openai", "anthropic", "google", "mistral", "cohere"],
        help="AI provider to use (default: openai)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model to use (e.g., gpt-4o-mini, claude-3-5-sonnet-20241022). "
             "Default: uses configured default model"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for the completion (default: %(default)s)"
    )
    
    parser.add_argument(
        "--remote",
        type=str,
        default="origin",
        help="Git remote to push to (default: %(default)s)"
    )
    
    parser.add_argument(
        "--set-default-model",
        type=str,
        default=None,
        metavar="MODEL",
        help="Set the default model to use and exit. Example: --set-default-model gpt-4o"
    )
    
    args = parser.parse_args()
    
    # Handle --set-default-model flag (exit early if set)
    if args.set_default_model:
        try:
            from .models import set_default_model, get_model_config
        except ImportError:
            from models import set_default_model, get_model_config
        
        model_name = args.set_default_model
        # Validate model if it's a known model
        config = get_model_config(model_name)
        if config:
            print(f"✅ Setting default model to: {config.display_name} ({model_name})")
        else:
            print(f"✅ Setting default model to: {model_name} (custom model)")
        
        set_default_model(model_name)
        print(f"Default model saved. It will be used when no --model is specified.")
        return
    
    try:
        print("🚀 AI Auto Commit Tool")
        print("=" * 60)
        
        # Initialize API key
        if args.api_key:
            init(api_key=args.api_key, provider=args.provider)
        else:
            # Try to initialize from environment
            try:
                init(provider=args.provider)
            except RuntimeError as e:
                print(f"\n❌ Error: {e}")
                sys.exit(1)
        
        commit_msg = auto_commit_and_push(
            model=args.model,
            temperature=args.temperature,
            remote=args.remote,
        )
        
        print("\n" + "=" * 60)
        print("✅ Success!")
        print("=" * 60)
        print(f"Commit message:\n{commit_msg}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
