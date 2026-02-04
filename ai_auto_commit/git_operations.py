"""Git operations and command wrappers."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional, Tuple


class GitPushError(Exception):
    """Exception raised when git push fails with diagnostic information."""
    
    def __init__(
        self,
        message: str,
        cause: str,
        suggestion: str,
        recoverable: bool = False,
        recovery_action: Optional[str] = None,
    ):
        super().__init__(message)
        self.cause = cause
        self.suggestion = suggestion
        self.recoverable = recoverable
        self.recovery_action = recovery_action


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


def diagnose_push_failure(
    target_dir: Path,
    remote: str,
    branch: str,
    stderr: str,
    stdout: str,
) -> GitPushError:
    """
    Diagnose why a git push failed and return a descriptive error.
    
    Parameters
    ----------
    target_dir : Path
        The git repository directory.
    remote : str
        The remote name (e.g., 'origin').
    branch : str
        The branch being pushed.
    stderr : str
        The stderr output from the failed push.
    stdout : str
        The stdout output from the failed push.
    
    Returns
    -------
    GitPushError
        A descriptive error with cause, suggestion, and recovery options.
    """
    combined_output = f"{stdout}\n{stderr}".lower()
    
    # Non-fast-forward (remote has commits we don't have)
    if "non-fast-forward" in combined_output or "fetch first" in combined_output:
        return GitPushError(
            message=f"Push rejected: remote '{remote}/{branch}' has commits that are not in your local branch.",
            cause="The remote branch has new commits that you don't have locally. This typically happens when someone else pushed changes, or you pushed from another machine.",
            suggestion="You can either:\n"
                       "  1. Rebase your changes on top of the remote (recommended for clean history)\n"
                       "  2. Merge the remote changes into your local branch\n"
                       "  3. Force push (WARNING: this will overwrite remote changes!)",
            recoverable=True,
            recovery_action="pull_rebase",
        )
    
    # No upstream branch set
    if "no upstream branch" in combined_output or "set-upstream" in combined_output:
        return GitPushError(
            message=f"Push failed: no upstream branch configured for '{branch}'.",
            cause="Your local branch doesn't have a tracking relationship with a remote branch.",
            suggestion=f"Run: git push --set-upstream {remote} {branch}",
            recoverable=True,
            recovery_action="set_upstream",
        )
    
    # Authentication failure
    if any(x in combined_output for x in ["authentication", "permission denied", "could not read from remote", "fatal: could not read username"]):
        return GitPushError(
            message="Push failed: authentication error.",
            cause="Git couldn't authenticate with the remote repository. This could be due to invalid credentials, expired tokens, or missing SSH keys.",
            suggestion="Try the following:\n"
                       "  1. Check your credentials: git config --global credential.helper\n"
                       "  2. For HTTPS: ensure your personal access token is valid\n"
                       "  3. For SSH: ensure your SSH key is added (ssh-add -l)\n"
                       "  4. Try: git remote -v to verify the remote URL",
            recoverable=False,
        )
    
    # Protected branch
    if "protected branch" in combined_output:
        return GitPushError(
            message=f"Push failed: '{branch}' is a protected branch.",
            cause="The branch has protection rules that prevent direct pushes.",
            suggestion="You need to:\n"
                       "  1. Create a pull/merge request instead of pushing directly\n"
                       "  2. Or ask an admin to temporarily disable branch protection",
            recoverable=False,
        )
    
    # Repository not found
    if "repository not found" in combined_output:
        return GitPushError(
            message=f"Push failed: remote repository '{remote}' not found.",
            cause="The remote repository doesn't exist or you don't have access to it.",
            suggestion="Check:\n"
                       f"  1. Verify remote URL: git remote get-url {remote}\n"
                       "  2. Ensure the repository exists on the remote\n"
                       "  3. Verify you have access to the repository",
            recoverable=False,
        )
    
    # Remote rejected (generic)
    if "remote rejected" in combined_output or "pre-receive hook declined" in combined_output:
        return GitPushError(
            message="Push rejected by remote server.",
            cause="The remote server rejected the push. This could be due to pre-receive hooks, CI checks, or policy violations.",
            suggestion="Check the error message above for specific requirements.\n"
                       "Common causes: commit message format, file size limits, or CI validation.",
            recoverable=False,
        )
    
    # Network/connection issues
    if any(x in combined_output for x in ["connection refused", "network", "timeout", "could not resolve host"]):
        return GitPushError(
            message="Push failed: network error.",
            cause="Could not connect to the remote server.",
            suggestion="Check:\n"
                       "  1. Your internet connection\n"
                       "  2. VPN if required for your repository\n"
                       "  3. Remote server status",
            recoverable=True,
            recovery_action="retry",
        )
    
    # Generic fallback
    return GitPushError(
        message="Push failed with an unexpected error.",
        cause=f"Git returned an error:\n{stderr or stdout}",
        suggestion="Review the error message above and check:\n"
                   "  1. git status - for any uncommitted changes\n"
                   "  2. git remote -v - to verify remote configuration\n"
                   "  3. git log --oneline -5 - to review recent commits",
        recoverable=False,
    )


def attempt_push_recovery(
    target_dir: Path,
    remote: str,
    branch: str,
    recovery_action: str,
    auto_recover: bool = False,
) -> Tuple[bool, str]:
    """
    Attempt to recover from a push failure.
    
    Parameters
    ----------
    target_dir : Path
        The git repository directory.
    remote : str
        The remote name.
    branch : str
        The branch being pushed.
    recovery_action : str
        The recovery action to attempt ('pull_rebase', 'set_upstream', 'retry').
    auto_recover : bool
        If True, perform recovery without prompting user.
    
    Returns
    -------
    Tuple[bool, str]
        (success, message) - whether recovery succeeded and a status message.
    """
    if recovery_action == "pull_rebase":
        if not auto_recover:
            print("\n🔄 Recovery Option: Pull with Rebase")
            print("=" * 50)
            print("This will:")
            print(f"  1. Fetch latest changes from {remote}/{branch}")
            print("  2. Rebase your commits on top of the remote changes")
            print("  3. Push the rebased commits")
            print("\nNote: If there are conflicts, you'll need to resolve them manually.")
            
            response = input("\nProceed with pull --rebase? (Y/n): ").strip().lower()
            if response not in ['y', 'yes', '']:
                return False, "Recovery cancelled by user."
        
        try:
            print(f"\n  → Fetching from {remote}...")
            run_git_command(target_dir, "fetch", remote)
            
            print(f"  → Rebasing onto {remote}/{branch}...")
            run_git_command(target_dir, "rebase", f"{remote}/{branch}")
            
            print(f"  → Pushing to {remote}/{branch}...")
            run_git_command(target_dir, "push", remote, branch)
            
            return True, "Successfully rebased and pushed!"
            
        except subprocess.CalledProcessError as e:
            # Check if rebase failed due to conflicts
            rebase_in_progress = (target_dir / ".git" / "rebase-merge").exists() or \
                                 (target_dir / ".git" / "rebase-apply").exists()
            
            if rebase_in_progress:
                return False, (
                    "Rebase encountered conflicts that need manual resolution.\n"
                    "To resolve:\n"
                    "  1. Fix the conflicts in the affected files\n"
                    "  2. Stage the resolved files: git add <files>\n"
                    "  3. Continue the rebase: git rebase --continue\n"
                    "  4. Push again: git push\n\n"
                    "To abort the rebase and return to the previous state:\n"
                    "  git rebase --abort"
                )
            
            return False, f"Recovery failed: {e.stderr if hasattr(e, 'stderr') else str(e)}"
    
    elif recovery_action == "set_upstream":
        if not auto_recover:
            print("\n🔄 Recovery Option: Set Upstream Branch")
            print("=" * 50)
            print(f"This will set up tracking between your local '{branch}' and '{remote}/{branch}'")
            
            response = input("\nProceed? (Y/n): ").strip().lower()
            if response not in ['y', 'yes', '']:
                return False, "Recovery cancelled by user."
        
        try:
            print(f"  → Pushing with --set-upstream...")
            run_git_command(target_dir, "push", "--set-upstream", remote, branch)
            return True, f"Successfully pushed and set upstream to {remote}/{branch}!"
            
        except subprocess.CalledProcessError as e:
            return False, f"Recovery failed: {e.stderr if hasattr(e, 'stderr') else str(e)}"
    
    elif recovery_action == "retry":
        if not auto_recover:
            print("\n🔄 Recovery Option: Retry Push")
            print("=" * 50)
            print("This will attempt to push again (useful for transient network issues).")
            
            response = input("\nRetry push? (Y/n): ").strip().lower()
            if response not in ['y', 'yes', '']:
                return False, "Recovery cancelled by user."
        
        try:
            print(f"  → Retrying push to {remote}/{branch}...")
            run_git_command(target_dir, "push", remote, branch)
            return True, "Push succeeded on retry!"
            
        except subprocess.CalledProcessError as e:
            return False, f"Retry failed: {e.stderr if hasattr(e, 'stderr') else str(e)}"
    
    return False, f"Unknown recovery action: {recovery_action}"


def push_with_recovery(
    target_dir: Path,
    remote: str,
    branch: str,
    auto_recover: bool = False,
    max_retries: int = 1,
) -> str:
    """
    Push to remote with automatic failure diagnosis and optional recovery.
    
    Parameters
    ----------
    target_dir : Path
        The git repository directory.
    remote : str
        The remote name (e.g., 'origin').
    branch : str
        The branch to push.
    auto_recover : bool
        If True, automatically attempt recovery for recoverable errors.
    max_retries : int
        Maximum number of recovery attempts.
    
    Returns
    -------
    str
        Success message.
    
    Raises
    ------
    GitPushError
        If push fails and recovery is not possible or was declined.
    """
    for attempt in range(max_retries + 1):
        try:
            result = subprocess.run(
                ["git", "-C", str(target_dir), "push", remote, branch],
                check=True,
                capture_output=True,
                text=True,
            )
            return f"Successfully pushed to {remote}/{branch}"
            
        except subprocess.CalledProcessError as e:
            error = diagnose_push_failure(
                target_dir, remote, branch,
                stderr=e.stderr or "",
                stdout=e.stdout or "",
            )
            
            print(f"\n❌ Push Failed")
            print("=" * 60)
            print(f"Cause: {error.cause}")
            print(f"\nSuggestion: {error.suggestion}")
            
            if error.recoverable and error.recovery_action and attempt < max_retries:
                print(f"\n💡 Automatic recovery is available!")
                
                success, message = attempt_push_recovery(
                    target_dir, remote, branch,
                    error.recovery_action,
                    auto_recover=auto_recover,
                )
                
                if success:
                    print(f"\n✅ {message}")
                    return message
                else:
                    print(f"\n⚠️  {message}")
                    # Continue to raise the error if recovery failed
            
            raise error

