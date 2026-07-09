from pathlib import Path
from uuid import uuid4

from app.command_runner import CommandResult
from app.models import RunCreateRequest, RunStatus
from app.steps import WorkflowContext, maybe_create_pr, run_agent, run_pytest


class FakeRepository:
    def __init__(self, request):
        self.request = request
        self.updates = []

    def get_run(self, run_id):
        return type("Run", (), {"id": run_id, "request": self.request})

    def update_run(self, run_id, **fields):
        self.updates.append(fields)
        return type("Run", (), fields)


class FakeAgent:
    def __init__(self, exit_code):
        self.exit_code = exit_code

    def generate_tests(self, repo_path, request, pytest_feedback=None):
        return CommandResult(["codex"], str(repo_path), self.exit_code, "agent out", "agent err")


class FakePytest:
    def __init__(self, exit_code):
        self.exit_code = exit_code

    def run_pytest(self, repo_path):
        return CommandResult(["pytest"], str(repo_path), self.exit_code, "pytest out", "pytest err")


class FakeGit:
    def __init__(self):
        self.has_remote = True

    def has_github_remote(self, repo_path):
        return self.has_remote

    def create_branch_commit_push(self, repo_path, run_id, base_branch, branch_name=None):
        return "ai-tests/run"


class FakeGithub:
    def create_pr(self, repo_path, branch, base_branch, run_id, title=None, body=None):
        return "https://github.com/acme/repo/pull/1"

    def get_pr_checks(self, repo_path, branch):
        return '[{"name":"tests","state":"SUCCESS"}]'


def make_context(request, repo, agent=None, pytest_runner=None, git=None, github=None):
    return WorkflowContext(
        run_id=uuid4(),
        repository=repo,
        git_client=git or FakeGit(),
        agent_runner=agent or FakeAgent(0),
        pytest_runner=pytest_runner or FakePytest(0),
        github_client=github or FakeGithub(),
    )


def test_run_agent_marks_agent_failed_on_nonzero_exit():
    request = RunCreateRequest(repo_url="sample", target_paths=["src/sample_app/calculator.py"])
    repo = FakeRepository(request)
    context = make_context(request, repo, agent=FakeAgent(2))

    run_agent(context, Path("repo"))

    assert repo.updates[-1]["status"] == RunStatus.AGENT_FAILED
    assert repo.updates[-1]["agent_stderr"] == "agent err"


def test_run_pytest_marks_tests_failed_on_nonzero_exit():
    request = RunCreateRequest(repo_url="sample", target_paths=["src/sample_app/calculator.py"])
    repo = FakeRepository(request)
    context = make_context(request, repo, pytest_runner=FakePytest(1))

    exit_code = run_pytest(context, Path("repo"))

    assert exit_code == 1
    assert repo.updates[-1]["status"] == RunStatus.TESTS_FAILED
    assert repo.updates[-1]["pytest_stdout"] == "pytest out"


def test_maybe_create_pr_returns_url_when_enabled_and_tests_pass():
    request = RunCreateRequest(
        repo_url="https://github.com/acme/repo.git",
        target_paths=["src/app.py"],
        create_pr=True,
    )
    repo = FakeRepository(request)
    context = make_context(request, repo)

    pr_url = maybe_create_pr(context, Path("repo"), pytest_exit_code=0)

    assert pr_url == "https://github.com/acme/repo/pull/1"
    assert repo.updates[-1]["status"] == RunStatus.COMPLETED
    assert repo.updates[-1]["pr_url"] == pr_url
    assert repo.updates[-1]["ci_status"] == '[{"name":"tests","state":"SUCCESS"}]'


def test_maybe_create_pr_uses_source_pr_branch_and_title_when_present():
    request = RunCreateRequest(
        repo_url="https://github.com/acme/repo.git",
        target_paths=["src/app.py"],
        base_branch="feature/payment",
        create_pr=True,
        source_pr_number=123,
    )
    repo = FakeRepository(request)

    class CapturingGit(FakeGit):
        def __init__(self):
            super().__init__()
            self.branch_name = None

        def create_branch_commit_push(self, repo_path, run_id, base_branch, branch_name=None):
            self.branch_name = branch_name
            return branch_name

    class CapturingGithub(FakeGithub):
        def __init__(self):
            self.title = None
            self.base_branch = None

        def create_pr(self, repo_path, branch, base_branch, run_id, title=None, body=None):
            self.title = title
            self.base_branch = base_branch
            return "https://github.com/acme/repo/pull/2"

        def get_pr_checks(self, repo_path, branch):
            return "[]"

    git = CapturingGit()
    github = CapturingGithub()
    context = make_context(request, repo, git=git, github=github)

    maybe_create_pr(context, Path("repo"), pytest_exit_code=0)

    assert git.branch_name == "ai-tests/pr-123"
    assert github.title == "AI Generated Tests for PR #123"
    assert github.base_branch == "feature/payment"
