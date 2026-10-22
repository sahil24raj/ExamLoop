---
doc: checklist
status: approved
---

# Build Checklist

Build mode: fast

## Slices

- [x] **1. Project Scaffolding and Authentication Setup**
  Becomes usable: Clean Next.js 14 frontend and FastAPI backend communicating with Supabase Auth session tokens.
  Why now: Establishes base architecture, secure headers, and user isolation from day one.
  PRD ref: `prd.md > The Core Journey` (Step 1)
  Spec ref: `spec.md > Stack`, `spec.md > File Structure`
  Build: Scaffold Next.js frontend with Tailwind CSS and FastAPI backend with SQLAlchemy and Supabase JWT middleware.
  Verify (mechanical): Automated tests for auth token decode and route protection.
  Learner check: Log in and see protected dashboard.
  Commit: `feat(auth): initialize full-stack scaffold and supabase auth integration`

- [x] **2. Subject Creation and Study Material Ingestion**
  Becomes usable: Users can create subjects and upload PDF/DOCX course documents.
  Why now: The test generation engine requires course documents and topics to operate on.
  PRD ref: `prd.md > Features and Behavior` (Section 1)
  Spec ref: `spec.md > Document Ingestion`
  Build: Implemented document parsers (PyPDF2/pdfplumber/docx) and automatic topic extraction.
  Verify (mechanical): Upload sample syllabus, verify extracted topics in database.
  Learner check: Upload lecture notes and see extracted topic badges appear immediately.
  Commit: `feat(materials): document parser and topic extraction pipeline`

- [x] **3. Adaptive Test Builder and LLM Question Generation**
  Becomes usable: Users can configure custom parameters (MCQ/Subjective, count, difficulty) and generate tests.
  Why now: Core product capability that creates practice value for the student.
  PRD ref: `prd.md > Features and Behavior` (Section 2)
  Spec ref: `spec.md > Components` (TestBuilderModal)
  Build: Integrated Groq/OpenAI JSON schema prompt pipelines generating structured question sets.
  Verify (mechanical): Automated test verifying prompt schema and question model persistence.
  Learner check: Click generate and see a test created in under 5 seconds.
  Commit: `feat(tests): ai-powered test generation engine`

- [x] **4. Distraction-Free Test Runner Interface**
  Becomes usable: Interactive, timed test interface with autosave, question navigator, and submission handler.
  Why now: Provides realistic exam pressure and seamless test-taking experience.
  PRD ref: `prd.md > Screens and Layout` (Test Taking Screen)
  Spec ref: `spec.md > Components` (TestRunner)
  Build: Built question stepper, countdown timer, radio options, essay textareas, and progress indicators.
  Verify (mechanical): Tested answer capture and submission payload verification.
  Learner check: Take a 5-question test and submit answers.
  Commit: `feat(ui): interactive timed test runner with autosave`

- [x] **5. AI-Powered Evaluation Engine and Detailed Results Dashboard**
  Becomes usable: Instant scoring out of 10, rubric breakdown, mistake critique, and persistent performance history.
  Why now: Closes the feedback loop by teaching the student why they were wrong and how to improve.
  PRD ref: `prd.md > Features and Behavior` (Section 3)
  Spec ref: `spec.md > Results & Evaluation Screen`
  Build: Built LLM rubric grading pipeline and visual results dashboard with score meters.
  Verify (mechanical): Tested grading calculations and feedback rendering.
  Learner check: Review submitted test and see score, explanations, and coaching recommendations.
  Commit: `feat(evaluation): automated ai grading and diagnostic report card`

## Hands-on Checkpoints

- [x] Early usable behavior explored — Document ingestion and topic badges verified on live sample PDFs.
- [x] Final kick-the-tires exploration and feedback completed — Full journey from login to retesting verified.

## Final Review

- [x] Final review complete — Token verification fixed for asymmetric ES256/RS256 algorithms and material ingestion speed optimized.

## Code Tour and App Map

- [x] Learning activity complete — Guided route through frontend component tree, FastAPI routing, and AI prompt pipeline.
- [x] Optional edit and transfer reflection addressed — Verified environment variable fallbacks and JWT verification.
- [x] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse.

Activity and evidence: End-to-end audit and verification from frontend `app/` through backend `routers/` to database and AI services.
Route and stops:
  - Stop 1: `frontend/src/components/TestBuilderModal.tsx`
  - Stop 2: `backend/app/services/ai_service.py`
  - Stop 3: `backend/app/routers/tests.py`
  - Stop 4: `frontend/src/app/results/[id]/page.tsx`
Edit outcome: Fixed JWT JWKS multi-algorithm token validation in `backend/app/dependencies.py` and optimized material ingestion in `backend/app/routers/materials.py`.
Reflection: Handled in ignored profile.
Activity mode: Live app and editor code walkthrough.

## Revisions
- Optimized material ingestion speed — Chunks text during upload rather than blocking API response.
- Asymmetric JWT token support — Added dynamic JWKS fetching for Supabase ES256/RS256 tokens.
