# AI Testgen GitHub Webhook Design

## Goal

Move `ai_testgen_pipeline` from a manual API-triggered demo to a GitHub label-triggered workflow:

```text
pull_request.labeled(generate-tests)
  -> POST /webhooks/github
  -> create queued run from changed Python files
  -> DBOS workflow
  -> Codex generates tests
  -> pytest verifies locally
  -> push ai-tests/pr-<number>
  -> open separate AI PR
```

Iteration 2 stops at a reliable label trigger and separate AI PR. It does not add CI auto-heal, webhook delivery storage, dedupe tables, scheduled polling, or GitHub App auth.

## Trigger

Add:

```text
POST /webhooks/github
```

The endpoint accepts GitHub webhook headers and raw JSON body. It only starts work for:

```text
X-GitHub-Event: pull_request
payload.action: labeled
payload.label.name: generate-tests
```

All other events return `200` with an ignored response, for example:

```json
{"ignored": true, "reason": "unsupported event"}
```

This prevents GitHub retries for events the platform intentionally ignores.

## Webhook Security

Use GitHub's `X-Hub-Signature-256` HMAC header when `GITHUB_WEBHOOK_SECRET` is configured.

Rules:

- If `GITHUB_WEBHOOK_SECRET` is set, missing or invalid signatures return `401`.
- If `GITHUB_WEBHOOK_SECRET` is not set, local unsigned requests are allowed.
- Signature comparison uses constant-time comparison.

The unsigned local path is only for demo convenience. Production deployments should always set `GITHUB_WEBHOOK_SECRET`.

## Changed File Selection

For an accepted `pull_request.labeled` event, the webhook fetches changed files for the source PR and filters them before creating a run.

Include:

```text
*.py
```

Exclude:

```text
tests/*
*_test.py
test_*.py
```

If no eligible files remain, return:

```json
{"ignored": true, "reason": "no eligible python files"}
```

No workflow should start in that case.

## Run Creation

The webhook creates a normal application run so the existing DBOS workflow, repository persistence, Codex runner, pytest runner, diff capture, PR creation, and status API remain the main execution path.

The run request should include:

```json
{
  "repo_url": "<repository clone URL>",
  "base_branch": "<source PR branch>",
  "target_paths": ["changed/file.py"],
  "create_pr": true,
  "source_pr_number": 123
}
```

`base_branch` is the source PR branch, not the target branch such as `main`. Codex must generate tests against the developer's changes.

## PR Output

Webhook-triggered runs create a separate AI PR instead of pushing to the developer's branch.

For source PR `#123` from branch `feature/payment`:

```text
AI branch: ai-tests/pr-123
AI PR title: AI Generated Tests for PR #123
AI PR base: feature/payment
```

Manual API runs without `source_pr_number` keep the existing behavior:

```text
AI branch: ai-tests/<run_id>
AI PR title: Add AI-generated tests for run <run_id>
AI PR base: request.base_branch
```

After PR creation, the existing `gh pr checks` snapshot is still stored as `ci_status`. Iteration 2 does not poll for later CI transitions.

## Components

### Webhook Endpoint

Extend the FastAPI router with `POST /webhooks/github`.

Responsibilities:

- Read raw body for signature verification.
- Check `X-GitHub-Event`.
- Ignore unsupported events/actions/labels.
- Extract repo clone URL, PR number, source branch, and repository identity.
- Ask the GitHub client for PR changed files.
- Filter eligible target paths.
- Create a run with `create_pr=true`.
- Start the existing workflow.

### GitHub Client

Add a minimal method for changed files:

```text
get_pr_changed_files(repository_full_name, pr_number) -> list[str]
```

The implementation will use GitHub CLI because the project already depends on `gh`:

```text
gh pr view <number> --repo <owner/name> --json files
```

This keeps the iteration aligned with the current GitHub CLI approach and avoids adding a Python GitHub SDK.

### Models

Extend `RunCreateRequest` with optional PR metadata:

```text
source_pr_number: int | None = None
```

No separate workflow type is needed.

### Git Client / GitHub Client PR Creation

Update PR branch/title generation to use `source_pr_number` when present.

Manual runs keep the current run-id branch and title.

## Error Handling

- Unsupported webhook event: `200`, ignored.
- Wrong label: `200`, ignored.
- Invalid signature with configured secret: `401`.
- No eligible changed files: `200`, ignored.
- Failure to fetch changed files: `502` or an accepted run marked failed only if the run has already been created. Prefer failing before run creation.
- Workflow failures after run creation use existing run statuses: `agent_failed`, `tests_failed`, `pr_failed`, `completed_without_pr`.

## Testing

Add focused tests for:

- ignored non-PR events
- ignored wrong label
- accepted `pull_request.labeled` with `generate-tests`
- changed-file filtering
- invalid signature when `GITHUB_WEBHOOK_SECRET` is configured
- PR branch/title behavior for webhook runs
- existing manual API PR behavior remains unchanged

Live GitHub webhook delivery and live PR creation remain manual demo paths.

## Out Of Scope

- CI auto-heal.
- GitHub Actions polling loop.
- webhook delivery dedupe table.
- GitHub App installation auth.
- pushing commits directly to the developer's PR branch.
- non-Python test generation.
