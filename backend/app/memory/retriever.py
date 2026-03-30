"""Hybrid retriever — BM25 + cosine similarity with Reciprocal Rank Fusion."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, replace
from typing import Optional

from sqlalchemy.orm import Session

from app.memory.models import MemoryChunk
from app.memory.embeddings import embed, cosine_similarity

logger = logging.getLogger(__name__)

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None
    logger.info("rank_bm25 not installed — BM25 search disabled, using token overlap")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RetrievedChunk:
    file: str
    content: str
    chunk_type: str
    score: float = 0.0
    bm25_rank: Optional[int] = None
    cosine_rank: Optional[int] = None
    chunk_name: Optional[str] = None

    @property
    def match_quality(self) -> str:
        if self.bm25_rank is not None and self.cosine_rank is not None:
            return "exact+semantic"
        if self.bm25_rank is not None:
            return "exact"
        return "semantic"

    @property
    def dedupe_key(self) -> str:
        head = self.content[:120]
        return f"{self.file}:{self.chunk_type}:{head}"


# ---------------------------------------------------------------------------
# Simple token-overlap fallback for when rank_bm25 is not installed
# ---------------------------------------------------------------------------

class _TokenOverlapScorer:
    """Minimal BM25 stand-in using token set overlap."""

    def __init__(self, corpus: list[list[str]]):
        self.corpus = corpus

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        q_set = set(query_tokens)
        scores = []
        for doc_tokens in self.corpus:
            overlap = len(q_set & set(doc_tokens))
            scores.append(overlap / max(len(q_set), 1))
        return scores


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    text = text.lower()
    tokens = re.findall(r"[a-z0-9_./\-]+", text)
    return [tok for tok in tokens if len(tok) > 1]


# ---------------------------------------------------------------------------
# HybridRetriever
# ---------------------------------------------------------------------------

class HybridRetriever:
    CACHE_TTL_SECONDS = 30.0

    def __init__(
        self,
        bm25_top_k: int = 20,
        cosine_top_k: int = 20,
        rrf_k: int = 60,
    ):
        self.bm25_top_k = bm25_top_k
        self.cosine_top_k = cosine_top_k
        self.rrf_k = rrf_k
        self._bm25_cache = None
        self._bm25_corpus: list[RetrievedChunk] = []
        self._bm25_built_at: float = 0.0

    # -------------------------------------------------------------------
    # BM25 index
    # -------------------------------------------------------------------

    def _cache_is_fresh(self) -> bool:
        return (time.monotonic() - self._bm25_built_at) < self.CACHE_TTL_SECONDS

    def _build_bm25_index(self, db: Session):
        """Build the BM25 index from all memory chunks."""
        rows = db.query(MemoryChunk).all()
        chunks = [
            RetrievedChunk(
                file=row.file_path,
                content=row.chunk_content,
                chunk_type=row.chunk_type,
                chunk_name=row.chunk_name,
            )
            for row in rows
        ]
        if not chunks:
            return None, []

        corpus_tokens = [
            _tokenize(" ".join(filter(None, [c.file, c.chunk_name or "", c.content])))
            for c in chunks
        ]
        if not any(corpus_tokens):
            return None, []

        if BM25Okapi is not None:
            index = BM25Okapi(corpus_tokens)
        else:
            index = _TokenOverlapScorer(corpus_tokens)
        return index, chunks

    def _get_or_build_bm25(self, db: Session):
        if self._bm25_cache is not None and self._cache_is_fresh():
            return self._bm25_cache, self._bm25_corpus
        index, corpus = self._build_bm25_index(db)
        self._bm25_cache = index
        self._bm25_corpus = corpus
        self._bm25_built_at = time.monotonic()
        return index, corpus

    def _bm25_search(self, query: str, db: Session) -> list[RetrievedChunk]:
        index, corpus = self._get_or_build_bm25(db)
        if index is None or not corpus:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scores = index.get_scores(query_tokens)
        top_indices = sorted(
            range(len(scores)), key=lambda idx: scores[idx], reverse=True
        )[: self.bm25_top_k]

        results: list[RetrievedChunk] = []
        for rank, idx in enumerate(top_indices):
            score = float(scores[idx])
            if score <= 0:
                doc_tokens = _tokenize(
                    " ".join(filter(None, [corpus[idx].file, corpus[idx].chunk_name or "", corpus[idx].content]))
                )
                overlap = len(set(query_tokens) & set(doc_tokens))
                if overlap == 0:
                    continue
                score = overlap / max(len(set(query_tokens)), 1)
            results.append(
                replace(corpus[idx], score=score, bm25_rank=rank, cosine_rank=None)
            )
        return results

    # -------------------------------------------------------------------
    # Cosine similarity search
    # -------------------------------------------------------------------

    def _cosine_search(self, query: str, db: Session) -> list[RetrievedChunk]:
        query_embedding = embed(query)
        if query_embedding is None:
            return []

        rows = db.query(MemoryChunk).filter(MemoryChunk.embedding.isnot(None)).all()
        if not rows:
            return []

        scored = []
        for row in rows:
            sim = cosine_similarity(query_embedding, row.embedding)
            if sim >= 0.3:  # minimum similarity threshold
                scored.append((sim, row))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for rank, (sim, row) in enumerate(scored[: self.cosine_top_k]):
            results.append(
                RetrievedChunk(
                    file=row.file_path,
                    content=row.chunk_content,
                    chunk_type=row.chunk_type,
                    chunk_name=row.chunk_name,
                    score=sim,
                    bm25_rank=None,
                    cosine_rank=rank,
                )
            )
        return results

    # -------------------------------------------------------------------
    # Reciprocal Rank Fusion
    # -------------------------------------------------------------------

    def _rrf_merge(
        self,
        bm25_results: list[RetrievedChunk],
        cosine_results: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        scores: dict[str, float] = {}
        merged: dict[str, RetrievedChunk] = {}

        for rank, chunk in enumerate(bm25_results):
            key = chunk.dedupe_key
            scores[key] = scores.get(key, 0.0) + 1.0 / (self.rrf_k + rank + 1)
            merged[key] = replace(chunk, bm25_rank=rank)

        for rank, chunk in enumerate(cosine_results):
            key = chunk.dedupe_key
            scores[key] = scores.get(key, 0.0) + 1.0 / (self.rrf_k + rank + 1)
            if key in merged:
                merged[key] = replace(
                    merged[key], cosine_rank=rank, score=float(scores[key])
                )
            else:
                merged[key] = replace(
                    chunk, cosine_rank=rank, score=float(scores[key])
                )

        ordered = sorted(scores, key=lambda k: scores[k], reverse=True)
        return [replace(merged[k], score=float(scores[k])) for k in ordered]

    # -------------------------------------------------------------------
    # Main retrieve method
    # -------------------------------------------------------------------

    def retrieve(
        self, query: str, db: Session, limit: int = 20
    ) -> list[dict]:
        """
        Hybrid retrieval: BM25 + cosine similarity merged via RRF.

        Falls back gracefully:
        - If both work → RRF merge
        - If only BM25 → BM25 results
        - If only cosine → cosine results
        - If neither → keyword fallback
        """
        bm25_results = self._bm25_search(query, db)

        cosine_error = None
        try:
            cosine_results = self._cosine_search(query, db)
        except Exception as exc:
            cosine_error = exc
            cosine_results = []

        if bm25_results and cosine_results:
            merged = self._rrf_merge(bm25_results, cosine_results)
            return [self._to_dict(c) for c in merged[:limit]]

        if bm25_results:
            return [self._to_dict(c) for c in bm25_results[:limit]]

        if cosine_results:
            return [self._to_dict(c) for c in cosine_results[:limit]]

        if cosine_error:
            logger.warning("Cosine retrieval failed: %s", cosine_error)

        # Last resort: keyword LIKE search
        return self._keyword_search(query, db, limit)

    def _keyword_search(self, query: str, db: Session, limit: int) -> list[dict]:
        """Simple LIKE fallback when embeddings are unavailable."""
        words = _tokenize(query)
        if not words:
            return []

        rows = db.query(MemoryChunk).all()
        results = []
        for row in rows:
            lower_content = row.chunk_content.lower()
            overlap = sum(1 for w in words if w in lower_content)
            if overlap > 0:
                results.append((overlap / len(words), row))

        results.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "file": row.file_path,
                "content": row.chunk_content,
                "chunk_type": row.chunk_type,
                "chunk_name": row.chunk_name,
                "score": float(score),
                "match_quality": "keyword",
            }
            for score, row in results[:limit]
        ]

    @staticmethod
    def _to_dict(chunk: RetrievedChunk) -> dict:
        return {
            "file": chunk.file,
            "content": chunk.content,
            "chunk_type": chunk.chunk_type,
            "chunk_name": chunk.chunk_name,
            "score": float(chunk.score),
            "match_quality": chunk.match_quality,
            "bm25_rank": chunk.bm25_rank,
            "cosine_rank": chunk.cosine_rank,
        }
