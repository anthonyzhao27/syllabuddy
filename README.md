# Syllabus Parser

A web app that extracts assignments and due dates from course syllabi, exports them to your calendar, and sends AI friend-style SMS reminders before deadlines.

## Project Structure

```
syllabus-parser/
├── CLAUDE.md
├── OVERVIEW.md
├── README.md
│
├── frontend/                          # Next.js App Router + TypeScript
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── .env.local.example
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx               # Upload/paste landing page
│   │   │   └── results/
│   │   │       └── page.tsx           # Parsed events review + export
│   │   ├── components/
│   │   │   ├── upload-form.tsx
│   │   │   ├── event-list.tsx
│   │   │   └── export-buttons.tsx
│   │   ├── lib/
│   │   │   ├── supabase.ts
│   │   │   ├── api.ts
│   │   │   └── calendar.ts           # .ics generation (client-side)
│   │   └── types/
│   │       └── index.ts
│   └── tailwind.config.ts
│
├── backend/                           # FastAPI + Python
│   ├── pyproject.toml
│   ├── .env.example
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/
│   │   │   ├── parse.py               # POST /parse
│   │   │   ├── export.py              # POST /export
│   │   │   └── reminders.py           # POST /reminders
│   │   ├── services/
│   │   │   ├── extraction.py          # PyMuPDF / pdfplumber / python-docx / HTML
│   │   │   ├── google_docs.py
│   │   │   ├── llm.py                 # OpenAI structured extraction
│   │   │   ├── calendar.py
│   │   │   └── sms.py                 # Twilio + AI friend style
│   │   ├── models/
│   │   │   ├── schemas.py             # Pydantic models
│   │   │   └── db.py                  # Supabase helpers
│   │   └── utils/
│   │       └── prompts.py             # LLM prompt templates
│   └── tests/
│       ├── test_extraction.py
│       └── test_llm.py
│
└── .github/
    └── workflows/
        └── ci.yml
```

## Getting Started

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```
