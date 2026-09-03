"""Document upload endpoint."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.models.schemas import UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """Persist a PDF, DOCX, or TXT file and return a file_id for /analyze."""
    filename = file.filename or "document.txt"
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "UNSUPPORTED_FILE",
                "message": (
                    f"Unsupported file type '{suffix or 'unknown'}'. "
                    "Upload a PDF, DOCX, or TXT file."
                ),
            },
        )

    payload = await file.read()
    size = len(payload)
    if size == 0:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "EMPTY_DOCUMENT",
                "message": f"{filename} is empty.",
            },
        )
    if size > settings.max_file_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": (
                    f"{filename} is {size} bytes; the limit is "
                    f"{settings.max_file_size_mb} MB."
                ),
            },
        )

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex
    destination = settings.upload_dir / f"{file_id}{suffix}"
    destination.write_bytes(payload)
    return UploadResponse(
        file_id=file_id,
        filename=filename,
        extension=suffix,
        size_bytes=size,
        message="Upload complete. Call /api/analyze with this file_id.",
    )
