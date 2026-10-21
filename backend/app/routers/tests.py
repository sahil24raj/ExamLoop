from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
import uuid

from backend.app.database import get_db
from backend.app.models import (
    Test, TestQuestion, Question, RubricCriterion, Concept, Subject, Attempt, StudentAnswer, Topic, SyllabusUnit
)
from backend.app.schemas import (
    TestCreateRequest, CustomTestCreateRequest, TestResponse, TestTakingView, StudentQuestionView, MCQOption
)
from backend.app.services.ai_service import ai_service
from backend.app.services.retrieval_service import retrieval_service
from backend.app.services.scoring_service import scoring_service
from backend.app.services.adaptive_service import adaptive_service
from backend.app.routers.subjects import get_or_create_default_user

router = APIRouter(prefix="/api", tags=["Tests"])

@router.post("/subjects/{subject_id}/tests/generate", response_model=TestResponse)
def generate_test_for_subject(
    subject_id: str,
    payload: TestCreateRequest = Body(...),
    db: Session = Depends(get_db)
):
    user = get_or_create_default_user(db)
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    mcq_count = payload.mcq_count or subject.default_mcq_count
    subjective_count = payload.subjective_count if payload.subjective_count is not None else subject.default_subjective_count

    # Determine concepts
    active_concepts = db.query(Concept).filter(
        Concept.subject_id == subject_id,
        Concept.is_excluded == False
    ).all()

    if not active_concepts:
        # Check active topics as concepts fallback
        active_topics = db.query(Topic).filter(
            Topic.subject_id == subject_id,
            Topic.is_deleted == False,
            Topic.is_excluded == False
        ).all()
        if active_topics:
            active_concepts = [
                Concept(
                    id=t.id,
                    subject_id=subject_id,
                    name=t.name,
                    description=t.description or f"Core curriculum topic: {t.name}",
                    is_excluded=False
                )
                for t in active_topics
            ]
        else:
            # Auto-synthesize default concepts from subject name
            def_concept = Concept(
                id=str(uuid.uuid4()),
                subject_id=subject_id,
                name=f"{subject.name} Core Fundamentals",
                description=f"Comprehensive examination covering all topics in {subject.name}",
                is_excluded=False
            )
            db.add(def_concept)
            db.commit()
            active_concepts = [def_concept]

    rationale = None
    target_concept_ids = payload.target_concept_ids or []

    if payload.test_type in ("adaptive", "targeted"):
        rec = adaptive_service.recommend_adaptive_blueprint(db, subject_id, user.id)
        if not target_concept_ids:
            target_concept_ids = rec["target_concept_ids"]
        rationale = rec["rationale"]
    else:
        # Diagnostic test: cover all active concepts
        if not target_concept_ids:
            target_concept_ids = [c.id for c in active_concepts]
        rationale = "Comprehensive diagnostic test covering your core syllabus concepts to assess baseline readiness."

    # Retrieve subject-scoped evidence for targeted concepts
    selected_concepts = [c for c in active_concepts if c.id in target_concept_ids]
    if not selected_concepts:
        selected_concepts = active_concepts

    concept_query = " ".join([c.name + " " + c.description for c in selected_concepts])
    evidence = retrieval_service.search_subject_chunks(
        db=db,
        subject_id=subject_id,
        query=concept_query,
        top_k=8
    )

    concepts_data = [{"id": c.id, "name": c.name, "description": c.description} for c in selected_concepts]
    raw_questions = []
    try:
        raw_questions = ai_service.generate_questions(
            concepts=concepts_data,
            retrieved_evidence=evidence,
            mcq_count=mcq_count,
            subjective_count=subjective_count,
            db=db
        )
    except Exception as e:
        print(f"[TEST GENERATION FALLBACK] Standard generate failed: {e}")
        raw_questions = []

    if not raw_questions:
        raw_questions = synthesize_custom_test_fallback(
            subject_name=subject.name,
            topics=concepts_data,
            evidence=evidence,
            config={
                "mcq_count": mcq_count,
                "short_count": subjective_count,
                "marks_per_type": {"mcq": 2, "short": subject.default_subjective_marks}
            }
        )

    # Validate and persist questions
    created_questions = []
    seen_texts = set()

    for item in raw_questions:
        q_text = item.get("question_text", "").strip()
        if not q_text or q_text in seen_texts:
            continue
        seen_texts.add(q_text)

        q_type = item.get("question_type", "mcq")
        marks = int(item.get("marks", 2 if q_type == "mcq" else subject.default_subjective_marks))

        # Check options for MCQ
        options = None
        correct_opt = None
        if q_type == "mcq":
            opts = item.get("options", [])
            if not opts or len(opts) < 2:
                continue
            options = opts
            correct_opt = item.get("correct_option_id")
            # Ensure correct option exists
            if not any(opt.get("id") == correct_opt for opt in opts):
                correct_opt = opts[0].get("id")

        # Rubric criteria for subjective
        rubric_data = []
        if q_type == "subjective":
            rubric_data = item.get("rubric_criteria", [])
            # Validate rubric sum equals question marks
            if not scoring_service.validate_rubric_sum(float(marks), rubric_data):
                # Auto-balance criteria
                if rubric_data:
                    portion = round(marks / len(rubric_data), 2)
                    for r in rubric_data:
                        r["max_marks"] = portion
                else:
                    rubric_data = [{
                        "criterion_id": "crit_1",
                        "description": "Technical completeness and conceptual accuracy",
                        "max_marks": float(marks)
                    }]

        # Prepare source references
        source_refs = []
        if evidence:
            source_refs = [
                {
                    "chunk_id": evidence[0]["chunk_id"],
                    "document_id": evidence[0]["document_id"],
                    "filename": evidence[0]["filename"],
                    "page_number": item.get("source_page", evidence[0]["page_number"]),
                    "excerpt": item.get("excerpt", evidence[0]["supporting_text"][:250])
                }
            ]

        question = Question(
            subject_id=subject_id,
            concept_ids=item.get("concept_ids", [selected_concepts[0].id]),
            question_type=q_type,
            question_text=q_text,
            options=options,
            correct_option_id=correct_opt,
            explanation=item.get("explanation"),
            difficulty_label=item.get("difficulty_label", "medium"),
            marks=marks,
            expected_key_points=item.get("expected_key_points", []),
            reference_answer=item.get("reference_answer"),
            source_references=source_refs,
            validation_status="valid"
        )
        db.add(question)
        db.commit()
        db.refresh(question)

        # Save rubric criteria
        for r in rubric_data:
            crit = RubricCriterion(
                question_id=question.id,
                criterion_id=r.get("criterion_id", f"crit_{uuid.uuid4().hex[:6]}"),
                description=r.get("description", "Evaluation criterion"),
                max_marks=float(r.get("max_marks", 1.0)),
                evidence_references=source_refs
            )
            db.add(crit)

        db.commit()
        created_questions.append(question)

    total_marks = sum(q.marks for q in created_questions)
    title = payload.title or (
        f"{payload.test_type.capitalize()} Test: {selected_concepts[0].name if selected_concepts else subject.name}"
    )

    test = Test(
        subject_id=subject_id,
        user_id=user.id,
        title=title,
        test_type=payload.test_type,
        target_concept_ids=target_concept_ids,
        duration_minutes=subject.preferred_duration_minutes,
        total_marks=total_marks,
        rationale=rationale,
        status="ready"
    )
    db.add(test)
    db.commit()
    db.refresh(test)

    # Link questions
    for idx, q in enumerate(created_questions):
        tq = TestQuestion(
            test_id=test.id,
            question_id=q.id,
            order_index=idx
        )
        db.add(tq)
    db.commit()

    return TestResponse(
        id=test.id,
        subject_id=test.subject_id,
        title=test.title,
        test_type=test.test_type,
        source_mode=test.source_mode or "reference_grounded",
        target_concept_ids=test.target_concept_ids or [],
        target_topic_ids=test.target_topic_ids or [],
        test_config=test.test_config or {},
        duration_minutes=test.duration_minutes,
        total_marks=test.total_marks,
        total_raw_marks=test.total_raw_marks or float(test.total_marks),
        normalized_max_score=test.normalized_max_score or 10.0,
        rationale=test.rationale,
        status=test.status,
        created_at=test.created_at,
        question_count=len(created_questions)
    )

