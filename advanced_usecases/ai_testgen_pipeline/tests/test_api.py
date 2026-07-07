from fastapi.testclient import TestClient

from app.main import create_app
from app.models import RunCreateRequest
from app.repositories import RunRepository


class FakeWorkflowStarter:
    def __init__(self):
        self.started = []

    def start(self, run_id):
        self.started.append(run_id)


def test_post_runs_creates_run_and_starts_workflow(session_factory):
    repository = RunRepository(session_factory)
    workflow = FakeWorkflowStarter()
    app = create_app(repository=repository, workflow_starter=workflow)
    client = TestClient(app)

    response = client.post(
        "/runs",
        json={"repo_url": "sample", "target_paths": ["src/sample_app/calculator.py"]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "queued"
    assert workflow.started == [body["id"]]


def test_get_run_returns_created_run(session_factory):
    repository = RunRepository(session_factory)
    created = repository.create_run(
        RunCreateRequest(repo_url="sample", target_paths=["src/sample_app/calculator.py"])
    )
    app = create_app(repository=repository, workflow_starter=FakeWorkflowStarter())
    client = TestClient(app)

    response = client.get(f"/runs/{created.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(created.id)


def test_get_runs_lists_runs(session_factory):
    repository = RunRepository(session_factory)
    repository.create_run(RunCreateRequest(repo_url="sample", target_paths=["a.py"]))
    app = create_app(repository=repository, workflow_starter=FakeWorkflowStarter())
    client = TestClient(app)

    response = client.get("/runs")

    assert response.status_code == 200
    assert len(response.json()) == 1
