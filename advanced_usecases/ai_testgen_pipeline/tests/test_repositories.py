from app.models import RunCreateRequest, RunStatus
from app.repositories import RunRepository


def test_create_and_fetch_run(session_factory):
    repo = RunRepository(session_factory)
    request = RunCreateRequest(repo_url="sample", target_paths=["src/sample_app/calculator.py"])

    created = repo.create_run(request)
    fetched = repo.get_run(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.status == RunStatus.QUEUED
    assert fetched.request.repo_url == "sample"


def test_update_run_stores_outputs(session_factory):
    repo = RunRepository(session_factory)
    created = repo.create_run(
        RunCreateRequest(repo_url="sample", target_paths=["src/sample_app/calculator.py"])
    )

    updated = repo.update_run(
        created.id,
        status=RunStatus.TESTS_FAILED,
        pytest_exit_code=1,
        pytest_stdout="stdout",
        pytest_stderr="stderr",
        generated_diff="diff",
        error="tests failed",
    )

    assert updated.status == RunStatus.TESTS_FAILED
    assert updated.pytest_exit_code == 1
    assert updated.pytest_stdout == "stdout"
    assert updated.pytest_stderr == "stderr"
    assert updated.generated_diff == "diff"
    assert updated.error == "tests failed"


def test_list_runs_orders_recent_first(session_factory):
    repo = RunRepository(session_factory)
    first = repo.create_run(RunCreateRequest(repo_url="sample", target_paths=["a.py"]))
    second = repo.create_run(RunCreateRequest(repo_url="sample", target_paths=["b.py"]))

    runs = repo.list_runs()

    assert [run.id for run in runs] == [second.id, first.id]