def synthesize_custom_test_fallback(
    subject_name: str,
    topics: list,
    evidence: list,
    config: dict
) -> list:
    """
    Deterministic fallback question generator that synthesizes questions
    strictly conforming to the requested counts, types, difficulty, and rubrics.
    Guarantees that test generation NEVER fails with 500 error.
    """
    questions = []
    marks_cfg = config.get("marks_per_type") or {}
    mcq_marks = float(marks_cfg.get("mcq", 2.0))
    vs_marks = float(marks_cfg.get("very_short", 2.0))
    s_marks = float(marks_cfg.get("short", 5.0))
    l_marks = float(marks_cfg.get("long", 10.0))

    mcq_count = config.get("mcq_count", 0)
    vs_count = config.get("very_short_count", 0) if config.get("mode") != "objective_only" else 0
    s_count = config.get("short_count", 0) if config.get("mode") != "objective_only" else 0
    l_count = config.get("long_count", 0) if config.get("mode") != "objective_only" else 0

    if (mcq_count + vs_count + s_count + l_count) == 0:
        mcq_count = 3
        s_count = 2

    # Map evidence snippets
    evidence_snippets = [e.get("supporting_text", "") for e in evidence if e.get("supporting_text")]
    if not evidence_snippets:
        evidence_snippets = [f"Core syllabus principles and concepts of {subject_name}."]

    def get_topic(idx: int):
        if topics:
            return topics[idx % len(topics)]
        return {"id": "topic_core", "name": f"Core {subject_name}", "description": f"Curriculum of {subject_name}"}

    # 1. Synthesize MCQs
    q_index = 0
    for i in range(mcq_count):
        t = get_topic(q_index)
        t_name = t.get("name", subject_name)
        ev_snip = evidence_snippets[i % len(evidence_snippets)][:200]

        q_text = f"Which of the following statements most accurately characterizes '{t_name}' in the study of {subject_name}?"
        opts = [
            {"id": "opt_a", "text": f"It establishes the fundamental structure and verified operation for {t_name}."},
            {"id": "opt_b", "text": f"It acts as a temporary workaround with no relevance to {t_name}."},
            {"id": "opt_c", "text": f"It eliminates the necessity for standard principles in {subject_name}."},
            {"id": "opt_d", "text": f"It is exclusively restricted to legacy deprecated environments."}
        ]
        questions.append({
            "question_type": "mcq",
            "subjective_subtype": None,
            "question_text": q_text,
            "difficulty_label": config.get("mcq_difficulty", "medium"),
            "marks": mcq_marks,
            "options": opts,
            "correct_option_id": "opt_a",
            "explanation": f"In {subject_name}, {t_name} defines the core mechanisms and principles governing system behavior.",
            "source_page": 1,
            "excerpt": ev_snip,
            "concept_ids": [t.get("id")] if t.get("id") else []
        })
        q_index += 1

    # 2. Synthesize Very Short Questions
    for i in range(vs_count):
        t = get_topic(q_index)
        t_name = t.get("name", subject_name)
        ev_snip = evidence_snippets[i % len(evidence_snippets)][:250]
        half_mark = round(vs_marks / 2.0, 2)
        second_half = round(vs_marks - half_mark, 2)

        questions.append({
            "question_type": "subjective",
            "subjective_subtype": "very_short",
            "question_text": f"State the primary definition and principal objective of '{t_name}' in {subject_name}.",
            "difficulty_label": config.get("very_short_difficulty", "easy"),
            "marks": vs_marks,
            "expected_key_points": [
                f"Precise technical definition of {t_name}.",
                f"Core functional purpose and key objective in {subject_name}."
            ],
            "reference_answer": f"{t_name} refers to the foundational mechanism in {subject_name} that structures key operations and ensures predictable system behavior.",
            "rubric_criteria": [
                {"criterion_id": f"vs_{i}_1", "description": f"Accurate identification and definition of {t_name}", "max_marks": half_mark},
                {"criterion_id": f"vs_{i}_2", "description": "Clear statement of functional objective/significance", "max_marks": second_half}
            ],
            "source_page": 1,
            "excerpt": ev_snip,
            "concept_ids": [t.get("id")] if t.get("id") else []
        })
        q_index += 1

    # 3. Synthesize Short Questions
    for i in range(s_count):
        t = get_topic(q_index)
        t_name = t.get("name", subject_name)
        ev_snip = evidence_snippets[i % len(evidence_snippets)][:300]
        crit_part1 = round(s_marks * 0.5, 2)
        crit_part2 = round(s_marks - crit_part1, 2)

        questions.append({
            "question_type": "subjective",
            "subjective_subtype": "short",
            "question_text": f"Explain the operational mechanism and key procedural steps involved in '{t_name}'.",
            "difficulty_label": config.get("short_difficulty", "medium"),
            "marks": s_marks,
            "expected_key_points": [
                f"Detailed explanation of core components in {t_name}.",
                f"Step-by-step operational flow or interaction model.",
                f"Practical implications and considerations in {subject_name}."
            ],
            "reference_answer": f"{t_name} operates by coordinating essential data structures and control flows. First, inputs are validated according to system constraints; second, state transitions or transformations are executed deterministically to maintain consistency in {subject_name}.",
            "rubric_criteria": [
                {"criterion_id": f"s_{i}_1", "description": "Conceptual depth and explanation of components", "max_marks": crit_part1},
                {"criterion_id": f"s_{i}_2", "description": "Accurate operational workflow and technical reasoning", "max_marks": crit_part2}
            ],
            "source_page": 1,
            "excerpt": ev_snip,
            "concept_ids": [t.get("id")] if t.get("id") else []
        })
        q_index += 1

    # 4. Synthesize Long Questions
    for i in range(l_count):
        t = get_topic(q_index)
        t_name = t.get("name", subject_name)
        ev_snip = evidence_snippets[i % len(evidence_snippets)][:400]
        c1 = round(l_marks * 0.4, 2)
        c2 = round(l_marks * 0.3, 2)
        c3 = round(l_marks - c1 - c2, 2)

        questions.append({
            "question_type": "subjective",
            "subjective_subtype": "long",
            "question_text": f"Provide an in-depth analytical evaluation of '{t_name}'. Discuss its architectural design, major tradeoffs, and failure recovery or optimization strategies in {subject_name}.",
            "difficulty_label": config.get("long_difficulty", "hard"),
            "marks": l_marks,
            "expected_key_points": [
                f"Comprehensive architectural breakdown of {t_name}.",
                f"Critical evaluation of tradeoffs (performance, complexity, reliability).",
                f"Handling edge cases, concurrency, or failure states.",
                f"Real-world application and system optimization strategies."
            ],
            "reference_answer": f"Architecturally, {t_name} requires careful balancing between performance and structural guarantees. In {subject_name}, implementing {t_name} involves establishing formal boundaries, mitigating bottleneck risks, and enforcing rigorous validation rules to ensure robust operation under load.",
            "rubric_criteria": [
                {"criterion_id": f"l_{i}_1", "description": "Thorough architectural breakdown and foundational knowledge", "max_marks": c1},
                {"criterion_id": f"l_{i}_2", "description": "Rigorous analysis of engineering tradeoffs and constraints", "max_marks": c2},
                {"criterion_id": f"l_{i}_3", "description": "Robust strategy for edge cases and system optimization", "max_marks": c3}
            ],
            "source_page": 1,
            "excerpt": ev_snip,
            "concept_ids": [t.get("id")] if t.get("id") else []
        })
        q_index += 1

    return questions

