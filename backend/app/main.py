from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import skus, orders, generate, layouts, bugreport, memory, settings as settings_router
# Import models so they register with Base.metadata
import app.models  # noqa: F401
import app.memory.models  # noqa: F401

def _ensure_cairn_columns(eng):
    """Add Cairn Protocol columns to decisions table if missing (SQLite only)."""
    if not str(eng.url).startswith("sqlite"):
        return
    import sqlite3
    db_path = str(eng.url).replace("sqlite:///", "")
    try:
        with sqlite3.connect(db_path) as conn:
            existing = {row[1] for row in conn.execute("PRAGMA table_info(decisions)")}
            migrations = {
                "query": "ALTER TABLE decisions ADD COLUMN query TEXT",
                "rejected": "ALTER TABLE decisions ADD COLUMN rejected TEXT",
                "outcome": "ALTER TABLE decisions ADD COLUMN outcome VARCHAR(50)",
                "model_used": "ALTER TABLE decisions ADD COLUMN model_used VARCHAR(100)",
                "files_changed": "ALTER TABLE decisions ADD COLUMN files_changed TEXT DEFAULT '[]'",
            }
            for col, sql in migrations.items():
                if col not in existing:
                    conn.execute(sql)
    except Exception:
        pass  # table may not exist yet on first run


app = FastAPI(
    title="NBNE Memorials",
    description="Order processing and SVG generation for personalised memorial products",
    version="0.1.0",
)

# Create tables on startup (safe for SQLite — no-op if tables exist)
Base.metadata.create_all(bind=engine)

# Cairn Protocol columns — ALTER TABLE for existing SQLite DBs
_ensure_cairn_columns(engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(skus.router)
app.include_router(orders.router)
app.include_router(generate.router)
app.include_router(layouts.router)
app.include_router(bugreport.router)
app.include_router(memory.router)
app.include_router(settings_router.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "memorials"}
