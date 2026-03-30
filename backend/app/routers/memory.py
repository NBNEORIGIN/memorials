"""Memory API — semantic search, chat history, decisions, and indexing."""

import threading
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.memory import retriever as mem_retriever
from app.memory import store as mem_store
from app.memory import indexer as mem_indexer
from app.memory import embeddings as mem_embeddings
from app.memory.models import MemoryChunk

router = APIRouter(prefix="/api/memory", tags=["Memory"])

# Singleton retriever instance (caches BM25 index)
_retriever = mem_retriever.HybridRetriever()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatMessageIn(BaseModel):
    session_id: str
    role: str
    content: str
    model_used: str = ""
    tokens_used: int = 0


class DecisionIn(BaseModel):
    decision_type: str
    description: str
    reasoning: str = ""
    files_affected: list[str] = []
    session_id: Optional[str] = None


class IndexRequest(BaseModel):
    codebase_path: str = "D:/memorials"
    force_reindex: bool = False


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

@router.get("/retrieve")
def retrieve(
    query: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Hybrid BM25 + cosine similarity retrieval over indexed code chunks."""
    results = _retriever.retrieve(query, db, limit=limit)
    return {"query": query, "count": len(results), "results": results}


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

@router.get("/status")
def memory_status(db: Session = Depends(get_db)):
    """Return memory system status: chunk count, embedding backend, sessions."""
    chunk_count = db.query(MemoryChunk).count()
    embedded_count = db.query(MemoryChunk).filter(MemoryChunk.embedding.isnot(None)).count()
    embedding_status = mem_embeddings.check_available()
    sessions = mem_store.list_sessions(db)
    return {
        "chunks": chunk_count,
        "chunks_with_embeddings": embedded_count,
        "embedding_backend": embedding_status,
        "sessions": len(sessions),
    }


@router.post("/index")
def index_codebase(
    req: IndexRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Index the codebase for semantic search.

    Runs synchronously (blocks until complete). For large codebases,
    consider calling this once and letting the BM25 + cosine cache warm up.
    """
    result = mem_indexer.index_codebase(
        db=db,
        codebase_path=req.codebase_path,
        force_reindex=req.force_reindex,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------

@router.post("/chat")
def add_chat_message(msg: ChatMessageIn, db: Session = Depends(get_db)):
    """Store a chat message in the memory system."""
    saved = mem_store.add_message(
        db=db,
        session_id=msg.session_id,
        role=msg.role,
        content=msg.content,
        model_used=msg.model_used,
        tokens_used=msg.tokens_used,
    )
    return {"id": saved.id, "session_id": msg.session_id}


@router.get("/chat/{session_id}")
def get_chat_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get chat history for a session."""
    messages = mem_store.get_history(db, session_id, limit=limit)
    return {"session_id": session_id, "count": len(messages), "messages": messages}


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    """List all chat sessions with message counts."""
    sessions = mem_store.list_sessions(db)
    return {"count": len(sessions), "sessions": sessions}


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------

@router.post("/decisions")
def record_decision(dec: DecisionIn, db: Session = Depends(get_db)):
    """Record an architectural or implementation decision."""
    saved = mem_store.record_decision(
        db=db,
        decision_type=dec.decision_type,
        description=dec.description,
        reasoning=dec.reasoning,
        files_affected=dec.files_affected,
        session_id=dec.session_id,
    )
    return {"id": saved.id, "decision_type": dec.decision_type}


@router.get("/decisions")
def get_decisions(
    decision_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get recorded decisions, optionally filtered by type."""
    decisions = mem_store.get_decisions(db, decision_type=decision_type, limit=limit)
    return {"count": len(decisions), "decisions": decisions}
