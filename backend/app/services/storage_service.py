import os
import re
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from backend.app.config import settings

class StorageService:
    def __init__(self, base_dir: Path = settings.storage_dir):
        self.base_dir = base_dir
        self.storage_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        # Strip path traversal and weird chars
        base = os.path.basename(filename)
        safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
        return safe or "document.pdf"

    async def save_file(self, subject_id: str, file: UploadFile) -> tuple[str, str, int, str]:
        """
        Validates and saves file in subject-isolated directory using memory-efficient chunked streaming.
        Supports large PDF uploads up to max_upload_size_bytes (default 100MB).
        Returns (stored_filename, absolute_path, file_size, mime_type)
        """
        mime = file.content_type or "application/octet-stream"
        filename = file.filename or "upload"
        ext = os.path.splitext(filename)[1].lower()

        if ext not in [".pdf", ".txt"]:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Only searchable .pdf and .txt files are accepted."
            )

        subject_dir = self.base_dir / subject_id
        subject_dir.mkdir(parents=True, exist_ok=True)

        unique_id = str(uuid.uuid4())[:8]
        safe_name = f"{unique_id}_{self.sanitize_filename(filename)}"
        target_path = subject_dir / safe_name

        max_bytes = settings.max_upload_size_bytes
        file_size = 0

        with open(target_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1MB buffer
                file_size += len(chunk)
                if file_size > max_bytes:
                    f.close()
                    if target_path.exists():
                        target_path.unlink()
                    limit_mb = max_bytes // (1024 * 1024)
                    raise HTTPException(
                        status_code=400,
                        detail=f"File exceeds maximum allowed size of {limit_mb}MB."
                    )
                f.write(chunk)

        return safe_name, str(target_path), file_size, mime

    def delete_file(self, file_path: str) -> bool:
        try:
            p = Path(file_path)
            if p.exists() and p.is_file():
                p.unlink()
                return True
        except Exception:
            pass
        return False

storage_service = StorageService()
