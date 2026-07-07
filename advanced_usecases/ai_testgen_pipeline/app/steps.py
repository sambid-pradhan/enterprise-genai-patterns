from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.agent_runner import AgentRunner
from app.git_client import GitClient
from app.github_client import GitHubClient
from app.models import RunStatus
from app.pytest_runner import PytestRunner
from app.repositories import RunRepository


@dataclass
class WorkflowContext:
    run_id: UUID
    repository: RunRepository
    git_client: GitClient
    agent_runner: AgentRunner
    pytest_runner: PytestRunner
    github_client: GitHubClient


def clone_repo(context: WorkflowContext) -> Path:
    run = context.repository.get_run(context.run_id)
    if run is None:
        raise KeyError(f"run not found: {context.run_id}")
    repo_path = context.git_client.prepare_repo(str(context.run_id), run.request)
    context.repository.update_run(
        context.run_id,
        status=RunStatus.RUNNING,
        repo_path=str(repo_path),
    )
    return repo_path


def run_agent(context: WorkflowContext, repo_path: Path) -> None:
    run = context.repository.get_run(context.run_id)
    if run is None:
        raise KeyError(f"run not found: {context.run_id}")
    result = context.agent_runner.generate_tests(repo_path, run.request)
    fields = {
        "agent_stdout": result.stdout,
        "agent_stderr": result.stderr,
    }
    if result.exit_code != 0:
        fields["status"] = RunStatus.AGENT_FAILED
        fields["error"] = result.stderr or result.stdout or "Codex CLI failed"
    context.repository.update_run(context.run_id, **fields)


def run_pytest(context: WorkflowContext, repo_path: Path) -> int:
    result = context.pytest_runner.run_pytest(repo_path)
    fields = {
        "pytest_exit_code": result.exit_code,
        "pytest_stdout": result.stdout,
        "pytest_stderr": result.stderr,
    }
    if result.exit_code != 0:
        fields["status"] = RunStatus.TESTS_FAILED
        fields["error"] = result.stderr or result.stdout or "pytest failed"
    context.repository.update_run(context.run_id, **fields)
    return result.exit_code


def store_results(context: WorkflowContext, repo_path: Path) -> str:
    generated_diff = context.git_client.diff(repo_path)
    context.repository.update_run(context.run_id, generated_diff=generated_diff)
    return generated_diff


def maybe_create_pr(context: WorkflowContext, repo_path: Path, pytest_exit_code: int) -> str | None:
    run = context.repository.get_run(context.run_id)
    if run is None:
        raise KeyError(f"run not found: {context.run_id}")
    if pytest_exit_code != 0:
        return None
    if not run.request.create_pr:
        context.repository.update_run(context.run_id, status=RunStatus.COMPLETED)
        return None
    if not context.git_client.has_github_remote(repo_path):
        context.repository.update_run(
            context.run_id,
            status=RunStatus.COMPLETED_WITHOUT_PR,
            error="create_pr requested, but repository has no GitHub remote",
        )
        return None

    try:
        branch = context.git_client.create_branch_commit_push(
            repo_path,
            str(context.run_id),
            run.request.base_branch,
        )
        pr_url = context.github_client.create_pr(
            repo_path,
            branch,
            run.request.base_branch,
            str(context.run_id),
        )
    except RuntimeError as exc:
        context.repository.update_run(context.run_id, status=RunStatus.PR_FAILED, error=str(exc))
        return None

    context.repository.update_run(context.run_id, status=RunStatus.COMPLETED, pr_url=pr_url)
    return pr_url
