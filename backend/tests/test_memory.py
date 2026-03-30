"""Tests for the semantic memory system."""

import pytest


def test_memory_status(client):
    resp = client.get("/api/memory/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "chunks" in data
    assert "embedding_backend" in data
    assert "sessions" in data


def test_chat_message_roundtrip(client):
    # Store a message
    resp = client.post("/api/memory/chat", json={
        "session_id": "test-session-1",
        "role": "user",
        "content": "Hello, this is a test message",
        "model_used": "test",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "test-session-1"

    # Retrieve it
    resp = client.get("/api/memory/chat/test-session-1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    assert data["messages"][-1]["content"] == "Hello, this is a test message"
    assert data["messages"][-1]["role"] == "user"


def test_sessions_list(client):
    # Store messages in two sessions
    client.post("/api/memory/chat", json={
        "session_id": "session-a",
        "role": "user",
        "content": "Message in session A",
    })
    client.post("/api/memory/chat", json={
        "session_id": "session-b",
        "role": "assistant",
        "content": "Message in session B",
    })

    resp = client.get("/api/memory/sessions")
    assert resp.status_code == 200
    data = resp.json()
    session_ids = [s["session_id"] for s in data["sessions"]]
    assert "session-a" in session_ids
    assert "session-b" in session_ids


def test_decision_roundtrip(client):
    resp = client.post("/api/memory/decisions", json={
        "decision_type": "architecture",
        "description": "Use hybrid BM25 + cosine for retrieval",
        "reasoning": "Combines exact keyword matching with semantic understanding",
        "files_affected": ["app/memory/retriever.py"],
        "session_id": "test-session-1",
    })
    assert resp.status_code == 200
    assert resp.json()["decision_type"] == "architecture"

    resp = client.get("/api/memory/decisions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    assert any(d["description"].startswith("Use hybrid") for d in data["decisions"])


def test_decision_filter_by_type(client):
    client.post("/api/memory/decisions", json={
        "decision_type": "fix",
        "description": "Fixed SMTP credential leak",
    })
    client.post("/api/memory/decisions", json={
        "decision_type": "architecture",
        "description": "Added semantic memory system",
    })

    resp = client.get("/api/memory/decisions?decision_type=fix")
    assert resp.status_code == 200
    data = resp.json()
    assert all(d["decision_type"] == "fix" for d in data["decisions"])


def test_retrieve_empty_index(client):
    resp = client.get("/api/memory/retrieve?query=test+query")
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "test query"
    assert isinstance(data["results"], list)
