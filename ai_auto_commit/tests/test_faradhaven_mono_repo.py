import subprocess
import os
import sys
import pytest
from pathlib import Path
import shutil # New import

# Add the project root to the sys.path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_auto_commit.cli import main
from ai_auto_commit import git_operations # Need this for mocking
from ai_auto_commit import git_safety # Need this for mocking

LOCAL_FARADHAVEN_REPO = "/home/beto/.gemini/tmp/9dbb847be477159afc41d3eb6f2f69f411b6c948206d75733a08fb3883e2eb03/faradhaven_local_copy"

@pytest.fixture
def faradhaven_repo(tmp_path):
    repo_path = tmp_path / "faradhaven"
    print(f"Copying local faradhaven repo from {LOCAL_FARADHAVEN_REPO} to {repo_path}")
    
    # Copy contents, ignoring the .git directory
    shutil.copytree(LOCAL_FARADHAVEN_REPO, repo_path, ignore=shutil.ignore_patterns(".git"))
    
    # Initialize a new git repository in the copied directory
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo_path, check=True) # Set default branch to main
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit from copied repo"], cwd=repo_path, check=True)
    return repo_path

@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
def test_faradhaven_mono_repo(monkeypatch, faradhaven_repo):
    """
    Test that auto_commit can handle the faradhaven mono-repo.
    It simulates adding a new file and expects auto_commit to generate a message.
    """
    # Store original functions to selectively unmock or call
    _original_run_git_command_output = git_operations.run_git_command_output
    _original_subprocess_run = subprocess.run

    # --- Mocks for git_operations and git_safety ---
    # Always report a safe git state
    monkeypatch.setattr(git_safety, "check_dangerous_git_state", lambda *args, **kwargs: False)
    monkeypatch.setattr(git_safety, "verify_working_directory_safety", lambda *args, **kwargs: True)

    # Ensure get_target_directory returns our temporary repo path
    def mock_get_target_directory():
        return faradhaven_repo
    monkeypatch.setattr(git_operations, "get_target_directory", mock_get_target_directory)

    # --- Mocks for specific git commands that return output ---
    committed_message = None # To capture the commit message if a commit happens
    def mock_run_git_command_output_with_commit_capture(cwd, *cmd, **kwargs):
        command_tuple = tuple(cmd)

        if command_tuple == ("status", "--porcelain"):
            return "A  new_file_faradhaven.txt" # Indicate a new file is added and staged
        elif command_tuple == ("diff", "--cached", "-U0", "--", "."):
            # Simulate a diff for the new staged file
            return "diff --git a/new_file_faradhaven.txt b/new_file_faradhaven.txt\n" \
                   "new file mode 100644\n" \
                   "index 0000000..e69de29\n" \
                   "--- /dev/null\n" \
                   "+++ b/new_file_faradhaven.txt\n" \
                   "@@ -0,0 +1,1 @@\n" \
                   "+This is a new file for faradhaven test."
        elif command_tuple == ("rev-parse", "--abbrev-ref", "HEAD"):
            return "main" # Assume main branch
        # This mock is only for commands that return output. 'git commit' doesn't return output,
        # so remove its capture logic from here.
        # if command_tuple[0] == "commit" and command_tuple[1] == "-m":
        #    committed_message = command_tuple[2] # Capture the commit message
        #    return "" # Return empty string for successful mock commit
        # For other commands, call the original if possible or return empty
        return _original_run_git_command_output(cwd, *cmd, **kwargs)

    monkeypatch.setattr(git_operations, "run_git_command_output", mock_run_git_command_output_with_commit_capture)

    # --- Mock subprocess.run to intercept git commit and git push ---
    def mock_subprocess_run(*args, **kwargs):
        nonlocal committed_message # Declare nonlocal to modify the outer variable
        command_list = args[0]
        
        # Mock 'git commit' to prevent actual commit while still allowing its call
        if "commit" in command_list and "-m" in command_list:
            commit_index = command_list.index("commit")
            m_index = command_list.index("-m", commit_index)
            if len(command_list) > m_index + 1:
                committed_message = command_list[m_index + 1] # Capture the commit message
            return subprocess.CompletedProcess(args=command_list, returncode=0, stdout="", stderr="")
        # Mock 'git push' to prevent actual push and return success
        if command_list[0] == "git" and "push" in command_list:
            return subprocess.CompletedProcess(args=command_list, returncode=0, stdout="Mock push successful", stderr="")
        
        # Allow other non-git commands or unmocked git commands to run
        return _original_subprocess_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    # --- Simulate changes in the cloned repo ---
    new_file_path = faradhaven_repo / "new_file_faradhaven.txt"
    with open(new_file_path, "w") as f:
        f.write("This is a new file for faradhaven test.")

    # Explicitly stage the new file
    subprocess.run(["git", "add", str(new_file_path)], cwd=faradhaven_repo, check=True)

    # --- Run the auto_commit tool ---
    original_cwd = os.getcwd()
    try:
        os.chdir(faradhaven_repo)
        # Set sys.argv to simulate command line arguments for the tool
        # Using a specific model for consistency, and --non-interactive
        sys.argv = ["autocommit", "--model", "gemini-3-flash-preview", "--non-interactive"]
        print(f"Running autocommit in {os.getcwd()}")
        main()
    except SystemExit as e:
        print(f"SystemExit code: {e.code}")
        assert e.code == 0
    finally:
        os.chdir(original_cwd)

    # --- Assertions ---
    # Verify that a commit message was captured, indicating the tool processed the changes
    assert committed_message is not None, "Auto-commit tool did not attempt to generate a commit message."
    assert isinstance(committed_message, str), "Captured commit message is not a string."
    assert len(committed_message) > 0, "Captured commit message is empty."
