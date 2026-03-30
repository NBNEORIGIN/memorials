"""Embedding generation — Ollama (nomic-embed-text) with sentence-transformers fallback."""

import logging
import os
from typing import Optional

import httpx
import numpy as np

logger = logging.getLogger(__name__)

MAX_CHUNK_CHARS = 1500  # safety limit for embedding model context

_st_model = None  # lazy-loaded sentence-transformers model


def _ollama_embed(text: str) -> Optional[list[float]]:
    """Generate embedding via Ollama's nomic-embed-text (768-dim)."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        resp = httpx.post(
            f"{base_url}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text},
            timeout=30,
        )
        resp.raise_for_status()
        emb = resp.json().get("embedding")
        if emb and len(emb) > 0:
            return emb
    except Exception as exc:
        logger.debug("Ollama embedding failed: %s", exc)
    return None


def _st_embed(text: str) -> Optional[list[float]]:
    """Generate embedding via sentence-transformers all-MiniLM-L6-v2 (384-dim)."""
    global _st_model
    try:
        if _st_model is None:
            from sentence_transformers import SentenceTransformer
            _st_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded sentence-transformers model: all-MiniLM-L6-v2")
        emb = _st_model.encode(text, show_progress_bar=False)
        return emb.tolist()
    except ImportError:
        logger.debug("sentence-transformers not installed")
    except Exception as exc:
        logger.debug("sentence-transformers embedding failed: %s", exc)
    return None


def embed(text: str) -> Optional[list[float]]:
    """
    Generate an embedding vector for the given text.

    Tries Ollama (nomic-embed-text, 768-dim) first, then falls back to
    sentence-transformers (all-MiniLM-L6-v2, 384-dim). Returns None if
    neither is available.
    """
    if len(text) > MAX_CHUNK_CHARS:
        text = text[:MAX_CHUNK_CHARS]

    # Try Ollama first (faster if running, and matches Cairn's embedding space)
    result = _ollama_embed(text)
    if result is not None:
        return result

    # Fall back to sentence-transformers (CPU, no server required)
    result = _st_embed(text)
    if result is not None:
        return result

    logger.warning("No embedding backend available")
    return None


def check_available() -> dict:
    """Check which embedding backends are available."""
    status = {"ollama": False, "sentence_transformers": False, "dims": 0}

    test = embed("test")
    if test is not None:
        status["dims"] = len(test)

    # Check Ollama specifically
    ollama_test = _ollama_embed("test")
    if ollama_test is not None:
        status["ollama"] = True

    # Check sentence-transformers
    try:
        import sentence_transformers  # noqa: F401
        status["sentence_transformers"] = True
    except ImportError:
        pass

    return status


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    dot = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))
