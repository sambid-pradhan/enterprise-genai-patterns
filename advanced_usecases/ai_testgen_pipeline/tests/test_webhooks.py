import hashlib
import hmac

from fastapi.testclient import TestClient

from app.models import RunCreateRequest
from app.repositories import RunRepository
from app.webhooks import create_github_webhook_router, filter_python_targets, verify_github_signature


def test_filter_python_targets_keeps_source_python_files():
    paths = [
        "src/app.py",
        "tests/test_app.py",
        "src/app_test.py",
        "src/test_utils.py",
        "README.md",
    ]

    assert filter_python_targets(paths) == ["src/app.py"]


def test_verify_github_signature_allows_unsigned_local_when_secret_missing():
    assert verify_github_signature(b"{}", None, None) is True


def test_verify_github_signature_rejects_invalid_signature_when_secret_set():
    assert verify_github_signature(b"{}", "sha256=bad", "secret") is False


def test_verify_github_signature_accepts_valid_signature():
    body = b'{"ok": true}'
    digest = hmac.new(b"secret", body, hashlib.sha256).hexdigest()

    assert verify_github_signature(body, f"sha256={digest}", "secret") is True


class FakeWorkflowStarter:
    def __init__(self):
        self.started = []

    def start(self, run_id):
        self.started.append(run_id)


class FakeGitHubClient:
    def __init__(self, files):
        self.files = files
        self.calls = []

    def get_pr_changed_files(self, repository_full_name, pr_number):
        self.calls.append((repository_full_name, pr_number))
        return self.files


def make_payload(label="generate-tests"):
    return {
        "action": "labeled",
        "label": {"name": label},
        "repository": {
            "full_name": "acme/repo",
            "clone_url": "https://github.com/acme/repo.git",
        },
        "pull_request": {
            "number": 123,
            "head": {"ref": "feature/payment"},
        },
    }


def make_client(session_factory, files):
    repository = RunRepository(session_factory)
    workflow = FakeWorkflowStarter()
    github = FakeGitHubClient(files)
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(create_github_webhook_router(repository, workflow, github, None))
    return TestClient(app), repository, workflow, github


def test_github_webhook_ignores_wrong_event(session_factory):
    client, repository, workflow, github = make_client(session_factory, ["src/app.py"])

    response = client.post(
        "/webhooks/github",
        json=make_payload(),
        headers={"X-GitHub-Event": "issues"},
    )

    assert response.status_code == 200
    assert response.json()["ignored"] is True
    assert workflow.started == []


def test_github_webhook_ignores_wrong_label(session_factory):
    client, repository, workflow, github = make_client(session_factory, ["src/app.py"])

    response = client.post(
        "/webhooks/github",
        json=make_payload(label="other"),
        headers={"X-GitHub-Event": "pull_request"},
    )

    assert response.status_code == 200
    assert response.json()["ignored"] is True
    assert workflow.started == []


def test_github_webhook_creates_run_for_generate_tests_label(session_factory):
    client, repository, workflow, github = make_client(session_factory, ["src/app.py", "tests/test_app.py"])

    response = client.post(
        "/webhooks/github",
        json=make_payload(),
        headers={"X-GitHub-Event": "pull_request"},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert workflow.started == [body["id"]]
    run = repository.get_run(body["id"])
    assert run.request.repo_url == "https://github.com/acme/repo.git"
    assert run.request.base_branch == "feature/payment"
    assert run.request.target_paths == ["src/app.py"]
    assert run.request.create_pr is True
    assert run.request.source_pr_number == 123


def test_github_webhook_ignores_when_no_eligible_python_files(session_factory):
    client, repository, workflow, github = make_client(session_factory, ["tests/test_app.py", "README.md"])

    response = client.post(
        "/webhooks/github",
        json=make_payload(),
        headers={"X-GitHub-Event": "pull_request"},
    )

    assert response.status_code == 200
    assert response.json() == {"ignored": True, "reason": "no eligible python files"}
    assert workflow.started == []
