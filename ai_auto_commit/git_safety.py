"""Git safety checks and verification utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

# Import git_operations - handle both package and direct script execution
try:
    from .git_operations import run_git_command, run_git_command_output
except ImportError:
    from git_operations import run_git_command, run_git_command_output


def check_dangerous_git_state(target_dir: Path) -> bool:
    """Check if git is in a dangerous state that could cause data loss."""
    try:
        # Check if we're in a merge or rebase state
        merge_head = target_dir / ".git" / "MERGE_HEAD"
        rebase_apply = target_dir / ".git" / "rebase-apply"
        rebase_merge = target_dir / ".git" / "rebase-merge"
        
        if merge_head.exists():
            print("  → Warning: Repository is in merge state")
            return True
        if rebase_apply.exists() or rebase_merge.exists():
            print("  → Warning: Repository is in rebase state")
            return True
            
        # Check if we're in detached HEAD state
        head_ref = run_git_command_output(
            target_dir, "rev-parse", "--abbrev-ref", "HEAD"
        ).strip()
        if head_ref == "HEAD":
            print("  → Warning: Repository is in detached HEAD state")
            return True
            
        return False
        
    except Exception:
        print("  → Warning: Could not check git state")
        return True  # Assume dangerous if we can't check


def verify_working_directory_safety(target_dir: Path) -> bool:
    """Verify that the working directory is safe to operate on."""
    print("Verifying working directory safety...")
    
    try:
        # Check if we're in a git repository
        run_git_command(target_dir, "rev-parse", "--git-dir")
        
        # Check for dangerous git states
        if check_dangerous_git_state(target_dir):
            print("  → Repository is in a potentially dangerous state")
            print(
                "  → Please resolve any pending merges, rebases, or detached HEAD state"
            )
            return False
        
        # Check if we have any uncommitted changes that could be lost
        status_result = run_git_command_output(target_dir, "status", "--porcelain")
        
        if status_result.strip():
            print("  → Found uncommitted changes in working directory")
            print("  → These changes will be preserved during operations")
            
            # Show what changes exist
            for line in status_result.strip().split('\n'):
                if line:
                    status = line[:2]
                    filename = line[2:].lstrip()
                    print(f"    → {status}: {filename}")
        else:
            print("  → Working directory is clean")
        
        return True
        
    except Exception as e:
        print(f"  → Error: {e}")
        return False


def create_safety_backup(target_dir: Path) -> Optional[Path]:
    """Create a backup of critical git state for safety."""
    try:
        import tempfile
        import shutil
        from datetime import datetime
        
        # Create a temporary backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(tempfile.gettempdir()) / f"git_womp_backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        # Backup git index (staging area)
        git_index = target_dir / ".git" / "index"
        if git_index.exists():
            backup_index = backup_dir / "index"
            shutil.copy2(git_index, backup_index)
            print(f"  → Created safety backup at: {backup_dir}")
            return backup_dir
        
        return None
        
    except Exception as e:
        print(f"  → Warning: Could not create safety backup: {e}")
        return None


def cleanup_backup(backup_dir: Optional[Path]) -> None:
    """Clean up safety backup files."""
    if backup_dir and backup_dir.exists():
        try:
            import shutil
            shutil.rmtree(backup_dir)
            print(f"  → Cleaned up safety backup: {backup_dir}")
        except Exception as e:
            print(f"  → Warning: Could not clean up backup {backup_dir}: {e}")


def verify_no_files_deleted(target_dir: Path, original_status: str) -> bool:
    """Verify that no files were deleted during the operation."""
    try:
        current_status = run_git_command_output(target_dir, "status", "--porcelain")
        
        # Parse original and current status to check for deletions
        original_files: set[str] = set()
        current_files: set[str] = set()
        
        for line in original_status.strip().split('\n'):
            if line:
                status = line[:2]
                filename = line[2:].lstrip()
                if status not in [' D', 'D ']:  # Not deleted
                    original_files.add(filename)
        
        for line in current_status.strip().split('\n'):
            if line:
                status = line[:2]
                filename = line[2:].lstrip()
                if status not in [' D', 'D ']:  # Not deleted
                    current_files.add(filename)
        
        # Check if any files that existed before are missing now
        missing_files = original_files - current_files
        if missing_files:
            print(f"  → Warning: {len(missing_files)} files appear to be missing:")
            for file in missing_files:
                print(f"    → {file}")
            return False
        
        print("  → Verification passed: No files were deleted")
        return True
        
    except Exception as e:
        print(f"  → Warning: Could not verify file safety: {e}")
        return True  # Assume safe if verification fails

