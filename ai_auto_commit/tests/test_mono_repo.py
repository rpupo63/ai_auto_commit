import subprocess
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_auto_commit.cli import main

@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
def test_appflowy_mono_repo(monkeypatch):
    """
    Test that auto_commit can handle a large mono-repo like AppFlowy.
    """
    # Mock push_with_recovery to prevent actual pushes
    def mock_push_with_recovery(*args, **kwargs):
        pass
    monkeypatch.setattr("ai_auto_commit.git_operations.push_with_recovery", mock_push_with_recovery)

    # Mock run_git_command to prevent actual git commands
    def mock_run_git_command(cwd, *cmd, **kwargs):
        if cmd == ("rev-parse", "--git-dir"):
            # Simulate a successful git command for checking if it's a git repo
            # It doesn't need to return anything, just not raise an error
            return subprocess.CompletedProcess(args=cmd, returncode=0)
        pass
    monkeypatch.setattr("ai_auto_commit.git_operations.run_git_command", mock_run_git_command)

    # Mock get_target_directory to return the repo_path
    def mock_get_target_directory():
        return Path(repo_path)
    monkeypatch.setattr("ai_auto_commit.git_operations.get_target_directory", mock_get_target_directory)

    # Mock check_dangerous_git_state to always return False
    def mock_check_dangerous_git_state(*args, **kwargs):
        return False
    monkeypatch.setattr("ai_auto_commit.git_safety.check_dangerous_git_state", mock_check_dangerous_git_state)

    # Mock verify_working_directory_safety to always return True
    def mock_verify_working_directory_safety(*args, **kwargs):
        return True
    monkeypatch.setattr("ai_auto_commit.git_safety.verify_working_directory_safety", mock_verify_working_directory_safety)
    monkeypatch.setattr("git_safety.verify_working_directory_safety", mock_verify_working_directory_safety)
    monkeypatch.setattr("ai_auto_commit.ai_auto_commit.verify_working_directory_safety", mock_verify_working_directory_safety)

    # Mock run_git_command_output to prevent actual git commands and return empty string
    def mock_run_git_command_output(cwd, *cmd, **kwargs):
        if cmd == ("status", "--porcelain"):
            return "A  new_file.txt"
        if cmd == ("diff", "--cached", "-U0", "--", ".") or cmd == ("diff", "--cached"):
            return "diff --git a/new_file.txt b/new_file.txt\nindex 0000000..8d2777f 100644\n--- a/new_file.txt\n+++ b/new_file.txt\n@@ -0,0 +1 @@\n++This is a new file."
        if cmd == ("rev-parse", "--abbrev-ref", "HEAD"): # for branch name in push
            return "main"
        return ""
    monkeypatch.setattr("ai_auto_commit.git_operations.run_git_command_output", mock_run_git_command_output)

    _original_subprocess_run = subprocess.run
    # Mock subprocess.run to prevent actual git add and git clone
    def mock_subprocess_run(*args, **kwargs):
        if args[0][0] == "git" and (args[0][1] == "add" or args[0][1] == "clone"):
            return
        # Call the original subprocess.run for other commands if needed
        return _original_subprocess_run(*args, **kwargs)
    monkeypatch.setattr("subprocess.run", mock_subprocess_run)
    
    repo_path = "tests/faradhaven"
    repo_url = "https://github.com/rpupo63/faradhaven"

    if not os.path.exists(repo_path):
        # Simulate git clone
        mock_subprocess_run(["git", "clone", repo_url, repo_path], check=True)
    
    # Simulate some changes in the repo
    with open(os.path.join(repo_path, "new_file.txt"), "w") as f:
        f.write("This is a new file.")
    
    
    
    # Run the auto_commit tool
    sys.argv = ["autocommit", "--model", "gemini-3-flash-preview", "--non-interactive"]
    # We need to change the current directory to the repo path
    # because the tool runs in the current directory.
    os.chdir(repo_path)
    try:
        main()
    except SystemExit as e:
        assert e.code == 0
    finally:
        os.chdir("../..")
