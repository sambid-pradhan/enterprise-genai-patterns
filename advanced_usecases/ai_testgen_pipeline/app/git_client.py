import shutil
from pathlib import Path

from app.command_runner import CommandRunner
from app.models import RunCreateRequest


class GitClient:
    def __init__(
        self,
        command_runner: CommandRunner,
        git_command: str,
        repos_dir: Path,
        sample_repo_dir: Path,
        timeout_seconds: int,
    ) -> None:
        self._runner = command_runner
        self._git = git_command
        self._repos_dir = repos_dir
        self._sample_repo_dir = sample_repo_dir
        self._timeout = timeout_seconds

    def prepare_repo(self, run_id: str, request: RunCreateRequest) -> Path:
        self._repos_dir.mkdir(parents=True, exist_ok=True)
        destination = self._repos_dir / run_id
        if destination.exists():
            raise FileExistsError(f"repo checkout already exists: {destination}")

        if request.repo_url == "sample":
            shutil.copytree(self._sample_repo_dir, destination)
            return destination

        result = self._runner.run(
            [
                self._git,
                "clone",
                "--branch",
                request.base_branch,
                "--single-branch",
                request.repo_url,
                str(destination),
            ],
            timeout_seconds=self._timeout,
        )
        if result.exit_code != 0:
            raise RuntimeError(result.stderr or result.stdout or "git clone failed")
        return destination

    def diff(self, repo_path: Path) -> str:
        result = self._runner.run([self._git, "diff", "--", "."], cwd=repo_path, timeout_seconds=self._timeout)
        return result.stdout

    def has_github_remote(self, repo_path: Path) -> bool:
        result = self._runner.run([self._git, "remote", "-v"], cwd=repo_path, timeout_seconds=self._timeout)
        if result.exit_code != 0:
            return False
        return "github.com" in result.stdout

    def create_branch_commit_push(self, repo_path: Path, run_id: str, base_branch: str) -> str:
        branch = f"ai-tests/{run_id}"
        commands = [
            [self._git, "checkout", "-b", branch],
            [self._git, "add", "."],
            [self._git, "commit", "-m", "Add AI-generated tests"],
            [self._git, "push", "origin", branch],
        ]
        for command in commands:
            result = self._runner.run(command, cwd=repo_path, timeout_seconds=self._timeout)
            if result.exit_code != 0:
                raise RuntimeError(result.stderr or result.stdout or f"command failed: {command}")
        return branch
