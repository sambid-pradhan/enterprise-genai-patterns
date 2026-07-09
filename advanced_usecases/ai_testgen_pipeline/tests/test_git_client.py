from pathlib import Path

from app.command_runner import CommandResult
from app.git_client import GitClient
from app.models import RunCreateRequest


class FakeRunner:
    def __init__(self):
        self.commands = []

    def run(self, command, cwd=None, timeout_seconds=None):
        self.commands.append((list(command), cwd, timeout_seconds))
        if command[:2] == ["git", "remote"]:
            return CommandResult(list(command), str(cwd), 0, "origin\thttps://github.com/acme/repo.git (fetch)\n", "")
        return CommandResult(list(command), str(cwd) if cwd else None, 0, "", "")


def test_prepare_sample_repo_copies_files(tmp_path):
    sample_repo = tmp_path / "sample"
    sample_file = sample_repo / "src" / "sample_app" / "calculator.py"
    sample_file.parent.mkdir(parents=True)
    sample_file.write_text("def add(a, b): return a + b\n", encoding="utf-8")
    repos_dir = tmp_path / "repos"

    client = GitClient(FakeRunner(), "git", repos_dir, sample_repo, 30)
    repo_path = client.prepare_repo(
        "run-1",
        RunCreateRequest(repo_url="sample", target_paths=["src/sample_app/calculator.py"]),
    )

    assert (repo_path / "src" / "sample_app" / "calculator.py").exists()


def test_prepare_git_repo_uses_git_clone(tmp_path):
    runner = FakeRunner()
    client = GitClient(runner, "git", tmp_path / "repos", tmp_path / "sample", 30)

    client.prepare_repo(
        "run-2",
        RunCreateRequest(repo_url="https://github.com/acme/repo.git", target_paths=["src/app.py"]),
    )

    assert runner.commands[0][0] == [
        "git",
        "clone",
        "--branch",
        "main",
        "--single-branch",
        "https://github.com/acme/repo.git",
        str(tmp_path / "repos" / "run-2"),
    ]


def test_has_github_remote_detects_github_url(tmp_path):
    client = GitClient(FakeRunner(), "git", tmp_path / "repos", tmp_path / "sample", 30)

    assert client.has_github_remote(Path("repo")) is True


def test_create_branch_commit_push_uses_branch_name_override(tmp_path):
    class Runner:
        def __init__(self):
            self.commands = []

        def run(self, command, cwd=None, timeout_seconds=None):
            self.commands.append(command)
            return CommandResult(list(command), str(cwd), 0, "", "")

    runner = Runner()
    client = GitClient(runner, "git", tmp_path / "repos", tmp_path / "sample", 30)

    branch = client.create_branch_commit_push(
        tmp_path,
        "run-id",
        "feature/payment",
        branch_name="ai-tests/pr-123",
    )

    assert branch == "ai-tests/pr-123"
    assert runner.commands[0] == ["git", "checkout", "-b", "ai-tests/pr-123"]
