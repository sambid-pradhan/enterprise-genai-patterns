import hashlib
import hmac
from pathlib import PurePosixPath
from typing import Any, Protocol

from fastapi import APIRouter, Header, HTTPException, Request, Response, status

from app.github_client import GitHubClient
from app.models import RunCreateRequest, RunCreateResponse
from app.repositories import RunRepository


def verify_github_signature(body: bytes, signature_header: str | None, secret: str | None) -> bool:
    if not secret:
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    actual = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(actual, expected)


def filter_python_targets(paths: list[str]) -> list[str]:
    result = []
    for value in paths:
        path = PurePosixPath(value)
        name = path.name
        if path.suffix != ".py":
            continue
        if path.parts and path.parts[0] == "tests":
            continue
        if name.endswith("_test.py") or name.startswith("test_"):
            continue
        result.append(value)
    return result


class WorkflowStarterProtocol(Protocol):
    def start(self, run_id: str) -> None:
        pass


def create_github_webhook_router(
    repository: RunRepository,
    workflow_starter: WorkflowStarterProtocol,
    github_client: GitHubClient,
    github_webhook_secret: str | None,
) -> APIRouter:
    router = APIRouter()

    @router.post("/webhooks/github", status_code=status.HTTP_202_ACCEPTED)
    async def github_webhook(
        request: Request,
        response: Response,
        x_github_event: str | None = Header(default=None, alias="X-GitHub-Event"),
        x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    ):
        body = await request.body()
        if not verify_github_signature(body, x_hub_signature_256, github_webhook_secret):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid signature")

        if x_github_event != "pull_request":
            response.status_code = status.HTTP_200_OK
            return {"ignored": True, "reason": "unsupported event"}

        payload: dict[str, Any] = await request.json()
        if payload.get("action") != "labeled":
            response.status_code = status.HTTP_200_OK
            return {"ignored": True, "reason": "unsupported action"}
        if payload.get("label", {}).get("name") != "generate-tests":
            response.status_code = status.HTTP_200_OK
            return {"ignored": True, "reason": "unsupported label"}

        repository_payload = payload["repository"]
        pull_request = payload["pull_request"]
        repository_full_name = repository_payload["full_name"]
        pr_number = int(pull_request["number"])
        changed_files = github_client.get_pr_changed_files(repository_full_name, pr_number)
        target_paths = filter_python_targets(changed_files)
        if not target_paths:
            response.status_code = status.HTTP_200_OK
            return {"ignored": True, "reason": "no eligible python files"}

        run = repository.create_run(
            RunCreateRequest(
                repo_url=repository_payload["clone_url"],
                base_branch=pull_request["head"]["ref"],
                target_paths=target_paths,
                create_pr=True,
                source_pr_number=pr_number,
            )
        )
        workflow_starter.start(str(run.id))
        return RunCreateResponse(id=run.id, status=run.status)

    return router
