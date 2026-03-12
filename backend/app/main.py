from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import skus, orders, generate

app = FastAPI(
    title="NBNE Memorials",
    description="Order processing and SVG generation for personalised memorial products",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(skus.router)
app.include_router(orders.router)
app.include_router(generate.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "memorials"}
