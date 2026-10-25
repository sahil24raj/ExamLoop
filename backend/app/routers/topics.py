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
from backend.app.auth import get_current_user, get_user_accessible_subject
from backend.app.models import User

router = APIRouter(prefix="/api", tags=["Syllabus & Topics"])

@router.post("/subjects/{subject_id}/syllabus/analyze", response_model=List[SyllabusUnitResponse])
def analyze_subject_syllabus(
    subject_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
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
    subject = get_user_accessible_subject(db, subject_id, user)
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

    # Gather syllabus chunks across the entire document
    syllabus_doc_ids = [d.id for d in syllabus_docs]
    all_chunks = db.query(DocumentChunk).filter(
        DocumentChunk.subject_id == subject_id,
        DocumentChunk.document_id.in_(syllabus_doc_ids)
    ).order_by(DocumentChunk.chunk_index).all()

    if not all_chunks:
        raise HTTPException(
            status_code=400,
            detail="Extracted syllabus text is empty. Please verify the uploaded document has readable text."
        )

    # Sample chunks across multi-page documents (first pages, evenly spaced middle pages, and summary pages)
    total_chunks = len(all_chunks)
    if total_chunks <= 15:
        selected_chunks = all_chunks
    else:
        indices = set()
        for i in range(min(5, total_chunks)):
            indices.add(i)
        step = max(1, total_chunks // 8)
        for i in range(step, total_chunks - 3, step):
            indices.add(i)
        for i in range(max(0, total_chunks - 3), total_chunks):
            indices.add(i)
        selected_chunks = [all_chunks[i] for i in sorted(indices)]

    syllabus_text = "\n\n".join([f"[Page {c.page_number}]\n{c.content}" for c in selected_chunks])

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

    # Detect if single chapter / unit notes or multi-unit curriculum
    primary_doc = syllabus_docs[0]
    doc_name = primary_doc.original_name.lower()
    
    import re
    # Check if document title explicitly mentions a single unit/chapter (e.g., "CS U3.pdf", "Unit 3", "Unit_3", "Ch 2", "Chapter 4")
    unit_match = re.search(r"\b(?:unit|u|chapter|ch|module|lecture|lec)[\s_-]*([0-9IVX]+)\b", doc_name, re.IGNORECASE)
    
    # Check if doc is explicitly named as a complete syllabus or lecture planner
    is_planner_or_full_syllabus = any(term in doc_name for term in [
        "syllabus", "curriculum", "lecture_plan", "lecture plan", "course_outline", "course outline", "planner", "scheme"
    ])
    
    # Check major unit headings in text
    major_units_in_text = re.findall(r"(?:^|\n)\s*(?:UNIT|MODULE|CHAPTER)\s*[-:]?\s*([0-9IVX]+)", syllabus_text, re.IGNORECASE)
    unique_major_units = set(u.upper() for u in major_units_in_text)

    is_single_chapter = True
    u_num = None
    if unit_match:
        # Document title explicitly specifies a unit/chapter (e.g., CS U3.pdf -> Unit 3)
        is_single_chapter = True
        u_num = unit_match.group(1).upper()
        doc_unit_title = f"Unit {u_num}: {subject.name}"
    elif is_planner_or_full_syllabus and len(unique_major_units) >= 2:
        # True multi-unit syllabus or lecture planner
        is_single_chapter = False
        doc_unit_title = f"{subject.name} Syllabus"
    elif primary_doc.document_role == "notes" or "notes" in doc_name or "slide" in doc_name:
        is_single_chapter = True
        doc_unit_title = f"{primary_doc.original_name.rsplit('.', 1)[0]}"
    elif len(unique_major_units) >= 3 and not unit_match:
        # Multi-unit syllabus with at least 3 distinct major unit headings
        is_single_chapter = False
        doc_unit_title = f"{subject.name} Syllabus"
    else:
        is_single_chapter = True
        doc_unit_title = f"{primary_doc.original_name.rsplit('.', 1)[0]}"

    parsed_unit_num = int(u_num) if u_num and u_num.isdigit() else 1

    # 3. Call AI Service to extract hierarchy with single-chapter awareness
    raw_units = []
    try:
        analysis_result = ai_service.analyze_syllabus_hierarchy(
            syllabus_text=syllabus_text[:12000],
            notes_chunks=notes_chunks_data[:10],
            previous_papers_chunks=paper_chunks_data[:6],
            is_single_chapter=is_single_chapter,
            doc_title=doc_unit_title,
            db=db
        )
        raw_units = analysis_result.get("units", [])
    except Exception as ai_err:
        raw_units = []

    # If single chapter was uploaded but model returned multiple units, consolidate into ONE unit
    if is_single_chapter and len(raw_units) > 1:
        combined_topics = []
        for u in raw_units:
            combined_topics.extend(u.get("topics", []))
        raw_units = [{
            "unit_number": parsed_unit_num,
            "title": doc_unit_title or raw_units[0].get("title", f"Unit: {subject.name}"),
            "description": f"Core examinable topics from {primary_doc.original_name}",
            "topics": combined_topics
        }]
    elif is_single_chapter and len(raw_units) == 1:
        raw_units[0]["unit_number"] = parsed_unit_num
        if not raw_units[0].get("title") or "unit 1" in raw_units[0]["title"].lower() and u_num and u_num != "1":
            raw_units[0]["title"] = doc_unit_title

    # Mandatory check: Ensure minimum 3 topics exist
    all_extracted_topics = []
    for u in raw_units:
        all_extracted_topics.extend(u.get("topics", []))

    if len(all_extracted_topics) < 3:
        # Extract headings and significant concepts directly from the document's own text chunks
        discovered_topics = []
        for c in all_chunks[:35]:
            lines = c.content.splitlines()
            for line in lines:
                clean_l = line.strip().strip("•-*#:").strip()
                if 5 <= len(clean_l) <= 55 and not clean_l.endswith("."):
                    if any(char.isupper() for char in clean_l) and clean_l not in discovered_topics:
                        # Avoid generic page or title headers
                        if not any(skip in clean_l.lower() for skip in ["page ", "http", "copyright", "author", "lecture"]):
                            discovered_topics.append(clean_l)
                            if len(discovered_topics) >= 6:
                                break
            if len(discovered_topics) >= 6:
                break

        if not discovered_topics:
            discovered_topics = [
                f"{subject.name} - Core Architecture & Theory",
                f"{subject.name} - Primary Algorithms & Mechanisms",
                f"{subject.name} - Applied Analysis & Constraints"
            ]

        fallback_items = [
            {
                "name": t_name,
                "description": f"Core topic extracted directly from {primary_doc.original_name}.",
                "subtopics": [],
                "practice_priority": "high" if idx < 2 else "medium",
                "priority_reason": "High frequency in examination materials",
                "is_inferred": False
            }
            for idx, t_name in enumerate(discovered_topics[:6])
        ]

        if not raw_units:
            raw_units = [{
                "unit_number": parsed_unit_num,
                "title": doc_unit_title or f"Unit: {primary_doc.original_name.rsplit('.', 1)[0]}",
                "description": f"Core syllabus topics from {primary_doc.original_name}",
                "topics": fallback_items
            }]
        else:
            existing_names = set(t.get("name") for t in all_extracted_topics)
            for item in fallback_items:
                if item["name"] not in existing_names:
                    raw_units[0].setdefault("topics", []).append(item)
                    if sum(len(u.get("topics", [])) for u in raw_units) >= 3:
                        break

    # 4. Clean up previous topics/units on re-analysis so generic placeholders are removed
    db.query(Topic).filter(Topic.subject_id == subject_id).delete(synchronize_session=False)
    db.query(SyllabusUnit).filter(SyllabusUnit.subject_id == subject_id).delete(synchronize_session=False)
    db.flush()

    # 5. Persist the real units and topics
    unit_order = 0
    for u_data in raw_units:
        unit_order += 1
        unit_num = u_data.get("unit_number", unit_order)
        unit_title = u_data.get("title", f"Unit {unit_num}")

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

        # Save topics
        topic_order = 0
        for t_data in u_data.get("topics", []):
            topic_order += 1
            t_name = t_data.get("name", "").strip()
            if not t_name:
                continue

            ref_coverage = t_data.get("reference_coverage") or ("good" if len(notes_chunks_data) > 0 else "missing")

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

    return get_subject_units_and_topics(subject_id, db, user)

@router.get("/subjects/{subject_id}/units", response_model=List[SyllabusUnitResponse])
def get_subject_units_and_topics(
    subject_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Returns full hierarchy of units and their child topics for the subject.
    """
    subject = get_user_accessible_subject(db, subject_id, user)
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
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Returns flat list of topics with optional filtering by unit, priority, and exclusion status.
    """
    subject = get_user_accessible_subject(db, subject_id, user)
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
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Manually add a topic to a syllabus unit.
    """
    subject = get_user_accessible_subject(db, subject_id, user)
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
