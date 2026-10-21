# ExamLoop — End-to-End Verification & Repair PRD

## 1. Mission

Audit, run, test, and repair the existing ExamLoop application until its
core user journey works end to end.

Work on the existing implementation.
Do not rebuild the app or replace working functionality.

Use a bounded, evidence-driven execution loop:

Inspect → Reproduce → Implement → Verify → Record → Repeat

A completed screen is not proof of a completed feature.
A successful API response is not proof of a working user journey.
A mocked test is not proof of successful live AI integration.

---

## 2. Product Definition

ExamLoop turns uploaded study material into reusable, personalized
mock-test practice.

Core journey:

1. Upload study material.
2. Extract and review topics.
3. Select objective or subjective test.
4. Choose question count and difficulty.
5. Select suggested topics, select all, or enter a supported topic.
6. Generate a mock test.
7. Answer questions.
8. Submit the attempt.
9. Receive evaluation and a score out of 10.
10. View the saved test in My Mock Tests.
11. Generate another fresh test from the same material.

The application must remain fully dark themed, using its current
black/green brand direction.

---

## 3. Execution Authority and Boundaries

Allowed:
- Inspect the repository.
- Run local services and automated checks.
- Create isolated test fixtures and test accounts.
- Fix frontend/backend integration defects.
- Repair broken business logic required by this PRD.
- Add regression tests.
- Update documentation.
- Add safe, necessary migrations.

Not allowed without explicit approval:
- Production deployments.
- Purchases or paid-service provisioning.
- Destructive database resets.
- Deleting real user documents or attempts.
- Changing production secrets.
- Publishing repositories.
- Replacing the technology stack.
- Removing features to make tests pass.
- Weakening authentication or validation.
- Unlimited paid API calls.

Preserve unrelated user changes.
Never print secrets or commit credentials.

---

## 4. Required Initial Audit

Before implementation:

- Read this PRD.
- Inspect repository instructions and available skills.
- Inspect existing frontend, backend, database, migrations, and tests.
- Identify documented startup commands.
- Identify actual environment variables from code.
- Identify live AI and demo-mode behavior.
- Check repository status and preserve unrelated modifications.
- Start the app using its existing setup where possible.
- Run available baseline checks.

Create:

- `TASKS.md` — acceptance criteria and actionable tasks.
- `PROGRESS.md` — append-only iteration log.
- `TEST_REPORT.md` — commands, scenarios, evidence, and final status.

Do not invent startup commands or environment variable names.

---

## 5. Ralph-Style Execution Loop

### 5.1 Loop Rules

For each iteration:

1. Read the latest TASKS.md and PROGRESS.md.
2. Select the highest-priority failing acceptance criterion.
3. Reproduce the failure.
4. Record the expected and actual behavior.
5. Identify the smallest coherent fix.
6. Implement the fix.
7. Add or update a regression test.
8. Run targeted checks.
9. Recheck the affected user flow.
10. Record evidence and update task status.
11. Continue to the next failing criterion.

Do not repeatedly redesign already working areas.
Do not mark tasks complete based only on code inspection.

### 5.2 Iteration Record

Append this structure to PROGRESS.md:

- Iteration:
- Acceptance criterion:
- Reproduction:
- Root cause:
- Changes:
- Checks executed:
- Actual result:
- Remaining risk/blocker:
- Next action:

Keep entries concise and factual.
Do not record private chain-of-thought.

### 5.3 Bounded Execution

Default maximum: 12 iterations per execution session.

If the same problem fails after three materially different attempts:
- Stop retrying that approach.
- Record the blocker and attempted fixes.
- Continue with independent tasks if safe.
- Ask for the specific missing input if required.

Do not create an infinite retry loop.

This document defines execution behavior; it does not itself install
or configure an external autonomous-loop runner.

### 5.4 Completion Signal

Emit:

<promise>EXAMLOOP_E2E_VERIFIED</promise>

ONLY when all mandatory acceptance criteria pass, including the live
integration check.

If credentials, tooling, budget, or infrastructure prevent verification,
do not emit the completion signal.

Report PARTIALLY VERIFIED or BLOCKED instead.

---

## 6. Acceptance-Criteria Statuses

Every criterion must have exactly one status:

