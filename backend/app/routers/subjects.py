from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.config import settings
from backend.app.models import Subject, User, Document, DocumentChunk, Concept
from backend.app.schemas import SubjectCreate, SubjectUpdate, SubjectResponse
from backend.app.fixtures.dbms_demo import DBMS_SAMPLE_TEXT, DBMS_FIXTURE_CONCEPTS
from backend.app.services.document_service import document_service
from backend.app.auth import get_current_user, get_or_create_default_user, get_user_accessible_subject

router = APIRouter(prefix="/api/subjects", tags=["Subjects"])

@router.post("", response_model=SubjectResponse)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    subject = Subject(
        user_id=user.id,
        name=payload.name,
        exam_date=payload.exam_date,
        preferred_duration_minutes=payload.preferred_duration_minutes,
        default_mcq_count=payload.default_mcq_count,
        default_subjective_count=payload.default_subjective_count,
        default_subjective_marks=payload.default_subjective_marks,
        syllabus_text=payload.syllabus_text
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject

@router.get("", response_model=List[SubjectResponse])
def list_subjects(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    subjects = db.query(Subject).filter(
        (Subject.user_id == user.id) | (Subject.user_id == settings.default_user_id)
    ).all()
    results = []
    for s in subjects:
        doc_count = db.query(Document).filter(Document.subject_id == s.id, Document.is_deleted == False).count()
        concept_count = db.query(Concept).filter(Concept.subject_id == s.id, Concept.is_excluded == False).count()
        results.append(
            SubjectResponse(
                id=s.id,
                user_id=s.user_id,
                name=s.name,
                exam_date=s.exam_date,
                preferred_duration_minutes=s.preferred_duration_minutes,
                default_mcq_count=s.default_mcq_count,
                default_subjective_count=s.default_subjective_count,
                default_subjective_marks=s.default_subjective_marks,
                syllabus_text=s.syllabus_text,
                created_at=s.created_at,
                document_count=doc_count,
                concept_count=concept_count,
                test_count=len(s.tests)
            )
        )
    return results

@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(
    subject_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    subject = get_user_accessible_subject(db, subject_id, user)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    doc_count = db.query(Document).filter(Document.subject_id == subject.id, Document.is_deleted == False).count()
    concept_count = db.query(Concept).filter(Concept.subject_id == subject.id, Concept.is_excluded == False).count()
    return SubjectResponse(
        id=subject.id,
        user_id=subject.user_id,
        name=subject.name,
        exam_date=subject.exam_date,
        preferred_duration_minutes=subject.preferred_duration_minutes,
        default_mcq_count=subject.default_mcq_count,
        default_subjective_count=subject.default_subjective_count,
        default_subjective_marks=subject.default_subjective_marks,
        syllabus_text=subject.syllabus_text,
        created_at=subject.created_at,
        document_count=doc_count,
        concept_count=concept_count,
        test_count=len(subject.tests)
    )

@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: str,
    payload: SubjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    subject = get_user_accessible_subject(db, subject_id, user)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    if payload.name is not None:
        subject.name = payload.name
    if payload.exam_date is not None:
        subject.exam_date = payload.exam_date
    if payload.preferred_duration_minutes is not None:
        subject.preferred_duration_minutes = payload.preferred_duration_minutes
    if payload.default_mcq_count is not None:
        subject.default_mcq_count = payload.default_mcq_count
    if payload.default_subjective_count is not None:
        subject.default_subjective_count = payload.default_subjective_count
    if payload.default_subjective_marks is not None:
        subject.default_subjective_marks = payload.default_subjective_marks
    if payload.syllabus_text is not None:
        subject.syllabus_text = payload.syllabus_text

    db.commit()
    db.refresh(subject)
    return subject

@router.post("/{subject_id}/seed-demo")
def seed_demo_data(
    subject_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Seeds verified DBMS sample notes and concepts for immediate demonstration.
    """
    subject = get_user_accessible_subject(db, subject_id, user)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Check if sample doc already exists
    existing_doc = db.query(Document).filter(
        Document.subject_id == subject.id,
        Document.original_name == "DBMS_Core_Exam_Notes.txt",
        Document.is_deleted == False
    ).first()

    if not existing_doc:
        # Create and write notes file
        subject_dir = settings.storage_dir / subject.id
        subject_dir.mkdir(parents=True, exist_ok=True)
        file_path = subject_dir / "DBMS_Core_Exam_Notes.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(DBMS_SAMPLE_TEXT)

        doc = Document(
            user_id=user.id,
            subject_id=subject.id,
            filename="DBMS_Core_Exam_Notes.txt",
            original_name="DBMS_Core_Exam_Notes.txt",
            file_size=len(DBMS_SAMPLE_TEXT.encode("utf-8")),
            mime_type="text/plain",
            file_path=str(file_path),
            page_count=4,
            status="ready"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Chunk by chapters/pages
        chapters = DBMS_SAMPLE_TEXT.split("---")
        for idx, chapter in enumerate(chapters):
            page_num = idx + 1
            chunks = document_service.chunk_extracted_pages([{"page_number": page_num, "text": chapter.strip()}])
            for c in chunks:
                chunk_entry = DocumentChunk(
                    document_id=doc.id,
                    subject_id=subject.id,
                    page_number=page_num,
                    chunk_index=c["chunk_index"],
                    content=c["content"],
                    token_estimate=c["token_estimate"]
                )
                db.add(chunk_entry)
        db.commit()

    # Seed concepts
    active_doc = existing_doc if existing_doc else doc
    existing_concepts = db.query(Concept).filter(Concept.subject_id == subject.id).all()
    if not existing_concepts and active_doc:
        for fc in DBMS_FIXTURE_CONCEPTS:
            concept = Concept(
                subject_id=subject.id,
                name=fc["name"],
                description=fc["description"],
                supporting_chunk_ids=[],
                source_references=[{
                    "document_id": active_doc.id,
                    "filename": active_doc.original_name,
                    "page_number": fc["supporting_pages"][0],
                    "excerpt": f"Study notes regarding {fc['name']}."
                }],
                is_student_edited=False,
                is_excluded=False
            )
            db.add(concept)
        db.commit()

    return {"message": "Demo DBMS notes and concepts successfully seeded."}

@router.post("/seed-demo")
def seed_global_demo(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    1-click endpoint to initialize default DBMS subject, notes, chunks, and concepts.
    """
    subject = db.query(Subject).filter(Subject.user_id == user.id, Subject.name.like("%DBMS%")).first()
    if not subject:
        subject = Subject(
            user_id=user.id,
            name="Database Management Systems (DBMS)",
            exam_date="2026-11-20",
            preferred_duration_minutes=20,
            default_mcq_count=3,
            default_subjective_count=2,
            default_subjective_marks=5,
            syllabus_text="Normalization (1NF, 2NF, 3NF, BCNF), SQL Joins, ACID Properties and Isolation levels, B+ Tree Indexing."
        )
        db.add(subject)
        db.commit()
        db.refresh(subject)
    
    seed_demo_data(subject.id, db)
    return {"status": "success", "subject_id": subject.id, "message": "DBMS Demo subject seeded successfully."}

@router.delete("/{subject_id}")
def delete_subject(subject_id: str, db: Session = Depends(get_db)):
    """
    Permanently deletes a subject/workspace and all its cascaded documents, chunks, topics, tests, attempts, and concept progress.
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Clean up ConceptProgress for concepts in this subject
    concept_ids = [c.id for c in subject.concepts]
    if concept_ids:
        from backend.app.models import ConceptProgress
        db.query(ConceptProgress).filter(ConceptProgress.concept_id.in_(concept_ids)).delete(synchronize_session=False)

    # Clean up document chunks
    doc_ids = [d.id for d in subject.documents]
    if doc_ids:
        db.query(DocumentChunk).filter(DocumentChunk.document_id.in_(doc_ids)).delete(synchronize_session=False)

    db.delete(subject)
    db.commit()
    return {"message": "Workspace deleted successfully."}

