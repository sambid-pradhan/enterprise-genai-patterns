import pytest
from pydantic import ValidationError

from app.models import RunCreateRequest, RunStatus


def test_run_create_request_accepts_sample_repo_defaults():
    request = RunCreateRequest(
        repo_url="sample",
        target_paths=["src/sample_app/calculator.py"],
    )

    assert request.repo_url == "sample"
    assert request.base_branch == "main"
    assert request.test_framework == "pytest"
    assert request.create_pr is False


def test_run_create_request_requires_target_paths():
    with pytest.raises(ValidationError):
        RunCreateRequest(repo_url="sample", target_paths=[])


def test_run_status_values_are_api_stable():
    assert RunStatus.QUEUED.value == "queued"
    assert RunStatus.RUNNING.value == "running"
    assert RunStatus.AGENT_FAILED.value == "agent_failed"
    assert RunStatus.TESTS_FAILED.value == "tests_failed"
    assert RunStatus.COMPLETED.value == "completed"
    assert RunStatus.COMPLETED_WITHOUT_PR.value == "completed_without_pr"
    assert RunStatus.PR_FAILED.value == "pr_failed"
    assert RunStatus.FAILED.value == "failed"
