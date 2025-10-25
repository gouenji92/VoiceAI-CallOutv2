from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from app.services.rag_service import rag_service
from app.dependencies import get_current_user_id


router = APIRouter()


class IngestPayload(BaseModel):
    content: str
    source: Optional[str] = None


@router.on_event("startup")
async def _build_index_on_startup():
    # Build index lazily on first request as well, but try early here
    try:
        rag_service.build_index()
    except Exception:
        # Avoid blocking startup if corpus is empty or missing
        pass


@router.get("/search", summary="RAG search", tags=["RAG"])
async def rag_search(q: str = Query(..., description="User query"), k: int = 3):
    """
    Public search endpoint to retrieve top-k passages.
    Returns empty results if knowledge base is empty (not an error).
    """
    try:
        results = rag_service.search(q, k=k)
        corpus_size = len(rag_service.documents)
        return {
            "query": q, 
            "k": k, 
            "results": results,
            "corpus_size": corpus_size,
            "message": "Knowledge base is empty. Add data via /ingest or files in data/knowledge_base/" if corpus_size == 0 else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", summary="Ingest knowledge", tags=["RAG"])
async def rag_ingest(payload: IngestPayload, current_user_id: str = Depends(get_current_user_id)):
    """Authenticated endpoint to ingest new knowledge text and rebuild index."""
    try:
        new_size = rag_service.ingest_text(payload.content, source=payload.source)
        return {"message": "ingested", "corpus_size": new_size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", summary="RAG status", tags=["RAG"])
async def rag_status():
    """Check RAG system status and corpus information."""
    try:
        rag_service.ensure_index()
        return {
            "provider": rag_service.provider,
            "corpus_size": len(rag_service.documents),
            "is_indexed": rag_service._is_built,
            "corpus_dir": rag_service.corpus_dir,
            "cache_enabled": rag_service.provider != "local",
            "message": "Add knowledge files to data/knowledge_base/ or use /ingest API" if len(rag_service.documents) == 0 else "RAG is ready"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
