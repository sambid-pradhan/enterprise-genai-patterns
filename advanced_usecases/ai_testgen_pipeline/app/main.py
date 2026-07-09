from threading import Thread
from uuid import UUID

from fastapi import FastAPI

from app.agent_runner import AgentRunner
from app.api import WorkflowStarter, create_router
from app.command_runner import CommandRunner
from app.git_client import GitClient
from app.github_client import GitHubClient
from app.logging_config import configure_logging
from app.pytest_runner import PytestRunner
from app.repositories import RunRepository, create_engine_from_url, create_schema, get_session_factory
from app.settings import Settings, get_settings
from app.steps import WorkflowContext
from app.workflows import configure_workflow_context_factory, generate_tests_workflow, generate_tests_workflow_impl

_USE_SETTINGS_SECRET = object()


class DBOSWorkflowStarter(WorkflowStarter):
    def start(self, run_id: str) -> None:
        generate_tests_workflow.start(run_id)


class LocalWorkflowStarter(WorkflowStarter):
    def start(self, run_id: str) -> None:
        Thread(target=generate_tests_workflow_impl, args=(run_id,), daemon=True).start()


def build_repository(settings: Settings) -> RunRepository:
    engine = create_engine_from_url(settings.database_url)
    create_schema(engine)
    return RunRepository(get_session_factory(engine))


def configure_runtime(repository: RunRepository, settings: Settings) -> None:
    command_runner = CommandRunner()

    def context_factory(run_id: UUID) -> WorkflowContext:
        return WorkflowContext(
            run_id=run_id,
            repository=repository,
            git_client=GitClient(
                command_runner,
                settings.git_command,
                settings.repos_dir,
                settings.sample_repo_dir,
                settings.git_timeout_seconds,
            ),
            agent_runner=AgentRunner(
                command_runner,
                settings.codex_command,
                settings.prompts_dir,
                settings.agent_timeout_seconds,
            ),
            pytest_runner=PytestRunner(
                command_runner,
                settings.pytest_command,
                settings.pytest_timeout_seconds,
            ),
            github_client=GitHubClient(
                command_runner,
                settings.gh_command,
                settings.git_timeout_seconds,
            ),
        )

    configure_workflow_context_factory(context_factory)


def create_app(
    repository: RunRepository | None = None,
    workflow_starter: WorkflowStarter | None = None,
    github_client: GitHubClient | None = None,
    github_webhook_secret: str | None | object = _USE_SETTINGS_SECRET,
) -> FastAPI:
    configure_logging()
    settings = get_settings()
    if repository is None:
        repository = build_repository(settings)
    configure_runtime(repository, settings)
    if workflow_starter is None:
        workflow_starter = LocalWorkflowStarter() if settings.app_env == "local" else DBOSWorkflowStarter()
    if github_client is None:
        github_client = GitHubClient(CommandRunner(), settings.gh_command, settings.git_timeout_seconds)
    if github_webhook_secret is _USE_SETTINGS_SECRET:
        github_webhook_secret = settings.github_webhook_secret

    app = FastAPI(title="AI Test Generation Pipeline")
    app.state.workflow_starter = workflow_starter
    app.include_router(
        create_router(repository, workflow_starter, github_client, github_webhook_secret)
    )
    return app


app = create_app()
