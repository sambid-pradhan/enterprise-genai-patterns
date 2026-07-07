from fastapi import FastAPI

from app.api import WorkflowStarter, create_router
from app.logging_config import configure_logging
from app.repositories import RunRepository, create_engine_from_url, create_schema, get_session_factory
from app.settings import get_settings
from app.workflows import generate_tests_workflow


class DBOSWorkflowStarter(WorkflowStarter):
    def start(self, run_id: str) -> None:
        generate_tests_workflow.start(run_id)


def create_app(
    repository: RunRepository | None = None,
    workflow_starter: WorkflowStarter | None = None,
) -> FastAPI:
    configure_logging()
    if repository is None:
        settings = get_settings()
        engine = create_engine_from_url(settings.database_url)
        create_schema(engine)
        repository = RunRepository(get_session_factory(engine))
    if workflow_starter is None:
        workflow_starter = DBOSWorkflowStarter()

    app = FastAPI(title="AI Test Generation Pipeline")
    app.include_router(create_router(repository, workflow_starter))
    return app


app = create_app()
