"""Memory store — chat history, decisions, and session management."""

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.memory.models import ChatMessage, Decision


def add_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    model_used: str = "",
    tokens_used: int = 0,
) -> ChatMessage:
    """Store a conversation message."""
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        model_used=model_used,
        tokens_used=tokens_used,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_history(
    db: Session,
    session_id: str,
    limit: int = 50,
) -> list[dict]:
    """Get recent chat history for a session, oldest first."""
    rows = (
        db.query(ChatMessage)
        .filter_by(session_id=session_id)
        .order_by(ChatMessage.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "role": r.role,
            "content": r.content,
            "model_used": r.model_used,
            "tokens_used": r.tokens_used,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in reversed(rows)
    ]


def list_sessions(db: Session) -> list[dict]:
    """List all unique session IDs with message counts and date range."""
    from sqlalchemy import func

    rows = (
        db.query(
            ChatMessage.session_id,
            func.count(ChatMessage.id).label("message_count"),
            func.min(ChatMessage.timestamp).label("started_at"),
            func.max(ChatMessage.timestamp).label("last_message_at"),
        )
        .group_by(ChatMessage.session_id)
        .order_by(func.max(ChatMessage.timestamp).desc())
        .all()
    )
    return [
        {
            "session_id": r.session_id,
            "message_count": r.message_count,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "last_message_at": r.last_message_at.isoformat() if r.last_message_at else None,
        }
        for r in rows
    ]


def record_decision(
    db: Session,
    decision_type: str,
    description: str,
    reasoning: str = "",
    files_affected: Optional[list[str]] = None,
    session_id: Optional[str] = None,
) -> Decision:
    """Record an architectural or implementation decision."""
    dec = Decision(
        session_id=session_id,
        decision_type=decision_type,
        description=description,
        reasoning=reasoning,
        files_affected=files_affected or [],
    )
    db.add(dec)
    db.commit()
    db.refresh(dec)
    return dec


def get_decisions(
    db: Session,
    decision_type: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """Get recorded decisions, optionally filtered by type."""
    query = db.query(Decision).order_by(Decision.id.desc())
    if decision_type:
        query = query.filter_by(decision_type=decision_type)
    rows = query.limit(limit).all()
    return [
        {
            "id": r.id,
            "session_id": r.session_id,
            "decision_type": r.decision_type,
            "description": r.description,
            "reasoning": r.reasoning,
            "files_affected": r.files_affected,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]
