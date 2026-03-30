"""Code indexer — chunks source files and generates embeddings for semantic search."""

import ast
import hashlib
import logging
import re
from pathlib import Path
from typing import Generator

from sqlalchemy.orm import Session

from app.memory.models import MemoryChunk
from app.memory.embeddings import embed, MAX_CHUNK_CHARS

logger = logging.getLogger(__name__)

INCLUDE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".md", ".json", ".yaml", ".yml",
    ".html", ".css", ".sql",
}

EXCLUDE_PATTERNS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "uploads", "output",
    ".pytest_cache", "coverage", ".mypy_cache",
}


# ---------------------------------------------------------------------------
# Chunking strategies
# ---------------------------------------------------------------------------

def _chunk_python(content: str) -> Generator[dict, None, None]:
    """Chunk Python files using AST (functions, classes)."""
    try:
        tree = ast.parse(content)
        lines = content.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start = node.lineno - 1
                end = node.end_lineno
                if end - start < 5:
                    continue
                chunk_content = "\n".join(lines[start:end])
                node_type = type(node).__name__.lower()
                if "async" in node_type:
                    node_type = "async_function"
                elif "functiondef" in node_type:
                    node_type = "function"
                if len(chunk_content) > MAX_CHUNK_CHARS:
                    yield from _chunk_window(chunk_content)
                else:
                    yield {"content": chunk_content, "type": node_type, "name": node.name}
    except SyntaxError:
        yield from _chunk_window(content)


def _chunk_typescript(content: str) -> Generator[dict, None, None]:
    """Chunk TypeScript/JavaScript files by function definitions."""
    pattern = re.compile(
        r"(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)[^{]*\{",
        re.MULTILINE,
    )
    lines = content.splitlines()
    matches = list(pattern.finditer(content))

    if not matches:
        yield from _chunk_window(content)
        return

    for i, match in enumerate(matches):
        start_line = content[: match.start()].count("\n")
        end_line = (
            content[: matches[i + 1].start()].count("\n")
            if i + 1 < len(matches)
            else len(lines)
        )
        chunk_lines = lines[start_line:end_line]
        if len(chunk_lines) >= 5:
            chunk_content = "\n".join(chunk_lines)
            if len(chunk_content) > MAX_CHUNK_CHARS:
                yield from _chunk_window(chunk_content)
            else:
                yield {"content": chunk_content, "type": "function", "name": match.group(1)}


def _chunk_markdown(content: str) -> Generator[dict, None, None]:
    """Chunk Markdown files by H2 sections."""
    sections = re.split(r"\n(?=## )", content)
    for section in sections:
        section = section.strip()
        if not section:
            continue
        name_match = re.match(r"## (.+)", section)
        name = name_match.group(1) if name_match else None
        if len(section) > MAX_CHUNK_CHARS:
            yield from _chunk_window(section)
        else:
            yield {"content": section, "type": "section", "name": name}


def _chunk_window(
    content: str, window: int = 40, overlap: int = 8
) -> Generator[dict, None, None]:
    """Fallback: sliding window chunking (40 lines, 8-line overlap)."""
    lines = content.splitlines()
    if not lines:
        return
    step = window - overlap
    for start in range(0, len(lines), step):
        chunk_lines = lines[start : start + window]
        if len(chunk_lines) < 5:
            break
        chunk = "\n".join(chunk_lines)
        if len(chunk) > MAX_CHUNK_CHARS:
            chunk = chunk[:MAX_CHUNK_CHARS]
        yield {"content": chunk, "type": "window", "name": None}


def _chunk_file(file_path: Path, content: str) -> Generator[dict, None, None]:
    """Dispatch to the right chunking strategy based on file extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".py":
        yield from _chunk_python(content)
    elif suffix in {".ts", ".tsx", ".js", ".jsx"}:
        yield from _chunk_typescript(content)
    elif suffix == ".md":
        yield from _chunk_markdown(content)
    else:
        yield from _chunk_window(content)


# ---------------------------------------------------------------------------
# Filesystem walker
# ---------------------------------------------------------------------------

def _walk_codebase(root: Path) -> Generator[Path, None, None]:
    """Walk the codebase, respecting EXCLUDE_PATTERNS and INCLUDE_EXTENSIONS."""
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        parts = set(path.relative_to(root).parts)
        if parts & EXCLUDE_PATTERNS:
            continue
        if path.suffix.lower() not in INCLUDE_EXTENSIONS:
            continue
        yield path


# ---------------------------------------------------------------------------
# Index orchestrator
# ---------------------------------------------------------------------------

def index_codebase(
    db: Session,
    codebase_path: str,
    force_reindex: bool = False,
) -> dict:
    """
    Index all source files in the codebase.

    Chunks each file, generates embeddings, and stores in memory_chunks.
    Returns a summary dict with counts.
    """
    root = Path(codebase_path)
    if not root.exists():
        return {"error": f"Codebase path does not exist: {codebase_path}"}

    all_files = list(_walk_codebase(root))
    total = len(all_files)
    indexed = 0
    skipped = 0
    errors = 0
    chunks_created = 0

    logger.info("[indexer] Found %d files to process in %s", total, root)

    for i, file_path in enumerate(all_files):
        try:
            rel_path = str(file_path.relative_to(root)).replace("\\", "/")
            content = file_path.read_text(encoding="utf-8", errors="replace")
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            # Skip if already indexed with same hash
            if not force_reindex:
                existing = (
                    db.query(MemoryChunk)
                    .filter_by(file_path=rel_path, content_hash=content_hash)
                    .first()
                )
                if existing:
                    skipped += 1
                    continue

            # Delete old chunks for this file
            db.query(MemoryChunk).filter_by(file_path=rel_path).delete()

            chunks = list(_chunk_file(file_path, content))
            file_ok = True

            for chunk in chunks:
                embedding = embed(chunk["content"])
                if embedding is None:
                    logger.warning("  WARN: no embedding for %s", rel_path)
                    file_ok = False
                    break

                db.add(MemoryChunk(
                    file_path=rel_path,
                    chunk_content=chunk["content"],
                    chunk_type=chunk["type"],
                    chunk_name=chunk.get("name"),
                    content_hash=content_hash,
                    embedding=embedding,
                    last_modified=file_path.stat().st_mtime,
                ))

            if not file_ok:
                db.rollback()
                errors += 1
                continue

            db.commit()
            indexed += 1
            chunks_created += len(chunks)

            if indexed % 10 == 0:
                logger.info(
                    "[indexer] Progress: %d/%d files (%d indexed, %d skipped)",
                    i + 1, total, indexed, skipped,
                )

        except Exception as exc:
            errors += 1
            logger.error("  ERR %s: %s", file_path, exc)
            db.rollback()

    summary = {
        "indexed": indexed,
        "skipped": skipped,
        "errors": errors,
        "chunks_created": chunks_created,
        "total_files": total,
    }
    logger.info("[indexer] Complete: %s", summary)
    return summary
