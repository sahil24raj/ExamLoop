import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.models import Document, DocumentChunk, Subject, User
from backend.app.schemas import DocumentResponse, DocumentChunkResponse
from backend.app.services.storage_service import storage_service
from backend.app.services.document_service import document_service, DocumentExtractionError
from backend.app.routers.subjects import get_or_create_default_user

from pydantic import BaseModel

class PasteTextRequest(BaseModel):
    title: str = "Pasted Syllabus"
    content: str
    document_role: str = "syllabus" # "syllabus" | "notes" | "previous_paper"

router = APIRouter(prefix="/api", tags=["Documents"])

@router.post("/subjects/{subject_id}/documents/upload", response_model=DocumentResponse)
async def upload_document(
    subject_id: str,
    file: UploadFile = File(...),
    document_role: str = Form("notes"), # "syllabus" | "notes" | "previous_paper"
    db: Session = Depends(get_db)
):
    user = get_or_create_default_user(db)
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Validate file size (max 15MB)
    MAX_FILE_BYTES = 15 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail="File size exceeds the 15MB limit. Please upload a smaller PDF or TXT file.")
    await file.seek(0)

    # Save to isolated filesystem
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
    db: Session = Depends(get_db)
):
    user = get_or_create_default_user(db)
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == user.id).first()
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
    return doc

@router.get("/subjects/{subject_id}/documents", response_model=List[DocumentResponse])
def list_documents(subject_id: str, db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    docs = db.query(Document).filter(
        Document.subject_id == subject_id,
        Document.user_id == user.id,
        Document.is_deleted == False
    ).order_by(Document.created_at.desc()).all()
    return docs

@router.get("/documents/{document_id}/chunks", response_model=List[DocumentChunkResponse])
def get_document_chunks(document_id: str, db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
    if not doc or doc.is_deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index).all()
    return chunks

@router.get("/documents/{document_id}/file")
def get_document_file(document_id: str, db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
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

