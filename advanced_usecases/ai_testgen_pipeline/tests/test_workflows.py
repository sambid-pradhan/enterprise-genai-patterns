from pathlib import Path

from app.command_runner import CommandResult
from app.models import RunCreateRequest, RunStatus
from app.steps import WorkflowContext
from app.workflows import configure_workflow_context_factory, generate_tests_workflow_impl


class FakeRun:
    def __init__(self, run_id, request):
        self.id = run_id
        self.request = request


class FakeRepository:
    def __init__(self, request):
        self.request = request
        self.updates = []

    def get_run(self, run_id):
        return FakeRun(run_id, self.request)

    def update_run(self, run_id, **fields):
        self.updates.append(fields)
        return FakeRun(run_id, self.request)


class FakeGit:
    def prepare_repo(self, run_id, request):
        return Path("repo")


class FailingAgent:
    def generate_tests(self, repo_path, request):
        return CommandResult(["codex"], str(repo_path), 1, "", "codex failed")


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
