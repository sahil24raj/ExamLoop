# Devpost Hackathon Submission Guide — Build With AI: Basics

Use this document to quickly fill out the official submission form on **[learn-ai-basics.devpost.com](https://learn-ai-basics.devpost.com/)**.

---

## 1. Project Title & Tagline

- **Project Title**: `ExamLoop — A Personal AI Exam Coach`
- **Elevator Pitch / Tagline**: `Turn any lecture notes, syllabus, or course PDFs into interactive, personalized mock tests with instant AI grading and feedback loops.`

---

## 2. Submission Form Answers

### Inspiration
Students spend countless hours passively highlighting textbooks and reading slides, only to freeze when confronting actual exam questions. We wanted to build a tool that replaces passive reading with the Feynman technique and active recall: taking what you've studied, immediately testing yourself under timed exam conditions, and getting constructive, rubric-level coaching on your mistakes.

### What it does
ExamLoop turns uploaded course notes into personalized, interactive exam simulations:
1. **Material Ingestion**: Upload course PDFs or DOCX files; ExamLoop automatically extracts key syllabus topics.
2. **Flexible Test Builder**: Choose between Objective (MCQ) or Subjective (Free response) tests, set difficulty levels (Easy, Medium, Hard), and select topic coverage.
3. **Timed Test Runner**: Take tests in a distraction-free dark interface with live countdown timers, question navigation, and autosave.
4. **Diagnostic AI Grading**: Submissions are graded instantly with a score out of 10, itemized explanations for every answer, and actionable coaching tips to reinforce weak areas.
5. **The Exam Loop**: History is saved so you can track your progress over time and re-test on specific gaps.

### How we built it
- **Planning & Curriculum**: Followed the official Devpost Learn AI Basics curriculum (`1-start` through `6-ship`), establishing formal Scope, PRD, Technical Spec, and Build Checklists before writing code.
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide icons, styled in a sleek dark theme with emerald green accents.
- **Backend**: FastAPI (Python 3.11+), Pydantic v2 schemas, async route handlers, PyPDF/pdfplumber for document parsing.
- **Database & Auth**: PostgreSQL managed via Supabase, with custom JWT token verification supporting asymmetric ES256/RS256 JWKS algorithms.
- **AI & Evaluation**: Groq API (LLaMA-3.3-70B-Versatile) and OpenAI for structured test generation and rubric scoring.
- **Deployment**: Vercel (Frontend) and Render (Backend).

### Challenges we ran into
- Handling asymmetric Supabase Auth JWT verification in FastAPI: We solved this by implementing dynamic remote JWKS fetching supporting both ES256 and RS256 algorithms.
- Speed of document ingestion: Parsing large multi-page PDFs was causing UI latency. We restructured the extraction pipeline to chunk text efficiently and return discovered topic tags within seconds.
- JSON schema stability: Ensuring LLM responses always adhered strictly to typed Pydantic structures for both 4-option MCQs and subjective grading rubrics.

### Accomplishments that we're proud of
- Delivering a complete, cohesive end-to-end loop: from raw PDF to live test to graded report card in seconds.
- Adhering to spec-driven development where every slice was planned, verified, and checked off.
- Creating an intuitive, distraction-free user interface designed specifically for students under exam pressure.

### What we learned
- The power of planning-first: Spending time defining the POC boundary in `scope.md` and `prd.md` prevented scope creep and kept the project deliverable.
- Structured output enforcement in AI engineering: Prompting with schema contracts is vastly superior to parsing unstructured text.

### What's next for ExamLoop
- Spaced repetition calendar scheduling to prompt students right before memory decay occurs.
- Voice-based oral exam coaching for viva and interview preparation.
- Collaborative study groups and teacher dashboards for automated classroom quiz generation.

---

## 3. Required Links for Devpost Form

- **Public GitHub Repository**:
  `https://github.com/sahil24raj/Examloop-a-personal-exam-coach`
  *(Also available at: `https://github.com/sahil24raj/ExamLoop`)*
- **Demo Video URL**:
  *(Record a 1–3 minute walkthrough showing: (1) Logging in, (2) Uploading a document & topic extraction, (3) Generating a mock test, (4) Answering questions with timer, (5) Viewing instant score/feedback out of 10. Upload to YouTube / Loom / Google Drive as unlisted / public).*
- **Live Demo (Optional)**:
  `https://examloop.vercel.app` (or your deployed Vercel URL)
- **Built With**:
  `next.js`, `react`, `typescript`, `python`, `fastapi`, `supabase`, `postgresql`, `tailwind-css`, `groq`, `openai`

---

## 4. Exit Survey Tips

- **How was your experience with AI coding tools?**: Share your honest thoughts on pair programming with AI agents, using planning-first skills (`SKILL.md`), and using spec-driven development.
- **Did you complete your project?**: Yes, fully functional proof-of-concept tested end-to-end.
