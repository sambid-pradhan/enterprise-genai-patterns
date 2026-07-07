from pathlib import Path

from app.command_runner import CommandResult, CommandRunner


class PytestRunner:
    def __init__(self, command_runner: CommandRunner, pytest_command: str, timeout_seconds: int) -> None:
        self._runner = command_runner
        self._pytest = pytest_command
        self._timeout = timeout_seconds

    def run_pytest(self, repo_path: Path) -> CommandResult:
        return self._runner.run([self._pytest], cwd=repo_path, timeout_seconds=self._timeout)
