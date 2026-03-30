"""SQLAlchemy models for the semantic memory system."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, JSON, Index,
)
from app.database import Base


class MemoryChunk(Base):
    """Indexed code chunk with embedding for semantic search."""
    __tablename__ = "memory_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(500), nullable=False)
    chunk_content = Column(Text, nullable=False)
    chunk_type = Column(String(50), nullable=False)  # function, class, section, window
    chunk_name = Column(String(200), nullable=True)
    content_hash = Column(String(64), nullable=False)
    embedding = Column(JSON, nullable=True)  # stored as list[float]
    last_modified = Column(Float, nullable=True)  # unix timestamp
    indexed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_memory_chunks_file", "file_path"),
        Index("idx_memory_chunks_hash", "content_hash"),
    )


class ChatMessage(Base):
    """Conversation history for development sessions."""
    __tablename__ = "chat_messages"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, default=0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_chat_session", "session_id"),
    )


class Decision(Base):
    """Architectural and implementation decisions — institutional memory."""
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=True)
    decision_type = Column(String(50), nullable=False)  # architecture, fix, feature, rejected
    description = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=True)
    files_affected = Column(JSON, default=list)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_decisions_type", "decision_type"),
    )
