"""Seed the memory system with chat history from the initial Cairn integration session."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine, Base, SessionLocal
from app.memory.models import ChatMessage, Decision
import app.models  # noqa: ensure all models registered
import app.memory.models  # noqa

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

SESSION_ID = "cairn-integration-2026-03-30"

# Check if already seeded
existing = db.query(ChatMessage).filter_by(session_id=SESSION_ID).count()
if existing > 0:
    print(f"Session {SESSION_ID} already has {existing} messages — skipping seed.")
    db.close()
    sys.exit(0)

# ---------------------------------------------------------------------------
# Chat history from the Cairn integration session
# ---------------------------------------------------------------------------

messages = [
    ("user", "Convert our next app — a personalised memorial maker — into our Cairn architecture (semantic memory using cosine similarity, BM25). The GitHub repo is https://github.com/NBNEORIGIN/memorials and the local directory is D:\\memorials."),
    ("assistant", "Cloned the repo and explored the full codebase. It's a FastAPI + Next.js 16 memorial product generator with 11 DB models, 7 SVG processor modules (22 registered variants), Amazon order ingestion, admin dashboard, Docker deployment. No tests, hardcoded SMTP credentials, stray files."),
    ("assistant", "Phase 1 complete — registered memorials in Cairn:\n- Created projects/memorials/config.json (permissions, indexing rules, model preferences)\n- Created projects/memorials/core.md (6 non-negotiable rules, domain vocabulary, architecture)\n- Added memorials to CAIRN_PROTOCOL.md project registry table"),
    ("assistant", "Phase 2 complete — fixed critical issues:\n- Extracted hardcoded SMTP credentials (toby@nbnesigns.com / !49Monkswood) from bugreport.py to pydantic-settings env vars\n- Fixed GRAPHICS_DIR default from Google Drive path to ./assets/graphics\n- Removed stray -w file (21KB HTML dump from shell redirect error)\n- Updated .env.example with all new vars"),
    ("assistant", "Phase 3 complete — added pytest scaffold:\n- conftest.py with in-memory SQLite + TestClient fixtures\n- test_health.py: GET /api/health returns 200\n- test_processors.py: all 22 processor keys registered correctly\n- 3/3 tests passing"),
    ("user", "Create semantic memory with cosine similarity and BM25 for this project. Include chat history from here. When done repush to git."),
    ("assistant", "Built the full semantic memory system:\n\n1. memory/models.py — MemoryChunk (embeddings stored as JSON), ChatMessage, Decision\n2. memory/embeddings.py — Ollama (nomic-embed-text, 768-dim) with sentence-transformers (all-MiniLM-L6-v2, 384-dim) fallback, numpy cosine similarity\n3. memory/indexer.py — AST-based Python chunking, regex TypeScript chunking, markdown H2 sections, 40-line sliding window fallback. SHA256 deduplication.\n4. memory/retriever.py — HybridRetriever with BM25 (rank_bm25) + cosine similarity merged via Reciprocal Rank Fusion (RRF k=60). Falls back: hybrid → BM25 only → cosine only → keyword LIKE.\n5. memory/store.py — chat history and decision recording\n6. routers/memory.py — API endpoints: /api/memory/retrieve, /api/memory/index, /api/memory/chat, /api/memory/sessions, /api/memory/decisions, /api/memory/status\n\nAll 9 tests passing (3 original + 6 memory tests)."),
]

for role, content in messages:
    db.add(ChatMessage(
        session_id=SESSION_ID,
        role=role,
        content=content,
        model_used="claude-opus-4-6" if role == "assistant" else "",
    ))

# ---------------------------------------------------------------------------
# Decisions from this session
# ---------------------------------------------------------------------------

decisions = [
    {
        "decision_type": "architecture",
        "description": "Registered memorials in Cairn sovereign memory architecture",
        "reasoning": "Enables semantic retrieval over the memorials codebase, decision logging, and chat history persistence. Follows the same pattern as phloe and render projects.",
        "files_affected": ["projects/memorials/config.json", "projects/memorials/core.md", "CAIRN_PROTOCOL.md"],
    },
    {
        "decision_type": "fix",
        "description": "Extracted hardcoded SMTP credentials to environment variables",
        "reasoning": "Plaintext password in source code committed to git. Moved to pydantic-settings with .env support. Old password in git history — rotation needed.",
        "files_affected": ["backend/app/config.py", "backend/app/routers/bugreport.py", "backend/.env.example"],
    },
    {
        "decision_type": "fix",
        "description": "Changed GRAPHICS_DIR default from Google Drive path to ./assets/graphics",
        "reasoning": "Previous default only worked on one machine and auto-created deep phantom directory trees elsewhere. New default points to bundled assets in the repo.",
        "files_affected": ["backend/app/config.py"],
    },
    {
        "decision_type": "architecture",
        "description": "Built standalone semantic memory system with hybrid BM25 + cosine retrieval",
        "reasoning": "Follows Cairn pattern: AST-based chunking, nomic-embed-text embeddings via Ollama with sentence-transformers fallback, BM25 + cosine merged via RRF. SQLite-compatible (embeddings stored as JSON, cosine computed via numpy). No pgvector dependency required.",
        "files_affected": [
            "backend/app/memory/models.py",
            "backend/app/memory/embeddings.py",
            "backend/app/memory/indexer.py",
            "backend/app/memory/retriever.py",
            "backend/app/memory/store.py",
            "backend/app/routers/memory.py",
            "backend/app/main.py",
        ],
    },
    {
        "decision_type": "rejected",
        "description": "Rejected pgvector as embedding storage for memorials",
        "reasoning": "Memorials uses SQLite in development and the codebase is small enough that numpy cosine similarity over JSON-stored embeddings is fast and sufficient. pgvector would add a PostgreSQL extension dependency for minimal benefit at this scale.",
        "files_affected": [],
    },
]

for dec in decisions:
    db.add(Decision(
        session_id=SESSION_ID,
        decision_type=dec["decision_type"],
        description=dec["description"],
        reasoning=dec["reasoning"],
        files_affected=dec["files_affected"],
    ))

db.commit()
print(f"Seeded {len(messages)} chat messages and {len(decisions)} decisions for session {SESSION_ID}.")
db.close()
