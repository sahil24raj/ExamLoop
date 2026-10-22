---
doc: spec
status: approved
---

# ExamLoop — Technical Specification

## How This Works, In Plain Language
ExamLoop is built with a modern decoupled full-stack architecture:
- A responsive **Next.js 14 frontend** provides a fast, interactive single-page experience.
- A **FastAPI Python backend** handles file processing, text extraction, database transactions, and LLM orchestration.
- **Supabase** provides managed PostgreSQL database storage and secure user authentication via JSON Web Tokens (JWT).
- High-speed **Groq / OpenAI LLM APIs** generate structured questions and evaluate learner submissions in real-time.

## The Core Journey Through the System
1. User authenticates via Supabase Auth in Next.js frontend; the bearer JWT is sent in the `Authorization` header to the FastAPI backend.
2. User uploads PDF/DOCX to `/api/materials/upload`; backend parses text, extracts syllabus topics, and writes material metadata to PostgreSQL.
3. User clicks "Generate Test"; backend receives parameters at `/api/tests/generate`, constructs a strict prompt for the LLM, parses the returned JSON schema, and stores the test questions in PostgreSQL.
4. User opens `/tests/[id]`, answers questions against the timer, and hits Submit.
5. Frontend POSTs answers to `/api/tests/[id]/submit`; backend calls the AI Evaluation Service, compares answers against rubrics, assigns a score out of 10 with feedback, and stores the test attempt.
6. Frontend redirects to `/results/[id]`, displaying instant feedback, explanations, and radar metrics.

## Stack
- **Frontend Framework**: Next.js 14 (App Router), React 18, TypeScript.
- **Styling**: Tailwind CSS with custom emerald theme variables, Lucide React icons.
- **Backend Framework**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2.
- **Database & Auth**: PostgreSQL managed via Supabase, SQLAlchemy ORM, Supabase Auth (JWT with ES256/RS256 JWKS verification).
- **Document Ingestion**: PyPDF2, pdfplumber, python-docx.
- **AI / LLM Engine**: Groq API (LLaMA-3.3-70B-Versatile) / OpenAI (GPT-4o-mini).

## Where It Runs and How Someone Tries It
- **Frontend Local Run**:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
  Runs at: `http://localhost:3000`
- **Backend Local Run**:
  ```bash
  cd backend
  python -m venv venv
  .\venv\Scripts\activate   # Windows
  pip install -r requirements.txt
  uvicorn app.main:app --reload --port 8000
  ```
  API Docs at: `http://localhost:8000/docs`
- **Live Deployment**:
  - Frontend: Hosted on **Vercel**
  - Backend: Hosted on **Render**

## Look and Feel
- Primary background: `#09090b` (Deep dark zinc)
- Card / Panel background: `#18181b`
- Brand Accent: `#10b981` (Emerald green) & `#059669`
- Text hierarchy: `#f4f4f5` (Heading white), `#a1a1aa` (Subtext muted zinc)
- Error / Warning: `#ef4444` (Rose red)

## Components
- `Navbar`: Displays brand, active user status, theme controls, and logout.
- `SubjectCard`: Renders subject stats, material count, and direct link.
- `MaterialUploader`: Drag-and-drop file ingestion zone with progress feedback.
- `TestBuilderModal`: Modal with sliders and toggles for question type, count, difficulty, and topics.
- `TestRunner`: Timed question stepper with radio options, text area, and review palette.
- `ResultCard`: Visual score circular meter, performance breakdown, and itemized critique.

## File Structure
```
ExamLoop/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── subjects/[id]/page.tsx
│   │   │   ├── tests/[id]/page.tsx
│   │   │   └── results/[id]/page.tsx
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   ├── TestBuilderModal.tsx
│   │   │   └── ...
│   │   └── lib/
│   │       ├── api.ts
│   │       └── supabase.ts
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── subjects.py
│   │   │   ├── materials.py
│   │   │   └── tests.py
│   │   ├── services/
│   │   │   ├── ai_service.py
│   │   │   ├── document_parser.py
│   │   │   └── grading_service.py
│   │   ├── models/
│   │   └── database.py
│   ├── requirements.txt
│   └── main.py
├── devpost/
│   ├── scope.md
│   ├── prd.md
│   ├── spec.md
│   ├── checklist.md
│   └── app-map.html
└── README.md
```

## External Services and Dependencies
- **Supabase**: Managed PostgreSQL and Auth (`https://api.supabase.com`).
- **Groq API**: Low-latency LLM inference (`https://api.groq.com/openai/v1`).
- **OpenAI API**: Fallback high-fidelity evaluation (`https://api.openai.com/v1`).

## Important Failure Modes
- **Invalid JWT Token**: If Supabase rotates asymmetric keys or token expires, the backend returns HTTP 401 and frontend redirects to login.
- **Corrupted Document Upload**: If a PDF is unreadable, parser catches exception and prompts user to paste text directly.
- **AI Rate Limit**: If LLM provider returns 429, backend falls back gracefully to backup model or cached evaluation retry.
