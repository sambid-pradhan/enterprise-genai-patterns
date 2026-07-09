from pathlib import Path

from app.agent_runner import AgentRunner
from app.command_runner import CommandResult
from app.models import RunCreateRequest


class FakeCommandRunner:
    def __init__(self):
        self.calls = []

    def run(self, command, cwd=None, timeout_seconds=None):
        self.calls.append((command, cwd, timeout_seconds))
        return CommandResult(list(command), str(cwd), 0, "", "")


def test_generate_tests_runs_codex_with_writable_workspace(tmp_path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "generate_tests.md").write_text("Generate tests.", encoding="utf-8")
    runner = FakeCommandRunner()
    agent = AgentRunner(runner, "codex", prompts_dir, 30)
    request = RunCreateRequest(repo_url="sample", target_paths=["src/sample_app/calculator.py"])

    agent.generate_tests(Path("repo"), request)

    command, cwd, timeout = runner.calls[0]
    assert command[:5] == ["codex", "exec", "--skip-git-repo-check", "--sandbox", "workspace-write"]
    assert "Target paths: src/sample_app/calculator.py" in command[5]
    assert cwd == Path("repo")
    assert timeout == 30


def test_generate_tests_includes_pytest_feedback(tmp_path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "generate_tests.md").write_text("Generate tests.", encoding="utf-8")
    runner = FakeCommandRunner()
    agent = AgentRunner(runner, "codex", prompts_dir, 30)
    request = RunCreateRequest(repo_url="sample", target_paths=["src/sample_app/calculator.py"])

    agent.generate_tests(Path("repo"), request, pytest_feedback="assertion failed")

    assert "Pytest failed" in runner.calls[0][0][5]
    assert "assertion failed" in runner.calls[0][0][5]
