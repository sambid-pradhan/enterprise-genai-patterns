# AI Test Generation Pipeline

Durable AI coding workflow demo inspired by Duolingo's AI unit test generation pipeline.

## What It Does

```text
POST /runs
  -> DBOS workflow
  -> clone bundled sample repo or Git URL
  -> run Codex CLI
  -> run pytest
  -> store generated diff and pytest output
  -> optionally create a GitHub PR
```

## Setup

Copy the environment file:

```powershell
Copy-Item .env.example .env
```

Set `OPENROUTER_API_KEY` in `.env` so the Codex CLI inside the app container can call OpenRouter.
The repo includes `.codex/config.toml`, and Docker Compose mounts it at `/workspace/.codex`.

Start the services:

```powershell
docker compose up --build
```

## Local Demo

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/runs -ContentType "application/json" -Body '{"repo_url":"sample","target_paths":["src/sample_app/calculator.py"],"create_pr":false}'
```

Fetch a run:

```powershell
Invoke-RestMethod -Method Get -Uri http://localhost:8000/runs/<run_id>
```

## Optional PR Mode

Set `create_pr=true` only for a real GitHub repository and a worker environment where `gh` is authenticated.

PR creation is skipped for the bundled sample repo unless it has a real GitHub remote.

## GitHub Label Webhook Demo

Iteration 2 supports a GitHub label trigger:

```text
pull_request.labeled(generate-tests)
  -> POST /webhooks/github
  -> changed Python files become target_paths
  -> existing DBOS workflow runs
  -> AI branch ai-tests/pr-<number>
  -> separate AI PR
```

Set `GITHUB_WEBHOOK_SECRET` in `.env` for signed GitHub deliveries. If the value is empty, unsigned local webhook requests are accepted for demo use.

Configure a GitHub webhook:

```text
Payload URL: https://<your-ngrok-host>/webhooks/github
Content type: application/json
Secret: same value as GITHUB_WEBHOOK_SECRET
Event: Pull requests
```

Demo:

1. Open a pull request.
2. Add the label `generate-tests`.
3. Fetch the created run through `GET /runs/{id}`.
4. Inspect `pr_url` and `ci_status`.

## Out Of Scope In Iteration 1

- GitHub webhooks
- Retry loops
- CI polling
- Multi-agent provider abstraction
- Scheduled backfill
