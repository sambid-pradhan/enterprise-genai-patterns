from pathlib import Path

from app.command_runner import CommandResult
from app.github_client import GitHubClient


class FakeCommandRunner:
    def __init__(self):
        self.calls = []

    def run(self, command, cwd=None, timeout_seconds=None):
        self.calls.append((command, cwd, timeout_seconds))
        return CommandResult(list(command), str(cwd), 0, '[{"name":"tests","state":"SUCCESS"}]', "")


def test_get_pr_checks_uses_github_cli_json_output():
    runner = FakeCommandRunner()
    client = GitHubClient(runner, "gh", 30)

    result = client.get_pr_checks(Path("repo"), "ai-tests/run")

    command, cwd, timeout = runner.calls[0]
    assert command == [
        "gh",
        "pr",
        "checks",
        "ai-tests/run",
        "--json",
        "name,state,conclusion,link",
    ]
    assert cwd == Path("repo")
    assert timeout == 30
    assert result == '[{"name":"tests","state":"SUCCESS"}]'


def test_get_pr_changed_files_reads_files_from_github_cli_json():
    class FilesRunner:
        def __init__(self):
            self.calls = []

        def run(self, command, cwd=None, timeout_seconds=None):
            self.calls.append((command, cwd, timeout_seconds))
            return CommandResult(
                list(command),
                str(cwd) if cwd is not None else None,
                0,
                '{"files":[{"path":"src/app.py"},{"path":"tests/test_app.py"}]}',
                "",
            )

    runner = FilesRunner()
    client = GitHubClient(runner, "gh", 30)

    files = client.get_pr_changed_files("acme/repo", 123)

    assert files == ["src/app.py", "tests/test_app.py"]
    assert runner.calls[0][0] == [
        "gh",
        "pr",
        "view",
        "123",
        "--repo",
        "acme/repo",
        "--json",
        "files",
    ]
