from uuid import UUID

try:
    from dbos import DBOS
except ImportError:
    class _LocalDBOS:
        @staticmethod
        def workflow():
            def decorate(func):
                func.start = func
                return func

            return decorate

    DBOS = _LocalDBOS()

from app.steps import WorkflowContext, clone_repo, maybe_create_pr, run_agent, run_pytest, store_results


def build_workflow_context(run_id: UUID) -> WorkflowContext:
    raise RuntimeError("Workflow dependencies are configured by app.main at runtime")


@DBOS.workflow()
def generate_tests_workflow(run_id: str) -> dict[str, str | None]:
    context = build_workflow_context(UUID(run_id))
    repo_path = clone_repo(context)
    run_agent(context, repo_path)
    pytest_exit_code = run_pytest(context, repo_path)
    store_results(context, repo_path)
    pr_url = maybe_create_pr(context, repo_path, pytest_exit_code)
    return {"run_id": run_id, "pr_url": pr_url}