- NOT TESTED
- PASS
- FAIL
- BLOCKED

A PASS requires executed evidence.

A BLOCKED result must include:
- Missing prerequisite.
- Exact scenario that could not run.
- What was verified independently.
- Required next action.

Do not count BLOCKED as PASS.

---

## 7. Functional Acceptance Criteria

### AC-01: Application Startup

- Frontend starts using documented commands.
- Backend starts using documented commands.
- Required database connections work.
- Existing migrations run safely.
- Main routes load.
- No critical browser/runtime errors.

Evidence:
Startup commands, health checks, route checks.

### AC-02: Upload Study Material

- User-facing upload heading says “Upload study material”.
- Supported searchable PDF and TXT uploads work.
- Supported file types match actual parser capabilities.
- Processing states are visible.
- Extracted content is persisted.
- PDF page references are preserved.
- Invalid, empty, oversized, and unsupported files fail helpfully.
- Image-only PDFs are handled honestly.
- Refresh does not lose processed materials.

Evidence:
Valid PDF, valid TXT, invalid file, empty file, refresh check.

### AC-03: Topic Extraction

- Topics come from the current material collection.
- Topic names are non-empty and usable.
- Topics remain available after refresh.
- Priority suggestions do not invent exam weightage.
- Syllabus-only topic headings are not treated as answer evidence.
- No topics from another user's materials appear.

### AC-04: Topic Selection

- Select one topic.
- Select multiple topics.
- Select all.
- Clear selection.
- Enter a manual topic.
- Remove a manually entered topic.
- Unsupported manual topics receive a helpful explanation.
- No-topic selection prevents generation.
- Selections passed to the backend match the UI.

### AC-05: Test Configuration

- Objective and subjective modes work.
- Question count accepts valid positive integers.
- Invalid and excessive counts are rejected server-side.
- Easy, Medium, and Hard values persist correctly.
- Generated tests reflect the submitted configuration.
- Failed generation does not leave a misleading completed test.

### AC-06: Objective Generation

- Requested number of questions is generated.
- Each question has valid options.
- Exactly one correct option is stored.
- Questions match selected topics.
- Answer keys are absent from pre-submission API payloads.
- Duplicate questions are rejected.
- Generation failures have a retryable error state.

### AC-07: Subjective Generation

- Requested number of questions is generated.
- Each question has a reference answer.
- Each question has a persisted rubric before submission.
- Rubric marks sum to the question maximum.
- Questions match selected topics and difficulty.
- Source-grounded and syllabus-scoped modes are distinguished.

### AC-08: Attempt and Autosave

- MCQ answers can be selected and changed.
- Subjective answers preserve paragraphs.
- Draft answers persist.
- Refresh restores the attempt.
- Continue opens the same attempt.
- Unanswered questions remain identifiable.
- Submit confirmation works.
- Double-clicking submit does not create duplicate attempts.

### AC-09: Objective Scoring

- Application code performs scoring.
- Known correct answers receive correct marks.
- Known incorrect answers receive zero.
- Unanswered questions follow the documented rule.
- Repeated submissions do not change finalized results unexpectedly.

### AC-10: Subjective Evaluation

- Evaluation uses the saved rubric.
- Correct paraphrases can receive credit.
- Partial answers can receive partial credit.
- Blank answers are handled deterministically.
- Awarded marks stay within valid bounds.
- Feedback identifies missing points or misconceptions.
- Evidence references exist where claimed.
- Instructions inside an answer cannot override grading.
- Failed evaluation remains pending/failed, not a fake zero.
- Evaluation retry is safe and idempotent.

### AC-11: Score Out of 10

Calculate in application code:

normalized_score =
10 × total_awarded_raw_marks / total_possible_raw_marks

- Preserve raw marks.
- Display normalized score to one decimal place.
- Round only for presentation.
- Prevent division by zero.
- Do not average percentages when raw-mark weighting is intended.
- Incomplete evaluation is clearly labeled.
- Subjective results say they are AI-estimated practice scores.

Known-value test:
18 / 25 raw marks = 7.2 / 10.

### AC-12: My Mock Tests

