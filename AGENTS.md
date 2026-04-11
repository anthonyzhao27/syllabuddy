# Repository Guidelines

## Project Structure & Module Organization
`frontend/` holds the Next.js 16 app: routes in `src/app/`, reusable UI in `src/components/`, browser helpers in `src/lib/`, shared state in `src/contexts/`, and colocated `*.test.ts(x)` files. `backend/` holds the FastAPI API: `app/routers/` for endpoints, `app/services/` for parsing, calendar, storage, and SMS logic, `app/models/` for schemas and DB helpers, and `tests/` for pytest coverage. `supabase/migrations/` stores schema changes; `docs/` stores planning notes.

## Build, Test, and Development Commands
Frontend:
- `cd frontend && npm run dev` starts Next.js locally.
- `cd frontend && npm run build` validates the production build.
- `cd frontend && npm run lint && npm run typecheck` runs ESLint and TypeScript checks.
- `cd frontend && npm run test:run` runs Vitest once.

Backend:
- `cd backend && python3 -m venv .venv && source .venv/bin/activate` creates the local virtualenv.
- `cd backend && python -m pip install -e ".[dev]"` installs app and dev dependencies.
- `cd backend && python -m uvicorn app.main:app --reload` starts FastAPI locally.
- `cd backend && python -m pytest` runs the backend test suite.
- `cd backend && python -m black app tests && python -m flake8 app tests` formats and lints Python code.

## Coding Style & Naming Conventions
Use 2 spaces in TypeScript/TSX and 4 in Python. Frontend files are generally kebab-case (`upload-form.tsx`); Python modules use snake_case (`google_calendar.py`). Use PascalCase for React components, camelCase for TypeScript helpers, and the existing `@/` alias for frontend imports. Keep FastAPI routers thin and move business logic into `backend/app/services/`. Black uses an 88-character line length.

## Testing Guidelines
Frontend tests use Vitest with Testing Library and `jsdom`; colocate them as `*.test.ts` or `*.test.tsx`. Backend tests live in `backend/tests/` as `test_*.py`. No coverage gate is configured, so add or update tests for every behavior change, especially routes, parsing services, auth flows, and calendar exports.

## Commit & Pull Request Guidelines
History mixes sentence-case commits with conventional prefixes, but `feat:`, `fix:`, and `chore:` are the clearest baseline and match branch names like `feat/...` and `fix/...`. Keep commits scoped to one change. PRs should summarize user-facing impact, note frontend/backend/Supabase touchpoints, link the issue when applicable, and include screenshots for UI changes. Call out new env vars, migrations, or API contract changes explicitly.

## Security & Configuration Tips
Never commit secrets from `backend/.env`, `frontend/.env.local`, or `.env.production`. Put schema changes in `supabase/migrations/` instead of ad hoc SQL.
