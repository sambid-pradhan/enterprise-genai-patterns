from pathlib import Path

from app.command_runner import CommandResult
from app.models import RunCreateRequest, RunStatus
from app.steps import WorkflowContext
from app.workflows import configure_workflow_context_factory, generate_tests_workflow_impl


class FakeRun:
    def __init__(self, run_id, request, pytest_stdout=None, pytest_stderr=None):
        self.id = run_id
        self.request = request
        self.pytest_stdout = pytest_stdout
        self.pytest_stderr = pytest_stderr


class FakeRepository:
    def __init__(self, request):
        self.request = request
        self.updates = []
        self.pytest_stdout = None
        self.pytest_stderr = None

    def get_run(self, run_id):
        return FakeRun(run_id, self.request, self.pytest_stdout, self.pytest_stderr)

    def update_run(self, run_id, **fields):
        self.updates.append(fields)
        self.pytest_stdout = fields.get("pytest_stdout", self.pytest_stdout)
        self.pytest_stderr = fields.get("pytest_stderr", self.pytest_stderr)
        return self.get_run(run_id)


class FakeGit:
    def prepare_repo(self, run_id, request):
        return Path("repo")

    def diff(self, repo_path):
        return "diff"

    def has_github_remote(self, repo_path):
        return False


class FailingAgent:
    def generate_tests(self, repo_path, request, pytest_feedback=None):
        return CommandResult(["codex"], str(repo_path), 1, "", "codex failed")


class FixingAgent:
    def __init__(self):
        self.feedback = []

    def generate_tests(self, repo_path, request, pytest_feedback=None):
        self.feedback.append(pytest_feedback)
        return CommandResult(["codex"], str(repo_path), 0, "", "")


class FlakyPytest:
    def __init__(self):
        self.calls = 0

    def run_pytest(self, repo_path):
        self.calls += 1
        if self.calls == 1:
            return CommandResult(["pytest"], str(repo_path), 1, "failed test", "")
        return CommandResult(["pytest"], str(repo_path), 0, "passed", "")


class UnexpectedPytest:
    def run_pytest(self, repo_path):
        raise AssertionError("pytest should not run when the agent fails")


class FakeGithub:
    pass


def test_workflow_stops_when_agent_fails():
    request = RunCreateRequest(repo_url="sample", target_paths=["src/sample_app/calculator.py"])
    repository = FakeRepository(request)

    def context_factory(run_id):
        return WorkflowContext(
            run_id=run_id,
            repository=repository,
            git_client=FakeGit(),
            agent_runner=FailingAgent(),
            pytest_runner=UnexpectedPytest(),
            github_client=FakeGithub(),
        )

    configure_workflow_context_factory(context_factory)

    result = generate_tests_workflow_impl("00000000-0000-0000-0000-000000000001")

    assert result == {"run_id": "00000000-0000-0000-0000-000000000001", "pr_url": None}
    assert repository.updates[-1]["status"] == RunStatus.AGENT_FAILED
    assert repository.updates[-1]["error"] == "codex failed"


def test_workflow_reruns_agent_once_when_pytest_fails():
    request = RunCreateRequest(repo_url="sample", target_paths=["src/sample_app/calculator.py"])
    repository = FakeRepository(request)
    agent = FixingAgent()
    pytest_runner = FlakyPytest()

    def context_factory(run_id):
        return WorkflowContext(
            run_id=run_id,
            repository=repository,
            git_client=FakeGit(),
            agent_runner=agent,
            pytest_runner=pytest_runner,
            github_client=FakeGithub(),
        )

    configure_workflow_context_factory(context_factory)

    result = generate_tests_workflow_impl("00000000-0000-0000-0000-000000000002")

    assert result == {"run_id": "00000000-0000-0000-0000-000000000002", "pr_url": None}
    assert agent.feedback == [None, "failed test"]
    assert pytest_runner.calls == 2
    assert repository.updates[-1]["status"] == RunStatus.COMPLETED
