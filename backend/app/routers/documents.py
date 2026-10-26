import os
import logging
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.models import Document, DocumentChunk, Subject, User, Topic
from backend.app.schemas import DocumentResponse, DocumentChunkResponse
from backend.app.services.storage_service import storage_service
from backend.app.services.document_service import document_service, DocumentExtractionError
from backend.app.auth import get_current_user, get_user_accessible_subject

from pydantic import BaseModel

logger = logging.getLogger(__name__)

def _background_topic_extraction(subject_id: str, user_id: str):
    """Safely triggers syllabus topic analysis in the background without blocking file upload HTTP response."""
    try:
        from backend.app.database import SessionLocal
        from backend.app.models import Topic, User
        from backend.app.routers.topics import analyze_subject_syllabus
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return
            existing_topics_count = db.query(Topic).filter(Topic.subject_id == subject_id).count()
            if existing_topics_count == 0:
                analyze_subject_syllabus(subject_id=subject_id, db=db, user=user)
        finally:
            db.close()
    except Exception as e:
        logger.warning("Background topic extraction note: %s", e)

class PasteTextRequest(BaseModel):
    title: str = "Pasted Syllabus"
    content: str
    document_role: str = "syllabus" # "syllabus" | "notes" | "previous_paper"

router = APIRouter(prefix="/api", tags=["Documents"])

@router.post("/subjects/{subject_id}/documents/upload", response_model=DocumentResponse)
async def upload_document(
    subject_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_role: str = Form("notes"), # "syllabus" | "notes" | "previous_paper"
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    subject = get_user_accessible_subject(db, subject_id, user)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Save to isolated filesystem with streaming (supports up to 100MB)
    safe_name, abs_path, file_size, mime = await storage_service.save_file(subject_id, file)

    doc = Document(
        user_id=user.id,
        subject_id=subject.id,
        document_role=document_role,
        filename=safe_name,
        original_name=file.filename or safe_name,
        file_size=file_size,
        mime_type=mime,
        file_path=abs_path,
        status="extracting"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        ext = os.path.splitext(doc.original_name)[1].lower()
        if ext == ".pdf":
            page_count, pages_data = document_service.extract_from_pdf(abs_path)
        else:
            page_count, pages_data = document_service.extract_from_txt(abs_path)

        chunks_data = document_service.chunk_extracted_pages(pages_data)

        doc.page_count = page_count
        for c in chunks_data:
            chunk = DocumentChunk(
                document_id=doc.id,
                subject_id=subject.id,
                page_number=c["page_number"],
                chunk_index=c["chunk_index"],
                content=c["content"],
                token_estimate=c["token_estimate"]
            )
            db.add(chunk)

        doc.status = "ready"
        db.commit()
        db.refresh(doc)

        # Auto-trigger topic extraction in background if no topics exist yet for this subject
        existing_topics_count = db.query(Topic).filter(Topic.subject_id == subject_id).count()
        if existing_topics_count == 0:
            background_tasks.add_task(_background_topic_extraction, subject.id, user.id)

        return doc

    except DocumentExtractionError as e:
        doc.status = "failed"
        doc.error_message = str(e)
        db.commit()
        db.refresh(doc)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        doc.status = "failed"
        doc.error_message = f"Processing error: {str(e)}"
        db.commit()
        db.refresh(doc)
        raise HTTPException(status_code=500, detail=f"Unexpected extraction error: {str(e)}")

@router.post("/subjects/{subject_id}/documents/paste-text", response_model=DocumentResponse)
def paste_document_text(
    subject_id: str,
    payload: PasteTextRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    subject = get_user_accessible_subject(db, subject_id, user)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    text_content = payload.content.strip()
    if len(text_content) < 20:
        raise HTTPException(status_code=400, detail="Pasted text is too short. Please provide at least a few syllabus topics or notes.")

    # Save to disk
    import uuid
    safe_name = f"Pasted_{uuid.uuid4().hex[:8]}.txt"
    subject_dir = storage_service.base_dir / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)
    file_path = subject_dir / safe_name
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text_content)

    doc = Document(
        user_id=user.id,
        subject_id=subject.id,
        document_role=payload.document_role,
        filename=safe_name,
        original_name=payload.title if payload.title.endswith(".txt") else f"{payload.title}.txt",
        file_size=len(text_content.encode("utf-8")),
        mime_type="text/plain",
        file_path=str(file_path),
        page_count=1,
        status="ready"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Chunk text
    pages_data = [{"page_number": 1, "text": text_content}]
    chunks_data = document_service.chunk_extracted_pages(pages_data)
    for c in chunks_data:
        chunk = DocumentChunk(
            document_id=doc.id,
            subject_id=subject.id,
            page_number=c["page_number"],
            chunk_index=c["chunk_index"],
            content=c["content"],
            token_estimate=c["token_estimate"]
        )
        db.add(chunk)
    
    # If this is syllabus, also update subject.syllabus_text
    if payload.document_role == "syllabus":
        subject.syllabus_text = text_content

    db.commit()
    db.refresh(doc)

    # Auto-trigger topic extraction in background if no topics exist yet for this subject
    existing_topics_count = db.query(Topic).filter(Topic.subject_id == subject_id).count()
    if existing_topics_count == 0:
        background_tasks.add_task(_background_topic_extraction, subject.id, user.id)

    return doc

@router.get("/subjects/{subject_id}/documents", response_model=List[DocumentResponse])
def list_documents(
    subject_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    subject = get_user_accessible_subject(db, subject_id, user)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    docs = db.query(Document).filter(
        Document.subject_id == subject_id,
        Document.is_deleted == False
    ).order_by(Document.created_at.desc()).all()
    return docs

@router.get("/documents/{document_id}/chunks", response_model=List[DocumentChunkResponse])
def get_document_chunks(
    document_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or doc.is_deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()
    return chunks

@router.get("/documents/{document_id}/file")
def get_document_file(
    document_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or doc.is_deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Physical file missing from storage.")

    return FileResponse(
        path=doc.file_path,
        filename=doc.original_name,
        media_type=doc.mime_type
    )

@router.delete("/documents/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Deletes the document and its chunks so it is immediately removed from the subject.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete all associated document chunks
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete(synchronize_session=False)
    
    # Delete the document record
    db.delete(doc)
    db.commit()
    return {"message": "Document and associated chunks deleted successfully."}

