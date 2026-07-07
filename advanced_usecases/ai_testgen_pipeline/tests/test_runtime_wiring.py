from app.models import RunCreateRequest
from app.repositories import RunRepository
from app.workflows import build_workflow_context, configure_workflow_context_factory


def test_configure_workflow_context_factory_controls_builder(session_factory):
    repository = RunRepository(session_factory)
    run = repository.create_run(
        RunCreateRequest(repo_url="sample", target_paths=["src/sample_app/calculator.py"])
    )

    expected = object()
    configure_workflow_context_factory(lambda run_id: expected)

    assert build_workflow_context(run.id) is expected
