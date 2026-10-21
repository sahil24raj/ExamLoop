import os
from pathlib import Path
from typing import List, Dict, Any
import pymupdf

class DocumentExtractionError(Exception):
    pass

class DocumentService:
    @staticmethod
    def extract_from_pdf(file_path: str) -> tuple[int, List[Dict[str, Any]]]:
        """
        Extracts text from PDF page by page using PyMuPDF.
        Returns (page_count, list of page dicts: [{'page_number': int, 'text': str}])
        Raises DocumentExtractionError if file cannot be opened or is scanned/empty.
        """
        path = Path(file_path)
        if not path.exists():
            raise DocumentExtractionError(f"File not found: {file_path}")

        try:
            doc = pymupdf.open(str(path))
        except Exception as e:
            raise DocumentExtractionError(f"Failed to open PDF document: {str(e)}")

        pages_data = []
        total_text_length = 0
        page_count = len(doc)

        for page_idx in range(page_count):
            page = doc[page_idx]
            page_text = page.get_text("text").strip()
            total_text_length += len(page_text)
            pages_data.append({
                "page_number": page_idx + 1,
                "text": page_text
            })

        doc.close()

        # Check for image-only or empty PDF
        if total_text_length < 50:
            raise DocumentExtractionError(
                "Document appears to be an image-only or scanned PDF without searchable text. "
                "Please upload a searchable text PDF or a .txt notes file."
            )

        return page_count, pages_data

    @staticmethod
    def extract_from_txt(file_path: str) -> tuple[int, List[Dict[str, Any]]]:
        """
        Extracts plain text.
        Returns (1, [{'page_number': 1, 'text': full_text}])
        """
        path = Path(file_path)
        if not path.exists():
            raise DocumentExtractionError(f"File not found: {file_path}")

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
        except Exception as e:
            raise DocumentExtractionError(f"Failed to read text file: {str(e)}")

        if len(content) < 20:
            raise DocumentExtractionError("Text file is too short or empty.")

        return 1, [{"page_number": 1, "text": content}]

    @classmethod
    def chunk_extracted_pages(cls, pages_data: List[Dict[str, Any]], target_chunk_chars: int = 700) -> List[Dict[str, Any]]:
        """
        Splits page text into coherent chunks while strictly maintaining page_number and chunk_index.
        """
        chunks = []
        global_chunk_idx = 0

        for page in pages_data:
            page_num = page["page_number"]
            text = page["text"]
            
            # Split by paragraphs / double newlines
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

            current_chunk_text = ""
            for p in paragraphs:
                if len(current_chunk_text) + len(p) + 2 <= target_chunk_chars:
                    if current_chunk_text:
                        current_chunk_text += "\n\n" + p
                    else:
                        current_chunk_text = p
                else:
                    if current_chunk_text:
                        chunks.append({
                            "page_number": page_num,
                            "chunk_index": global_chunk_idx,
                            "content": current_chunk_text,
                            "token_estimate": len(current_chunk_text) // 4
                        })
                        global_chunk_idx += 1
                    current_chunk_text = p

            if current_chunk_text:
                chunks.append({
                    "page_number": page_num,
                    "chunk_index": global_chunk_idx,
                    "content": current_chunk_text,
                    "token_estimate": len(current_chunk_text) // 4
                })
                global_chunk_idx += 1

        return chunks

document_service = DocumentService()
