from pathlib import Path

from app.command_runner import CommandResult, CommandRunner
from app.models import RunCreateRequest


class AgentRunner:
    def __init__(
        self,
        command_runner: CommandRunner,
        codex_command: str,
        prompts_dir: Path,
        timeout_seconds: int,
    ) -> None:
        self._runner = command_runner
        self._codex = codex_command
        self._prompts_dir = prompts_dir
        self._timeout = timeout_seconds

    def generate_tests(self, repo_path: Path, request: RunCreateRequest) -> CommandResult:
        prompt_template = (self._prompts_dir / "generate_tests.md").read_text(encoding="utf-8")
        prompt = (
            f"{prompt_template}\n\n"
            f"Repository path: {repo_path}\n"
            f"Target paths: {', '.join(request.target_paths)}\n"
            f"Test framework: {request.test_framework}\n"
        )
        return self._runner.run([self._codex, "exec", prompt], cwd=repo_path, timeout_seconds=self._timeout)