- Generated tests are saved automatically.
- Correct material collection is attached.
- Status is accurate.
- Question count, type, difficulty, and date display correctly.
- Completed scores appear.
- Unfinished tests can be resumed.
- Results survive refresh and application restart.
- Another user cannot access the test.

### AC-13: Fresh Tests From Existing Material

- No re-upload is required.
- “Generate new test” creates a separate test.
- Previous tests remain unchanged.
- Exclusion history includes previously generated questions,
  not only submitted questions.
- Exact normalized duplicates are blocked.
- MCQ option shuffling does not bypass duplicate checks.
- Near-duplicate checks are executed and limitations documented.
- The same concept can receive a genuinely different question.
- Concurrent requests do not publish overlapping exact duplicates.

Test at least three small generated tests from one collection.

If fresh-question supply is insufficient:
- Do not silently repeat.
- Do not silently reduce the count.
- Explain the limitation.
- Suggest fewer questions, more topics, or more material.

Semantic uniqueness is best-effort; do not claim a perfect guarantee.

### AC-14: Ownership and Security

Using two isolated test users:

- User A cannot access User B's documents.
- User A cannot access User B's tests or results.
- Retrieval does not cross ownership boundaries.
- Source-file access enforces authorization.
- API keys are absent from client bundles and responses.
- Model output is rendered safely.
- Document/answer prompt injection cannot override system behavior.

If only local single-user mode exists:
- Document that limitation.
- Do not claim multi-user security verification.

### AC-15: Full Dark UI

Verify existing main routes and overlays:

- Dashboard.
- Study Materials.
- Upload.
- Topic selection.
- Test configuration.
- Test-taking.
- Results.
- My Mock Tests.
- Dialogs and dropdowns.
- Loading, empty, and error states.

Requirements:
- Consistent black/green theme.
- No unintended white panels.
- No obsolete purple-theme leftovers.
- Readable input and placeholder text.
- Visible keyboard focus.
- Clear selected and disabled states.
- No answer-writing obstruction from decorative elements.

### AC-16: Responsive Behavior

Check approximately:
- 390 px mobile.
- 768 px tablet.
- 1440 px desktop.

Verify:
- No horizontal overflow.
- No clipped actions.
- Usable navigation.
- Readable topic names.
- Comfortable answer fields.
- Accessible submit controls.
- Long answers and long filenames remain usable.

### AC-17: Recovery and Error Handling

Test:
- AI timeout.
- Invalid AI JSON.
- Provider rate limit.
- Backend unavailable.
- Upload parsing failure.
- Interrupted generation.
- Interrupted evaluation.

Requirements:
- Helpful error states.
- Bounded retries.
- No silent switch to demo data.
- No duplicate records on retry.
- Existing completed attempts remain intact.

---

## 8. Test Fixtures

Create isolated, original fixtures:

1. Small searchable DBMS PDF with page references.
2. Equivalent TXT notes.
3. Syllabus-only document.
4. Empty file.
5. Unsupported file.
6. Small material collection with limited question variety.
7. Known correct MCQ answers.
8. Correct, partial, incorrect, and blank subjective answers.
9. Prompt-injection text inside a document and student answer.

Never use real private student files as committed fixtures.

---

## 9. Three Verification Layers

### Layer A: Deterministic Tests

Use fixtures/mocks for:
- Parsing.
- Validation.
- Scoring.
- Persistence.
- Authorization.
- Duplicate detection.
- Retry behavior.

Default automated tests must not require paid AI calls.

### Layer B: Browser End-to-End

Use available browser automation to execute the real UI against the
running local backend.

Verify the actual DOM, navigation, visible states, and persistence.

Screenshots support visual evidence but do not replace assertions.

### Layer C: Live Integration Smoke Test

With valid credentials and an approved small API budget:

- Upload a small material fixture.
- Generate a small objective test.
- Generate a small subjective test.
- Submit a subjective answer.
- Verify live evaluation.
- Generate a follow-up test and check exclusions.

Use bounded call counts and retries.
Reuse successful outputs where appropriate.

Record:
- Provider/model identifier.
- Timestamp.
- Operation.
- Success/failure.
- Duration.
- Token usage if returned.

Do not log secrets or full private material.
Do not claim live verification if only mocks ran.

---

## 10. Required Full Journey

Execute this journey through the UI:

1.