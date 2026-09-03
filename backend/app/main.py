"""FastAPI entrypoint for RAGarator."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyze import router as analyze_router
from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered RAG chunking benchmark: upload a document, compare four "
        "chunking strategies, and receive an explainable recommendation."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(upload_router, prefix="/api", tags=["upload"])
app.include_router(analyze_router, prefix="/api", tags=["analyze"])


@app.get("/")
def root() -> dict:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/health",
    }
