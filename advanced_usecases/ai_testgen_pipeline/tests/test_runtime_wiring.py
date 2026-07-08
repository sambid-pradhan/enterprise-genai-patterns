import app.main
from app.models import RunCreateRequest
from app.main import LocalWorkflowStarter, create_app
from app.repositories import RunRepository
from app.settings import get_settings
from app.workflows import build_workflow_context, configure_workflow_context_factory


def test_configure_workflow_context_factory_controls_builder(session_factory):
    repository = RunRepository(session_factory)
    run = repository.create_run(
        RunCreateRequest(repo_url="sample", target_paths=["src/sample_app/calculator.py"])
    )

    expected = object()
    configure_workflow_context_factory(lambda run_id: expected)

    assert build_workflow_context(run.id) is expected


def test_create_app_uses_local_workflow_starter_by_default(session_factory, monkeypatch):
    repository = RunRepository(session_factory)
    monkeypatch.setenv("APP_ENV", "local")
    get_settings.cache_clear()

    app = create_app(repository=repository)

    assert isinstance(app.state.workflow_starter, LocalWorkflowStarter)
    get_settings.cache_clear()


def test_local_workflow_starter_runs_plain_workflow_impl(monkeypatch):
    started = []

    def fake_workflow_impl(run_id):
        started.append(run_id)

    class ImmediateThread:
        def __init__(self, target, args, daemon):
            self.target = target
            self.args = args
            self.daemon = daemon

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(app.main, "Thread", ImmediateThread)
    monkeypatch.setattr(app.main, "generate_tests_workflow_impl", fake_workflow_impl)

    LocalWorkflowStarter().start("run-1")

    assert started == ["run-1"]
