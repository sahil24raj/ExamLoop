---
doc: scope
status: approved
---

# ExamLoop

A personal AI exam coach that turns uploaded course notes into personalized, interactive mock-test practice with instant diagnostic feedback.

## The Unique Kernel
The closed-loop exam engine: ExamLoop doesn't just ask AI for questions; it extracts syllabus topics from learner notes, generates realistic objective/subjective tests calibrated by difficulty, scores attempts with granular rubric evaluation (out of 10), diagnoses exact conceptual blindspots, and lets the learner immediately retest on their weaknesses.

## Who It's For
Students and self-learners facing upcoming exams who have mountains of notes/PDFs and don't know if they are truly prepared. Today, they re-read notes passively or guess what might be asked; ExamLoop gives them active, quantified exam simulations.

## The Core Loop
1. Upload course material (PDF, DOCX, or text).
2. Review extracted topics & select exam parameters (Objective / Subjective, question count, difficulty).
3. Take the timed mock test in a distraction-free interface.
4. Submit and get an instant score (out of 10), topic breakdown, and actionable coaching guidance.
5. Loop back to retest missed concepts with fresh generated questions.

## Inspiration & Identity
- **Aesthetic**: Deep dark mode (`#0a0a0a` / `#121212`) accented with focused emerald green (`#10b981`).
- **Tone**: Focused, motivating, calm, and rigorous—like having a personal tutor sitting next to you.
- **References**: Linear-like clean typography, Quizlet's active recall speed, and Coursera's structured rubric feedback.

## Why This Matters to the Learner
Students spend 80% of study time in passive reading which leads to blanking out in exams. Active test generation with instant constructive feedback turns anxiety into measurable confidence.

## What "Working" Looks Like
A user signs in, creates a subject, uploads a study document, selects topics, takes a 5-question test with timer, submits answers, and receives an evaluated report card with score, detailed critique for every answer, and strengths/weaknesses breakdown stored in their history.

## The POC Boundary
- **In**: Document upload & text extraction, topic discovery, test builder (MCQ & subjective), test-taking runner with autosave & timer, LLM evaluation engine with score/10, performance dashboard with history.
- **Out for POC**: Multi-user live multiplayer competitions, handwritten OCR scanning, automated payment gateways.

## Later
- Spaced-repetition calendar scheduling.
- Class-wide teacher portals and automated assignment grading.
- Voice-based oral exam simulations.

## Explicitly Cut
- Complex subscription billing — to keep the hackathon PoC accessible and focused on core learning velocity.
- Native mobile app wrapper — responsive mobile web in Next.js is sufficient and faster to iterate.
