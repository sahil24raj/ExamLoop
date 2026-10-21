from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.models import Concept, Document, DocumentChunk, Subject
from backend.app.schemas import ConceptResponse, ConceptUpdate
from backend.app.services.ai_service import ai_service
from backend.app.routers.subjects import get_or_create_default_user

router = APIRouter(prefix="/api", tags=["Concepts"])

@router.post("/subjects/{subject_id}/concepts/extract", response_model=List[ConceptResponse])
def extract_concepts_for_subject(subject_id: str, db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Get active documents
    active_docs = db.query(Document).filter(
        Document.subject_id == subject_id,
        Document.is_deleted == False,
        Document.status == "ready"
    ).all()

    if not active_docs:
        raise HTTPException(
            status_code=400,
            detail="No ready documents found. Please upload at least one study notes file first."
        )

    doc_ids = [d.id for d in active_docs]
    doc_map = {d.id: d for d in active_docs}

    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.subject_id == subject_id,
        DocumentChunk.document_id.in_(doc_ids)
    ).order_by(DocumentChunk.chunk_index).all()

    chunks_data = [
        {
            "id": c.id,
            "document_id": c.document_id,
            "page_number": c.page_number,
            "content": c.content
        }
        for c in chunks
    ]

    extracted = ai_service.extract_concepts(chunks_data, db=db)

    # Persist concepts
    saved_concepts = []
    for item in extracted:
        # Check if concept with similar name already exists for this subject
        existing = db.query(Concept).filter(
            Concept.subject_id == subject_id,
            Concept.name == item.get("name")
        ).first()

        if existing:
            saved_concepts.append(existing)
            continue

        # Match supporting chunks
        keywords = [k.lower() for k in item.get("keywords", [])]
        matched_chunks = []
        source_refs = []

        for c in chunks:
            c_text = c.content.lower()
            if any(k in c_text for k in keywords) or (item.get("supporting_pages") and c.page_number in item["supporting_pages"]):
                matched_chunks.append(c.id)
                if len(source_refs) < 2:
                    doc = doc_map.get(c.document_id)
                    source_refs.append({
                        "chunk_id": c.id,
                        "document_id": c.document_id,
                        "filename": doc.original_name if doc else "Document",
                        "page_number": c.page_number,
                        "excerpt": c.content[:300] + ("..." if len(c.content) > 300 else "")
                    })

        concept = Concept(
            subject_id=subject_id,
            name=item.get("name", "Extracted Concept"),
            description=item.get("description", "Concept extracted from uploaded study materials."),
            supporting_chunk_ids=matched_chunks[:5],
            source_references=source_refs or [{
                "chunk_id": chunks[0].id if chunks else None,
                "document_id": chunks[0].document_id if chunks else "",
                "filename": doc_map.get(chunks[0].document_id).original_name if chunks else "Notes",
                "page_number": chunks[0].page_number if chunks else 1,
                "excerpt": chunks[0].content[:200] if chunks else ""
            }],
            is_student_edited=False,
            is_excluded=False
        )
        db.add(concept)
        db.commit()
        db.refresh(concept)
        saved_concepts.append(concept)

    return saved_concepts

@router.get("/subjects/{subject_id}/concepts", response_model=List[ConceptResponse])
def list_concepts(subject_id: str, db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    concepts = db.query(Concept).filter(Concept.subject_id == subject_id).all()
    return concepts

@router.put("/concepts/{concept_id}", response_model=ConceptResponse)
def update_concept(concept_id: str, payload: ConceptUpdate, db: Session = Depends(get_db)):
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    if payload.name is not None and payload.name.strip():
        concept.name = payload.name.strip()
        concept.is_student_edited = True
    if payload.description is not None:
        concept.description = payload.description.strip()
        concept.is_student_edited = True
    if payload.is_excluded is not None:
        concept.is_excluded = payload.is_excluded

    db.commit()
    db.refresh(concept)
    return concept
