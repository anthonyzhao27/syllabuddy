# CLAUDE.md

## Project Overview

Syllabus parser — a web app that extracts assignments/due dates from course syllabi, exports to calendars, and sends AI friend-style SMS reminders. See `OVERVIEW.md` for full details.

## Tech Stack

- **Frontend:** Next.js (App Router) with TypeScript
- **Backend:** FastAPI (Python)
- **Database / Auth:** Supabase
- **AI / LLM:** OpenAI API
- **Text Extraction:** PyMuPDF / pdfplumber / python-docx
- **SMS:** Twilio
- **Testing:** pytest (backend), Next.js built-in (frontend)

## Project Structure

Monorepo with `frontend/` and `backend/` as sibling directories. See OVERVIEW.md for full tree.

## Commands

### Frontend

```bash
cd frontend
npm install        # install dependencies
npm run dev        # start dev server
npm run lint       # lint
npm run build      # production build
```

### Backend

```bash
cd backend
pip install -e ".[dev]"                    # install dependencies
uvicorn app.main:app --reload              # start dev server
black app/ tests/                          # format
flake8 app/ tests/                         # lint
pytest                                     # run tests
```

## Code Style & Conventions

### General
- **File names:** kebab-case (e.g., `upload-form.tsx`, `google_docs.py` follows Python convention)
- **TypeScript:** camelCase for variables/functions, PascalCase for components/types
- **Python:** snake_case for variables/functions/files

### Frontend
- Use **named exports** (no default exports)
- Lint with `npm run lint`
- Next.js App Router — pages in `src/app/`, components in `src/components/`

### Backend
- Format with **Black**, lint with **flake8**
- Relaxed typing — type hints appreciated but not strict
- Routers stay thin; business logic goes in `services/`
- Pydantic models in `models/schemas.py`
- LLM prompt templates in `utils/prompts.py`

## Testing

- **Test extensively** — all API endpoints and services should have test coverage
- Backend: pytest in `backend/tests/`
- Frontend: tests alongside components or in a `__tests__/` directory

## Git Workflow

- **Branch naming:** `feature/`, `fix/`, `chore/` prefixes
- **Commits:** casual style, no strict format required
- Monorepo — all changes in one repo

## Rules for Claude

- **Do NOT refactor code that wasn't asked about.** Stay focused on the requested change.
- **Always ask before creating new files.** Propose the file and its purpose first.
- **Always ask before making architectural decisions.** Never assume — present options and let me choose.
- **Check `OVERVIEW.md` for project scope** when unsure if a feature is in MVP or post-MVP.
- **If `OVERVIEW.md` has inline notes/comments from me**, integrate them when asked.
