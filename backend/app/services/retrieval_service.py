import re
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models import Document, DocumentChunk
from backend.app.config import settings

class RetrievalService:
    def __init__(self):
        self.active_mode = "lexical_bm25"
        if settings.embedding_provider != "lexical" and settings.embedding_api_key:
            self.active_mode = "semantic_vector"

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "active_retrieval_mode": self.active_mode,
            "embedding_provider": settings.embedding_provider,
            "embedding_model": settings.embedding_model,
            "is_vector_enabled": self.active_mode == "semantic_vector"
        }

    def tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\b\w{2,}\b", text)]

    def search_subject_chunks(
        self,
        db: Session,
        subject_id: str,
        query: str,
        top_k: int = 5,
        concept_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Subject-scoped retrieval strictly constrained to non-deleted, ready documents
        under the specified subject.
        """
        # Fetch active documents
        active_docs = db.query(Document).filter(
            Document.subject_id == subject_id,
            Document.is_deleted == False,
            Document.status == "ready"
        ).all()

        if not active_docs:
            return []

        doc_map = {d.id: d for d in active_docs}
        active_doc_ids = list(doc_map.keys())

        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.subject_id == subject_id,
            DocumentChunk.document_id.in_(active_doc_ids)
        ).all()

        if not chunks:
            return []

        query_terms = self.tokenize(query)
        if not query_terms:
            # Fallback to returning first chunks if query is empty
            return [
                {
                    "chunk_id": c.id,
                    "document_id": c.document_id,
                    "filename": doc_map[c.document_id].original_name,
                    "page_number": c.page_number,
                    "supporting_text": c.content[:400] + ("..." if len(c.content) > 400 else ""),
                    "score": 1.0
                }
                for c in chunks[:top_k]
            ]

        # BM25-style lexical scoring
        scored_results = []
        doc_count = len(chunks)
        avg_len = sum(len(c.content) for c in chunks) / max(1, doc_count)
        k1 = 1.5
        b = 0.75

        # Calculate term document frequencies
        term_dfs = {}
        chunk_token_cache = []
        for c in chunks:
            tokens = self.tokenize(c.content)
            chunk_token_cache.append((c, tokens))
            for term in set(query_terms):
                if term in tokens:
                    term_dfs[term] = term_dfs.get(term, 0) + 1

        for c, tokens in chunk_token_cache:
            score = 0.0
            doc_len = len(c.content)
            token_counts = {}
            for t in tokens:
                token_counts[t] = token_counts.get(t, 0) + 1

            for term in query_terms:
                if term in token_counts:
                    tf = token_counts[term]
                    df = term_dfs.get(term, 0)
                    idf = math.log((doc_count - df + 0.5) / (df + 0.5) + 1.0)
                    term_score = idf * ((tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_len))))
                    score += term_score

            if score > 0:
                doc = doc_map.get(c.document_id)
                scored_results.append({
                    "chunk_id": c.id,
                    "document_id": c.document_id,
                    "filename": doc.original_name if doc else "Document",
                    "page_number": c.page_number,
                    "supporting_text": c.content,
                    "score": round(score, 3)
                })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

retrieval_service = RetrievalService()