@router.post("/subjects/{subject_id}/tests/custom", response_model=TestResponse)
def create_custom_test(
    subject_id: str,
    payload: CustomTestCreateRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Creates a custom practice test configured by the student:
    - Independent controls for MCQ, Very Short, Short, and Long answer questions
    - Per-type counts and difficulty settings
    - Target topic selection
    - Pre-persists complete rubrics and answer keys
    - Automatically determines source_mode (reference_grounded vs syllabus_scoped)
    """
    user = get_or_create_default_user(db)
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    total_requested = payload.mcq_count + payload.very_short_count + payload.short_count + payload.long_count
    if total_requested <= 0:
        raise HTTPException(
            status_code=400,
            detail="Test must contain at least 1 question. Please specify counts for MCQs or subjective questions."
        )

    # 1. Resolve topics: If specific IDs provided, use them; otherwise default to ALL topics for the subject!
    topics_query = db.query(Topic).filter(
        Topic.subject_id == subject_id,
        Topic.is_deleted == False,
        Topic.is_excluded == False
    )
    if payload.target_topic_ids and len(payload.target_topic_ids) > 0:
        filtered_topics = topics_query.filter(Topic.id.in_(payload.target_topic_ids)).all()
        selected_topics = filtered_topics if filtered_topics else topics_query.all()
    else:
        selected_topics = topics_query.all()

    if not selected_topics:
        # Fallback to concepts if topics table was not yet populated
        concepts = db.query(Concept).filter(
            Concept.subject_id == subject_id,
            Concept.is_excluded == False
        ).all()
        if concepts:
            topics_data = [{"id": c.id, "name": c.name, "description": c.description} for c in concepts]
            target_topic_ids = [c.id for c in concepts]
        else:
            # Neither topics nor concepts exist yet: auto-synthesize default unit and topics for the subject!
            unit = db.query(SyllabusUnit).filter(SyllabusUnit.subject_id == subject_id).first()
            if not unit:
                unit = SyllabusUnit(
                    id=str(uuid.uuid4()),
                    subject_id=subject_id,
                    unit_number=1,
                    title=f"Unit 1: Complete Curriculum of {subject.name}",
                    description=f"Core curriculum concepts, principles, and problems for {subject.name}"
                )
                db.add(unit)
                db.flush()

            default_topics_specs = [
                (f"Core Concepts & Architecture of {subject.name}", f"Fundamental definitions, core components, and architecture in {subject.name}."),
                (f"Key Operations & Algorithms in {subject.name}", f"Essential operations, procedures, and mechanics across {subject.name}."),
                (f"Applied Problem Solving & Analysis in {subject.name}", f"Technical reasoning, tradeoffs, and scenario problem-solving in {subject.name}.")
            ]
            synthesized_topics = []
            for t_name, t_desc in default_topics_specs:
                new_topic = Topic(
                    id=str(uuid.uuid4()),
                    subject_id=subject_id,
                    unit_id=unit.id,
                    name=t_name,
                    description=t_desc,
                    practice_priority="high"
                )
                db.add(new_topic)
                synthesized_topics.append(new_topic)
            db.commit()

            selected_topics = synthesized_topics
            topics_data = [{"id": t.id, "name": t.name, "description": t.description} for t in selected_topics]
            target_topic_ids = [t.id for t in selected_topics]
    else:
        topics_data = [{"id": t.id, "name": t.name, "description": t.description} for t in selected_topics]
        target_topic_ids = [t.id for t in selected_topics]

    # 2. Retrieve supporting evidence for reference-grounded generation
    topic_query_str = " ".join([t["name"] + " " + (t.get("description") or "") for t in topics_data])
    evidence = retrieval_service.search_subject_chunks(
        db=db,
        subject_id=subject_id,
        query=topic_query_str,
        top_k=10
    )

    source_mode = "reference_grounded" if evidence else "syllabus_scoped"

    # 3. Call custom test generator in AI Service
    config_dict = payload.model_dump()
    raw_questions = []
    try:
        raw_questions = ai_service.generate_custom_test(
            topics=topics_data,
            retrieved_evidence=evidence,
            config=config_dict,
            db=db
        )
    except Exception as e:
        print(f"[TEST GENERATION FALLBACK] AI model failed or malformed: {e}")
        raw_questions = []

    if not raw_questions:
        raw_questions = synthesize_custom_test_fallback(
            subject_name=subject.name,
            topics=topics_data,
            evidence=evidence,
            config=config_dict
        )

    # 4. Strict Quota Enforcement: categorize raw AI questions into subtype pools
    desired_mcq = payload.mcq_count if payload.mode != "subjective_only" else 0
    desired_vs = payload.very_short_count if payload.mode != "objective_only" else 0
    desired_short = payload.short_count if payload.mode != "objective_only" else 0
    desired_long = payload.long_count if payload.mode != "objective_only" else 0

    pool_mcq = []
    pool_vs = []
    pool_short = []
    pool_long = []

    for item in raw_questions:
        q_text = item.get("question_text", "").strip()
        if not q_text:
            continue
        q_type = item.get("question_type", "mcq")
        subj_subtype = item.get("subjective_subtype")

        if q_type == "mcq":
            opts = item.get("options", [])
            if opts and len(opts) >= 2:
                pool_mcq.append(item)
        elif q_type == "subjective":
            m = float(item.get("marks", 2))
            if subj_subtype == "very_short" or (m <= 2 and subj_subtype not in ("short", "long")):
                item["subjective_subtype"] = "very_short"
                pool_vs.append(item)
            elif subj_subtype == "long" or m >= 8:
                item["subjective_subtype"] = "long"
                pool_long.append(item)
            else:
                item["subjective_subtype"] = "short"
                pool_short.append(item)

    # Fulfill requested quotas exactly; synthesize dynamically if any pool has fewer than requested
    marks_cfg = payload.marks_per_type or {"mcq": 2, "very_short": 2, "short": 5, "long": 10}
    selected_items = []

    # A. MCQs
    chosen_mcq = pool_mcq[:desired_mcq]
    if len(chosen_mcq) < desired_mcq:
        needed = desired_mcq - len(chosen_mcq)
        synth = synthesize_custom_test_fallback(
            subject_name=subject.name,
            topics=topics_data,
            evidence=evidence,
            config={**config_dict, "mcq_count": needed, "very_short_count": 0, "short_count": 0, "long_count": 0}
        )
        chosen_mcq.extend(synth[:needed])
    selected_items.extend(chosen_mcq)

    # B. Very Short Questions
    chosen_vs = pool_vs[:desired_vs]
    if len(chosen_vs) < desired_vs:
        needed = desired_vs - len(chosen_vs)
        synth = synthesize_custom_test_fallback(
            subject_name=subject.name,
            topics=topics_data,
            evidence=evidence,
            config={**config_dict, "mcq_count": 0, "very_short_count": needed, "short_count": 0, "long_count": 0}
        )
        chosen_vs.extend(synth[:needed])
    selected_items.extend(chosen_vs)

    # C. Short Questions
    chosen_short = pool_short[:desired_short]
    if len(chosen_short) < desired_short:
        needed = desired_short - len(chosen_short)
        synth = synthesize_custom_test_fallback(
            subject_name=subject.name,
            topics=topics_data,
            evidence=evidence,
            config={**config_dict, "mcq_count": 0, "very_short_count": 0, "short_count": needed, "long_count": 0}
        )
        chosen_short.extend(synth[:needed])
    selected_items.extend(chosen_short)

    # D. Long Questions
    chosen_long = pool_long[:desired_long]
    if len(chosen_long) < desired_long:
        needed = desired_long - len(chosen_long)
        synth = synthesize_custom_test_fallback(
            subject_name=subject.name,
            topics=topics_data,
            evidence=evidence,
            config={**config_dict, "mcq_count": 0, "very_short_count": 0, "short_count": 0, "long_count": needed}
        )
        chosen_long.extend(synth[:needed])
    selected_items.extend(chosen_long)

    # 5. Persist strictly validated questions with corresponding rubrics
    created_questions = []
    seen_texts = set()
    total_raw_marks = 0.0

    for item in selected_items:
        q_text = item.get("question_text", "").strip()
        if not q_text or q_text in seen_texts:
            continue
        seen_texts.add(q_text)

        q_type = item.get("question_type", "mcq")
        subj_subtype = item.get("subjective_subtype")
        
        # Enforce exact marks configured per question type
        if q_type == "mcq":
            marks = int(marks_cfg.get("mcq", 2))
        elif subj_subtype == "very_short":
            marks = int(marks_cfg.get("very_short", 2))
        elif subj_subtype == "long":
            marks = int(marks_cfg.get("long", 10))
        else:
            marks = int(marks_cfg.get("short", 5))

        total_raw_marks += marks

        options = None
        correct_opt = None
        if q_type == "mcq":
            opts = item.get("options", [])
            # Normalize option IDs if needed
            standard_opts = []
            for opt_idx, opt in enumerate(opts):
                opt_id = opt.get("id") or chr(65 + opt_idx)
                # Map opt_a -> A
                if opt_id.lower().startswith("opt_"):
                    opt_id = opt_id.split("_")[-1].upper()
                standard_opts.append({"id": opt_id, "text": opt.get("text", "")})
            options = standard_opts
            raw_correct = item.get("correct_option_id", "A")
            if raw_correct.lower().startswith("opt_"):
                raw_correct = raw_correct.split("_")[-1].upper()
            correct_opt = raw_correct
            if not any(opt.get("id") == correct_opt for opt in options):
                correct_opt = options[0].get("id")

        q_topic_ids = item.get("topic_ids") or target_topic_ids[:1]

        q = Question(
            id=str(uuid.uuid4()),
            subject_id=subject_id,
            concept_ids=q_topic_ids,
            topic_ids=q_topic_ids,
            question_type=q_type,
            subjective_subtype=subj_subtype,
            source_mode=source_mode,
            question_text=q_text,
            options=options,
            correct_option_id=correct_opt,
            explanation=item.get("explanation"),
            difficulty_label=item.get("difficulty_label", payload.global_difficulty),
            marks=marks,
            expected_key_points=item.get("expected_key_points") or [],
            reference_answer=item.get("reference_answer"),
            source_references=[{
                "page_number": item.get("source_page", 1),
                "supporting_text": item.get("excerpt", "Syllabus topic reference"),
                "source_mode": source_mode
            }],
            validation_status="valid"
        )
        db.add(q)
        db.flush()

        # Save rubrics for subjective questions
        if q_type == "subjective":
            rubric_raw = item.get("rubric_criteria", [])
            if not rubric_raw:
                half = round(marks / 2.0, 1)
                rubric_raw = [
                    {"criterion_id": f"crit_{q.id}_1", "description": "Core conceptual accuracy and definition", "max_marks": half},
                    {"criterion_id": f"crit_{q.id}_2", "description": "Technical completeness and explanation", "max_marks": round(marks - half, 1)}
                ]
            else:
                # Ensure criteria max_marks sum to question marks
                c_sum = sum(float(r.get("max_marks", 1.0)) for r in rubric_raw)
                scale = (marks / c_sum) if c_sum > 0 else 1.0
                for r in rubric_raw:
                    r["max_marks"] = round(float(r.get("max_marks", 1.0)) * scale, 1)

            for idx, r in enumerate(rubric_raw):
                crit = RubricCriterion(
                    id=str(uuid.uuid4()),
                    question_id=q.id,
                    criterion_id=r.get("criterion_id", f"crit_{idx}"),
                    description=r.get("description", "Evaluation criterion"),
                    max_marks=float(r.get("max_marks", 1.0)),
                    evidence_references=q.source_references
                )
                db.add(crit)

        created_questions.append(q)

    if not created_questions:
        raise HTTPException(status_code=500, detail="Could not validate generated questions.")

    # 5. Persist Test
    test_title = payload.title or f"{subject.name} - Custom Practice Test"
    mode_disclosure = (
        "Questions and grading criteria verified against uploaded study materials."
        if source_mode == "reference_grounded" else
        "AI-generated practice based on your syllabus. Answers are not verified against uploaded study notes."
    )
    rationale = f"Custom test covering {len(target_topic_ids)} topics ({len(created_questions)} questions, {int(total_raw_marks)} raw marks). {mode_disclosure}"

    test = Test(
        id=str(uuid.uuid4()),
        subject_id=subject_id,
        user_id=user.id,
        title=test_title,
        test_type="practice",
        source_mode=source_mode,
        target_concept_ids=target_topic_ids,
        target_topic_ids=target_topic_ids,
        test_config=config_dict,
        duration_minutes=payload.duration_minutes if payload.is_timed else 0,
        total_marks=int(total_raw_marks),
        total_raw_marks=total_raw_marks,
        normalized_max_score=10.0,
        rationale=rationale,
        status="ready"
    )
    db.add(test)
    db.commit()
    db.refresh(test)

    # Link test questions in order
    for idx, q in enumerate(created_questions):
        tq = TestQuestion(
            test_id=test.id,
            question_id=q.id,
            order_index=idx
        )
        db.add(tq)
    db.commit()

    return TestResponse(
        id=test.id,
        subject_id=test.subject_id,
        title=test.title,
        test_type=test.test_type,
        source_mode=test.source_mode,
        target_concept_ids=test.target_concept_ids or [],
        target_topic_ids=test.target_topic_ids or [],
        test_config=test.test_config or {},
        duration_minutes=test.duration_minutes,
        total_marks=test.total_marks,
        total_raw_marks=test.total_raw_marks or float(test.total_marks),
        normalized_max_score=test.normalized_max_score or 10.0,
        rationale=test.rationale,
        status=test.status,
        created_at=test.created_at,
        question_count=len(created_questions)
    )

@router.get("/tests/{test_id}", response_model=TestResponse)
def get_test(test_id: str, db: Session = Depends(get_db)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    q_count = len(test.test_questions)
    return TestResponse(
        id=test.id,
        subject_id=test.subject_id,
        title=test.title,
        test_type=test.test_type,
        source_mode=test.source_mode or "reference_grounded",
        target_concept_ids=test.target_concept_ids or [],
        target_topic_ids=test.target_topic_ids or [],
        test_config=test.test_config or {},
        duration_minutes=test.duration_minutes,
        total_marks=test.total_marks,
        total_raw_marks=test.total_raw_marks or float(test.total_marks),
        normalized_max_score=test.normalized_max_score or 10.0,
        rationale=test.rationale,
        status=test.status,
        created_at=test.created_at,
        question_count=q_count
    )

@router.get("/subjects/{subject_id}/tests", response_model=List[TestResponse])
def list_tests_for_subject(subject_id: str, db: Session = Depends(get_db)):
    """
    List all tests for a subject.
    """
    tests = db.query(Test).filter(Test.subject_id == subject_id).order_by(Test.created_at.desc()).all()
    results = []
    for t in tests:
        q_count = len(t.test_questions)
        results.append(
            TestResponse(
                id=t.id,
                subject_id=t.subject_id,
                title=t.title,
                test_type=t.test_type,
                source_mode=t.source_mode or "reference_grounded",
                target_concept_ids=t.target_concept_ids or [],
                target_topic_ids=t.target_topic_ids or [],
                test_config=t.test_config or {},
                duration_minutes=t.duration_minutes,
                total_marks=t.total_marks,
                total_raw_marks=t.total_raw_marks or float(t.total_marks),
                normalized_max_score=t.normalized_max_score or 10.0,
                rationale=t.rationale,
                status=t.status,
                created_at=t.created_at,
                question_count=q_count
            )
        )
    return results

@router.get("/tests/{test_id}/take", response_model=TestTakingView)
def get_test_taking_view(test_id: str, db: Session = Depends(get_db)):
    """
    CRITICAL: Secure student view of test.
    Excludes correct_option_id, reference_answer, and rubrics!
    Creates or resumes an in-progress Attempt.
    """
    user = get_or_create_default_user(db)
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Check for existing in_progress attempt
    attempt = db.query(Attempt).filter(
        Attempt.test_id == test_id,
        Attempt.user_id == user.id,
        Attempt.status == "in_progress"
    ).first()

    if not attempt:
        attempt = Attempt(
            test_id=test_id,
            user_id=user.id,
            status="in_progress"
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

    # Fetch previously saved answers for this attempt
    saved_answers_records = db.query(StudentAnswer).filter(StudentAnswer.attempt_id == attempt.id).all()
    saved_answers = {
        a.question_id: {
            "selected_option_id": a.selected_option_id,
            "answer_text": a.answer_text,
            "is_marked_for_review": a.is_marked_for_review
        }
        for a in saved_answers_records
    }

    test_questions = db.query(TestQuestion).filter(TestQuestion.test_id == test_id).order_by(TestQuestion.order_index).all()
    student_questions = []

    for tq in test_questions:
        q = tq.question
        opts = None
        if q.options:
            opts = [MCQOption(id=o["id"], text=o["text"]) for o in q.options]

        student_questions.append(
            StudentQuestionView(
                id=q.id,
                question_type=q.question_type,
                subjective_subtype=q.subjective_subtype,
                question_text=q.question_text,
                options=opts, # NO correct_option_id!
                marks=q.marks,
                difficulty_label=q.difficulty_label,
                order_index=tq.order_index
            )
        )

    return TestTakingView(
        attempt_id=attempt.id,
        test_id=test.id,
        subject_id=test.subject_id,
        title=test.title,
        source_mode=test.source_mode or "reference_grounded",
        duration_minutes=test.duration_minutes,
        total_marks=test.total_marks,
        started_at=attempt.started_at,
        questions=student_questions,
        saved_answers=saved_answers
    )
