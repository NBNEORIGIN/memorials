from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import skus, orders, generate, layouts, bugreport, memory
# Import models so they register with Base.metadata
import app.models  # noqa: F401
import app.memory.models  # noqa: F401

app = FastAPI(
    title="NBNE Memorials",
    description="Order processing and SVG generation for personalised memorial products",
    version="0.1.0",
)

# Create tables on startup (safe for SQLite — no-op if tables exist)
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "memorials"}
