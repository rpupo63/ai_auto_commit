"""Git operations and command wrappers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def get_target_directory() -> Path:
    """Get the git repository root directory from the current working directory."""
    # Start from the current working directory
    current_dir = Path.cwd().resolve()
    
    # Walk up the directory tree to find the .git directory
    for path in [current_dir] + list(current_dir.parents):
        git_dir = path / ".git"
        if git_dir.exists() and (git_dir.is_dir() or git_dir.is_file()):
            return path
    
    # If we didn't find a git repository, raise an error
    raise RuntimeError(
        f"Not in a git repository. Current directory: {current_dir}\n"
        "Please run this command from within a git repository."
    )


def run_git_command(target_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command in the target directory."""
    return subprocess.run(
        ["git", "-C", str(target_dir)] + list(args),
        check=True,
        capture_output=True,
        text=True
    )


def run_git_command_output(target_dir: Path, *args: str) -> str:
    """Run a git command in the target directory and return the output."""
    result = subprocess.run(
        ["git", "-C", str(target_dir)] + list(args),
        check=True,
        capture_output=True,
        text=True
    )
    return result.stdout


def show_changes_summary(target_dir: Path) -> None:
    """Show a summary of all changes in the repository."""
    print("Repository changes summary:")
    print("=" * 50)
    
    # Show detailed status
    result = run_git_command_output(target_dir, "status")
    print(result)
    print("=" * 50)


def has_changes(target_dir: Path) -> bool:
    """Check if there are any changes in the repository."""
    try:
        result = run_git_command_output(target_dir, "status", "--porcelain")
        return bool(result.strip())
    except subprocess.CalledProcessError:
        return False


def has_unpushed_commits(target_dir: Path, remote: str = "origin") -> bool:
    """Check if there are any unpushed commits in the repository."""
    try:
        # Get current branch
        current_branch = run_git_command_output(
            target_dir, "rev-parse", "--abbrev-ref", "HEAD"
        ).strip()
        
        # Check if local branch is ahead of remote
        ahead_count = run_git_command_output(
            target_dir, "rev-list", "--count", f"{remote}/{current_branch}..HEAD"
        ).strip()
        
        return ahead_count != "0"
        
    except subprocess.CalledProcessError:
        # If there's an error (e.g., no remote tracking branch), assume no unpushed commits
        return False


def clear_git_cache(target_dir: Path) -> None:
    """Clear the git staging area and untrack files that are now in .gitignore."""
    print("Clearing git staging area and untracking ignored files...")
    
    try:
        # Remove all files from the index (staging area) without affecting working directory
        # Using --mixed to ensure working directory is preserved
        run_git_command(target_dir, "reset", "--mixed")
        print("  → Cleared staging area (files remain unchanged)")
        
        # Remove files from git index that are now in .gitignore (but keep them locally)
        # This will untrack files that were previously tracked but are now ignored
        try:
            # Get list of files that are tracked but would be ignored
            result = run_git_command_output(
                target_dir, "ls-files", "--ignored", "--exclude-standard"
            )
            ignored_tracked_files = result.strip().split('\n') if result.strip() else []
            
            if ignored_tracked_files:
                print(
                    f"  → Found {len(ignored_tracked_files)} tracked files "
                    "that are now in .gitignore"
                )
                print("  → These files will be untracked but kept locally:")
                
                for file_path in ignored_tracked_files:
                    if file_path:  # Skip empty lines
                        # Verify the file exists locally before untracking
                        local_file_path = target_dir / file_path
                        if local_file_path.exists():
                            try:
                                run_git_command(target_dir, "rm", "--cached", file_path)
                                print(f"    → Untracked (kept locally): {file_path}")
                            except subprocess.CalledProcessError:
                                # File might have been removed already or doesn't exist
                                print(f"    → Warning: Could not untrack {file_path}")
                        else:
                            print(
                                f"    → Warning: File {file_path} not found locally, skipping"
                            )
                
                print("  → Successfully untracked files that are now in .gitignore")
            else:
                print("  → No tracked files to untrack")
                
        except subprocess.CalledProcessError:
            # If ls-files fails, it might be because there are no files to check
            print("  → No files to check for untracking")
            
    except subprocess.CalledProcessError as e:
        print(f"  → Warning: Could not clear staging area: {e}")
        # Continue anyway, as this is not critical

