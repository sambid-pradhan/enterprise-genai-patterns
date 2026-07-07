from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.models import RunCreateRequest, RunCreateResponse, RunRecord
from app.repositories import RunRepository


class WorkflowStarter:
    def start(self, run_id: str) -> None:
        raise NotImplementedError


def create_router(
    repository: RunRepository,
    workflow_starter: WorkflowStarter,
) -> APIRouter:
    router = APIRouter()

    def get_repository() -> RunRepository:
        return repository

    def get_workflow_starter() -> WorkflowStarter:
        return workflow_starter

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/runs", response_model=RunCreateResponse, status_code=status.HTTP_201_CREATED)
    def create_run(
        request: RunCreateRequest,
        run_repository: RunRepository = Depends(get_repository),
        starter: WorkflowStarter = Depends(get_workflow_starter),
    ) -> RunCreateResponse:
        run = run_repository.create_run(request)
        starter.start(str(run.id))
        return RunCreateResponse(id=run.id, status=run.status)

    @router.get("/runs/{run_id}", response_model=RunRecord)
    def get_run(
        run_id: UUID,
        run_repository: RunRepository = Depends(get_repository),
    ) -> RunRecord:
        run = run_repository.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        return run

    @router.get("/runs", response_model=list[RunRecord])
    def list_runs(run_repository: RunRepository = Depends(get_repository)) -> list[RunRecord]:
        return run_repository.list_runs()

    return router
