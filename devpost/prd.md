---
doc: prd
status: approved
---

# ExamLoop — Product Requirements

ExamLoop turns uploaded study material into personalized, active mock-test practice with instant AI coaching and diagnostic evaluations.
Source: `scope.md > The Unique Kernel`, `scope.md > The Core Loop`.

## The Core Journey
1. **Arrival & Authentication**: Learner arrives at the clean, dark-mode landing page and signs in or signs up securely via Supabase Auth.
2. **Subject Workspace**: Learner creates or selects a subject (e.g., "Computer Networks" or "Organic Chemistry").
3. **Material Ingestion**: Learner uploads study material (PDF, DOCX, or pasted text). The backend ingests the material, parses text, and automatically extracts key syllabus topics.
4. **Test Configuration**: Learner clicks "Build Mock Test", choosing:
   - Question Type: Objective (MCQ) or Subjective (Free response).
   - Question Count: 5, 10, or 15 questions.
   - Difficulty Level: Easy, Medium, or Hard.
   - Topic Scope: Select all extracted topics or pick specific focus areas.
5. **Test Generation**: The AI engine crafts custom questions, options/rubrics, and stores the test.
6. **Active Test Taking**: Learner completes the test under timed conditions with a progress bar, question navigator, and autosaved answers.
7. **Instant Evaluation**: Upon submission, the LLM evaluates all responses, scores the test out of 10, highlights misconceptions, and generates strengths and improvement tips.
8. **Review & Retest**: The test attempt is archived under "My Mock Tests" and the learner can instantly generate a targeted follow-up test.

## Screens and Layout
- **Landing / Auth Screen**: Brand introduction, quick sign-in/up modal, feature highlights.
- **Subjects Dashboard (`/dashboard`)**: Grid of active subjects, quick stats (tests completed, average score, total materials).
- **Subject Detail Page (`/subjects/[id]`)**:
  - Left panel: Uploaded materials list & topic tag cloud.
  - Center/Right: "Generate Test" action card and historical tests table.
- **Test Taking Screen (`/tests/[id]`)**: Full-screen distraction-free layout with remaining timer, question card, option selectors / textarea, and Next/Previous navigation.
- **Results & Evaluation Screen (`/results/[id]`)**: Score hero card (Score/10), breakdown radar/progress, question-by-question review with ideal answers and feedback notes.

## Look and Feel
- **Visual Theme**: Cohesive dark theme (`#09090b` zinc background, `#18181b` card surfaces).
- **Accents**: Neon Emerald green (`#10b981`) for correct answers, action buttons, and progress meters; Rose red (`#f43f5e`) for mistakes.
- **Typography**: Inter / sans-serif with crisp hierarchy, high contrast for long study sessions.
- **Density**: Calm, focused, uncluttered, with clear visual breathing room.

## Features and Behavior

### 1. Document Ingestion & Topic Extraction
- Ingests PDF and DOCX files securely.
- Chunks and sanitizes text before topic modeling.
- Returns clean topic badges allowing one-click selection.

### 2. Adaptive Mock Test Builder
- **Objective (MCQs)**: 4 options per question, single correct choice, randomized order, explanation attached.
- **Subjective**: Conceptual questions requiring paragraph answers, graded against ideal answer rubrics and key conceptual markers.
- Time limit dynamically calculated based on question count and difficulty.

### 3. Comprehensive Evaluation Engine
- Evaluates answers using Groq / OpenAI LLM prompts with strict JSON schemas.
- Outputs an overall score out of 10.
- Itemized feedback:
  - Is correct? (for MCQs) or Score awarded (for subjective).
  - Why the chosen option was correct/incorrect.
  - Actionable advice for subsequent study sessions.

## States and Boundaries
- **Empty State**: New subjects prompt clear drag-and-drop file upload.
- **Loading State**: Smooth pulse skeletons during AI test generation and evaluation.
- **In-Progress State**: Answers cached in local state so accidental browser refreshes do not lose student input.
- **Completed State**: Permanent record in PostgreSQL database linked to learner's user ID.

## Product Decisions
- **Supabase Auth with JWT**: Chosen for frictionless user management with enterprise-grade token security.
- **FastAPI + Async Python Backend**: Ensures sub-second response times and non-blocking LLM calls.
- **Dark Mode Default**: Reduces eye strain during intense late-night study sessions.

## What We're Building
A production-ready full-stack web application featuring authenticated workspaces, multi-format file ingestion, custom test generation, real-time testing interface, and AI-powered evaluation with persistent dashboards.

## Deferred From the POC
- Collaborative peer study rooms.
- Native iOS/Android apps.
- PDF export of graded report cards.

## Non-Goals
- Generic chatbots with unstructured chit-chat.
- Replacing official teacher grading or high-stakes proctoring.
