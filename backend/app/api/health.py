"""Liveness endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """Return service identity and a simple ready flag."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }
