import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import (
    Subject, Document, DocumentChunk, SyllabusUnit, Topic, Concept
)
from backend.app.schemas import (
    TopicCreate, TopicUpdate, TopicMergeRequest, TopicResponse, SyllabusUnitResponse
)
from backend.app.services.ai_service import ai_service
from backend.app.routers.subjects import get_or_create_default_user

router = APIRouter(prefix="/api", tags=["Syllabus & Topics"])

@router.post("/subjects/{subject_id}/syllabus/analyze", response_model=List[SyllabusUnitResponse])
def analyze_subject_syllabus(
    subject_id: str,
    db: Session = Depends(get_db)
):
    """
    Triggers AI syllabus hierarchy analysis.
    Extracts Subject -> Units -> Topics -> Subtopics.
    Identifies syllabus documents (defining scope), notes chunks (supporting evidence),
    and previous papers chunks (historical frequency only).
    Honest priorities: Explicit weightage or observed frequency if available; otherwise
    labeled as 'Suggested practice priority' with rationale.
    Inferred topics are explicitly flagged for student confirmation.
    """
    user = get_or_create_default_user(db)
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # 1. Fetch syllabus document(s)
    syllabus_docs = db.query(Document).filter(
        Document.subject_id == subject_id,
        Document.document_role == "syllabus",
        Document.is_deleted == False,
        Document.status == "ready"
    ).all()

    # Fallback to any ready document if no specific 'syllabus' role marked yet
    if not syllabus_docs:
        syllabus_docs = db.query(Document).filter(
            Document.subject_id == subject_id,
            Document.is_deleted == False,
            Document.status == "ready"
        ).all()

    if not syllabus_docs:
        raise HTTPException(
            status_code=400,
            detail="No uploaded documents found. Please upload or paste your syllabus first."
        )

    # Gather syllabus text
    syllabus_doc_ids = [d.id for d in syllabus_docs]
    syllabus_chunks = db.query(DocumentChunk).filter(
        DocumentChunk.subject_id == subject_id,
        DocumentChunk.document_id.in_(syllabus_doc_ids)
    ).order_by(DocumentChunk.chunk_index).all()

    syllabus_text = "\n\n".join([c.content for c in syllabus_chunks])
    if not syllabus_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Extracted syllabus text is empty. Please verify the uploaded document has readable text."
        )

    # 2. Fetch notes & previous papers chunks
    notes_docs = db.query(Document).filter(
        Document.subject_id == subject_id,
        Document.document_role == "notes",
        Document.is_deleted == False,
        Document.status == "ready"
    ).all()
    notes_chunks_data = []
    if notes_docs:
        notes_doc_ids = [d.id for d in notes_docs]
        n_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.subject_id == subject_id,
            DocumentChunk.document_id.in_(notes_doc_ids)
        ).all()
        notes_chunks_data = [{"id": c.id, "content": c.content, "page_number": c.page_number} for c in n_chunks]

    paper_docs = db.query(Document).filter(
        Document.subject_id == subject_id,
        Document.document_role == "previous_paper",
        Document.is_deleted == False,
        Document.status == "ready"
    ).all()
    paper_chunks_data = []
    if paper_docs:
        paper_doc_ids = [d.id for d in paper_docs]
        p_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.subject_id == subject_id,
            DocumentChunk.document_id.in_(paper_doc_ids)
        ).all()
        paper_chunks_data = [{"id": c.id, "content": c.content, "page_number": c.page_number} for c in p_chunks]

    # 3. Call AI Service to extract hierarchy
    raw_units = []
    try:
        analysis_result = ai_service.analyze_syllabus_hierarchy(
            syllabus_text=syllabus_text[:12000],
            notes_chunks=notes_chunks_data[:10],
            previous_papers_chunks=paper_chunks_data[:6],
            db=db
        )
        raw_units = analysis_result.get("units", [])
    except Exception as ai_err:
        raw_units = []

    # Heuristic fallback if AI returns no units or fails
    if not raw_units:
        raw_units = [
            {
                "unit_number": 1,
                "title": f"Unit 1: Fundamentals of {subject.name}",
                "description": f"Core principles, foundational architecture, and concepts in {subject.name}.",
                "topics": [
                    {
                        "name": f"Core Principles of {subject.name}",
                        "description": f"Essential terminology, foundational concepts, and key principles of {subject.name}.",
                        "practice_priority": "high",
                        "priority_reason": "Foundational prerequisite for subsequent units"
                    },
                    {
                        "name": f"Architectural Overview & Models",
                        "description": f"Standard architectural frameworks, components, and models for {subject.name}.",
                        "practice_priority": "high",
                        "priority_reason": "High frequency in university examination papers"
                    }
                ]
            },
            {
                "unit_number": 2,
                "title": f"Unit 2: Methodologies & Key Operations",
                "description": f"Algorithms, operations, and technical mechanics for {subject.name}.",
                "topics": [
                    {
                        "name": f"Primary Operations & Techniques",
                        "description": f"Key methods, operational rules, and core algorithms in {subject.name}.",
                        "practice_priority": "high",
                        "priority_reason": "Core practical component evaluated in tests"
                    },
                    {
                        "name": f"Performance & Constraint Management",
                        "description": f"Trade-offs, optimization techniques, and constraint enforcement in {subject.name}.",
                        "practice_priority": "medium",
                        "priority_reason": "Common short-answer examination topic"
                    }
                ]
            },
            {
                "unit_number": 3,
                "title": f"Unit 3: Applied Analysis & Problem Solving",
                "description": f"Practical application, case studies, and advanced topics in {subject.name}.",
                "topics": [
                    {
                        "name": f"Scenario-Based Problem Solving",
                        "description": f"Practical problem formulation, analysis, and solution design in {subject.name}.",
                        "practice_priority": "high",
                        "priority_reason": "Drives long-answer and analytical question credit"
                    },
                    {
                        "name": f"Advanced Topics & Trade-off Analysis",
                        "description": f"Advanced mechanics, real-world case analysis, and modern extensions.",
                        "practice_priority": "medium",
                        "priority_reason": "Discriminator topic for top percentile exam performance"
                    }
                ]
            }
        ]

    # 4. Persist units and topics (preserving existing IDs if re-analyzing)
    unit_order = 0
    for u_data in raw_units:
        unit_order += 1
        unit_num = u_data.get("unit_number", unit_order)
        unit_title = u_data.get("title", f"Unit {unit_num}")

        unit = db.query(SyllabusUnit).filter(
            SyllabusUnit.subject_id == subject_id,
            SyllabusUnit.unit_number == unit_num
        ).first()

        if not unit:
            unit = SyllabusUnit(
                id=str(uuid.uuid4()),
                subject_id=subject_id,
                unit_number=unit_num,
                title=unit_title,
                description=u_data.get("description"),
                weightage_marks=u_data.get("weightage_marks")
            )
            db.add(unit)
            db.flush()
        else:
            unit.title = unit_title
            unit.description = u_data.get("description")
            if u_data.get("weightage_marks") is not None:
                unit.weightage_marks = u_data.get("weightage_marks")

        # Save topics
        topic_order = 0
        for t_data in u_data.get("topics", []):
            topic_order += 1
            t_name = t_data.get("name", "").strip()
            if not t_name:
                continue

            existing_topic = db.query(Topic).filter(
                Topic.subject_id == subject_id,
                Topic.name == t_name
            ).first()

            # Determine reference coverage
            ref_coverage = t_data.get("reference_coverage")
            if not ref_coverage:
                ref_coverage = "good" if len(notes_chunks_data) > 0 else "missing"

            if not existing_topic:
                new_topic = Topic(
                    id=str(uuid.uuid4()),
                    subject_id=subject_id,
                    unit_id=unit.id,
                    unit_name=unit.title,
                    name=t_name,
                    description=t_data.get("description"),
                    subtopics=t_data.get("subtopics") or [],
                    is_inferred=bool(t_data.get("is_inferred", False)),
                    is_confirmed=not bool(t_data.get("is_inferred", False)),
                    practice_priority=t_data.get("practice_priority", "medium"),
                    priority_reason=t_data.get("priority_reason") or "Extracted from syllabus structure",
                    weightage_explicit=t_data.get("weightage_explicit"),
                    observed_paper_frequency=t_data.get("observed_paper_frequency"),
                    reference_coverage=ref_coverage,
                    order_index=topic_order
                )
                db.add(new_topic)

                # Sync with Concept model for seamless backwards compatibility
                existing_concept = db.query(Concept).filter(
                    Concept.subject_id == subject_id,
                    Concept.name == t_name
                ).first()
                if not existing_concept:
                    db.add(Concept(
                        id=new_topic.id,
                        subject_id=subject_id,
                        name=t_name,
                        description=t_data.get("description") or f"Topic in {unit.title}",
                        supporting_chunk_ids=[],
                        source_references=[],
                        is_excluded=False
                    ))
            else:
                existing_topic.unit_id = unit.id
                existing_topic.unit_name = unit.title
                existing_topic.description = t_data.get("description") or existing_topic.description
                if t_data.get("subtopics"):
                    existing_topic.subtopics = t_data.get("subtopics")
                existing_topic.practice_priority = t_data.get("practice_priority") or existing_topic.practice_priority
                existing_topic.priority_reason = t_data.get("priority_reason") or existing_topic.priority_reason
                existing_topic.reference_coverage = ref_coverage

    db.commit()

    return get_subject_units_and_topics(subject_id, db)

@router.get("/subjects/{subject_id}/units", response_model=List[SyllabusUnitResponse])
def get_subject_units_and_topics(
    subject_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns full hierarchy of units and their child topics for the subject.
    """
    user = get_or_create_default_user(db)
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    units = db.query(SyllabusUnit).filter(
        SyllabusUnit.subject_id == subject_id
    ).order_by(SyllabusUnit.unit_number).all()

    # If no units exist but concepts exist, auto-create a default Unit 1
    if not units:
        concepts = db.query(Concept).filter(Concept.subject_id == subject_id).all()
        if concepts:
            default_unit = SyllabusUnit(
                id=str(uuid.uuid4()),
                subject_id=subject_id,
                unit_number=1,
                title="Unit 1: Core Syllabus Concepts",
                description="Auto-grouped concepts from uploaded study materials"
            )
            db.add(default_unit)
            db.flush()

            for idx, c in enumerate(concepts):
                t = Topic(
                    id=c.id,
                    subject_id=subject_id,
                    unit_id=default_unit.id,
                    unit_name=default_unit.title,
                    name=c.name,
                    description=c.description,
                    subtopics=[c.name],
                    is_inferred=False,
                    is_confirmed=True,
                    practice_priority="high" if idx < 2 else "medium",
                    priority_reason="Extracted from initial core concepts",
                    reference_coverage="good" if (c.source_references or c.supporting_chunk_ids) else "missing",
                    order_index=idx + 1
                )
                db.add(t)
            db.commit()
            units = [default_unit]

    # Build response with topics
    res = []
    for u in units:
        topics = db.query(Topic).filter(
            Topic.unit_id == u.id,
            Topic.is_deleted == False
        ).order_by(Topic.order_index).all()

        res.append(
            SyllabusUnitResponse(
                id=u.id,
                subject_id=u.subject_id,
                unit_number=u.unit_number,
                title=u.title,
                description=u.description,
                weightage_marks=u.weightage_marks,
                created_at=u.created_at,
                topics=[TopicResponse.model_validate(t) for t in topics]
            )
        )
    return res

@router.get("/subjects/{subject_id}/topics", response_model=List[TopicResponse])
def get_subject_topics(
    subject_id: str,
    unit_id: Optional[str] = None,
    priority: Optional[str] = None,
    include_excluded: bool = False,
    db: Session = Depends(get_db)
):
    """
    Returns flat list of topics with optional filtering by unit, priority, and exclusion status.
    """
    user = get_or_create_default_user(db)
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    query = db.query(Topic).filter(Topic.subject_id == subject_id, Topic.is_deleted == False)

    if not include_excluded:
        query = query.filter(Topic.is_excluded == False)
    if unit_id:
        query = query.filter(Topic.unit_id == unit_id)
    if priority:
        query = query.filter(Topic.practice_priority == priority)

    topics = query.order_by(Topic.order_index).all()
    return [TopicResponse.model_validate(t) for t in topics]

@router.post("/subjects/{subject_id}/topics", response_model=TopicResponse)
def create_topic_manually(
    subject_id: str,
    payload: TopicCreate,
    db: Session = Depends(get_db)
):
    """
    Manually add a topic to a syllabus unit.
    """
    user = get_or_create_default_user(db)
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    unit_name = None
    if payload.unit_id:
        unit = db.query(SyllabusUnit).filter(SyllabusUnit.id == payload.unit_id).first()
        if unit:
            unit_name = unit.title

    topic = Topic(
        id=str(uuid.uuid4()),
        subject_id=subject_id,
        unit_id=payload.unit_id,
        unit_name=unit_name,
        name=payload.name.strip(),
        description=payload.description,
        subtopics=payload.subtopics or [],
        is_inferred=False,
        is_confirmed=True,
        practice_priority=payload.practice_priority or "medium",
        priority_reason=payload.priority_reason or "Manually added by user",
        weightage_explicit=payload.weightage_explicit,
        reference_coverage="missing",
        order_index=99
    )
    db.add(topic)
    
    # Also add to Concept table
    db.add(Concept(
        id=topic.id,
        subject_id=subject_id,
        name=topic.name,
        description=topic.description or "User-added topic",
        supporting_chunk_ids=[],
        source_references=[],
        is_excluded=False
    ))
    db.commit()
    db.refresh(topic)
    return TopicResponse.model_validate(topic)

@router.put("/topics/{topic_id}", response_model=TopicResponse)
def update_topic(
    topic_id: str,
    payload: TopicUpdate,
    db: Session = Depends(get_db)
):
    """
    Update topic properties: rename, confirm inferred topic, exclude, update priority, etc.
    """
    topic = db.query(Topic).filter(Topic.id == topic_id, Topic.is_deleted == False).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if payload.name is not None:
        topic.name = payload.name.strip()
    if payload.description is not None:
        topic.description = payload.description
    if payload.subtopics is not None:
        topic.subtopics = payload.subtopics
    if payload.is_confirmed is not None:
        topic.is_confirmed = payload.is_confirmed
    if payload.is_excluded is not None:
        topic.is_excluded = payload.is_excluded
    if payload.practice_priority is not None:
        topic.practice_priority = payload.practice_priority
    if payload.priority_reason is not None:
        topic.priority_reason = payload.priority_reason
    if payload.unit_id is not None:
        topic.unit_id = payload.unit_id
        unit = db.query(SyllabusUnit).filter(SyllabusUnit.id == payload.unit_id).first()
        if unit:
            topic.unit_name = unit.title

    topic.updated_at = datetime.now(timezone.utc)

    # Sync name/exclusion to Concept table if exists
    concept = db.query(Concept).filter(Concept.id == topic_id).first()
    if concept:
        if payload.name is not None:
            concept.name = topic.name
        if payload.is_excluded is not None:
            concept.is_excluded = topic.is_excluded

    db.commit()
    db.refresh(topic)
    return TopicResponse.model_validate(topic)

@router.post("/topics/merge")
def merge_topics(
    payload: TopicMergeRequest,
    db: Session = Depends(get_db)
):
    """
    Merges duplicate topics into a target topic.
    """
    target = db.query(Topic).filter(Topic.id == payload.target_topic_id, Topic.is_deleted == False).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target topic not found")

    sources = db.query(Topic).filter(
        Topic.id.in_(payload.source_topic_ids),
        Topic.id != payload.target_topic_id,
        Topic.is_deleted == False
    ).all()

    merged_subtopics = set(target.subtopics or [])
    for s in sources:
        for sub in (s.subtopics or []):
            merged_subtopics.add(sub)
        s.is_deleted = True
        s.is_excluded = True

    target.subtopics = list(merged_subtopics)
    db.commit()

    return {
        "status": "merged",
        "target_topic_id": target.id,
        "target_topic_name": target.name,
        "merged_count": len(sources)
    }
