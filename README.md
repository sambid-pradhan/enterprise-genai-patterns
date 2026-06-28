# genai-at-scale

Minimal monorepo scaffold for a local MVP with separate `frontend/` and `backend/` apps.

## Layout

- `frontend/`: UI app
- `backend/`: API app
- `docker-compose.yml`: local Postgres plus both apps
- `.env.example`: shared local environment defaults

## Getting started

1. Copy `.env.example` to `.env` and adjust values if needed.
2. Install the workspace dependencies from the repository root.
3. Run the frontend and backend from their own folders, or use Docker Compose once you want the full stack together.

## Notes

- The root is intentionally small and workspace-friendly.
- `pnpm-workspace.yaml` and the root `package.json` are set up for `frontend/` and `backend/` packages.
- No application code lives at the root.
- The frontend proxies chat requests through `frontend/src/app/api/chat/route.ts` to the backend API.
