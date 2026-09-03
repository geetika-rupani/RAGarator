"""Analysis endpoints: sync JSON pipeline and async dashboard jobs."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.services.jobs.runner import persist_upload, start_job
from app.services.jobs.store import Job, store
from app.services.pipeline.analyzer import analyze_file
from app.utils.errors import RagaratorError

router = APIRouter()


class AnalyzeRequest(BaseModel):
    file_id: str = Field(..., min_length=8, max_length=80)


class JobStatus(BaseModel):
    status: str
    stage: Optional[str] = None
    logs: list[str] = Field(default_factory=list)
    error: Optional[str] = None


def _http_error(exc: RagaratorError) -> HTTPException:
    status = 404 if exc.code == "FILE_NOT_FOUND" else 400
    return HTTPException(
        status_code=status,
        detail={"code": exc.code, "message": exc.message, "error": exc.message},
    )


@router.post("/analyze")
async def analyze(
    request: Request,
    file: Optional[UploadFile] = File(default=None),
):
    """JSON {file_id} runs synchronously. Multipart file starts a dashboard job."""
    if file is not None and file.filename:
        return await _start_job_from_upload(file)

    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded = form.get("file")
        if uploaded is not None and hasattr(uploaded, "read"):
            if not isinstance(uploaded, UploadFile):
                uploaded = UploadFile(
                    file=uploaded.file,
                    filename=getattr(uploaded, "filename", "document.txt"),
                )
            return await _start_job_from_upload(uploaded)
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MISSING_INPUT",
                "message": "Upload a file in the 'file' field.",
                "error": "Upload a file in the 'file' field.",
            },
        )

    try:
        body = await request.json()
        payload = AnalyzeRequest.model_validate(body)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MISSING_INPUT",
                "message": "Provide file_id JSON or upload a file.",
                "error": "Provide file_id JSON or upload a file.",
            },
        ) from exc
    try:
        return analyze_file(payload.file_id)
    except RagaratorError as exc:
        raise _http_error(exc) from exc


@router.get("/analyze/{job_id}/status", response_model=JobStatus)
def job_status(job_id: str) -> JobStatus:
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"error": "Unknown job id"})
    return JobStatus(
        status=job.status,
        stage=job.stage,
        logs=list(job.logs),
        error=job.error,
    )


@router.get("/analyze/{job_id}/result")
def job_result(job_id: str) -> dict:
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"error": "Unknown job id"})
    if job.status != "complete" or job.result is None:
        raise HTTPException(
            status_code=409,
            detail={"error": job.error or "Result is not ready yet."},
        )
    return job.result


async def _start_job_from_upload(file: UploadFile) -> JSONResponse:
    filename = file.filename or "document.txt"
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        message = (
            f"Unsupported file type '{suffix or 'unknown'}'. "
            "Upload a PDF, DOCX, or TXT file."
        )
        raise HTTPException(
            status_code=400,
            detail={"error": message, "code": "UNSUPPORTED_FILE", "message": message},
        )
    payload = await file.read()
    if not payload:
        message = f"{filename} is empty."
        raise HTTPException(
            status_code=400,
            detail={"error": message, "code": "EMPTY_DOCUMENT", "message": message},
        )
    if len(payload) > settings.max_file_bytes:
        message = f"{filename} exceeds the {settings.max_file_size_mb} MB limit."
        raise HTTPException(
            status_code=413,
            detail={"error": message, "code": "FILE_TOO_LARGE", "message": message},
        )
    file_id = persist_upload(filename, payload)
    job_id = uuid.uuid4().hex
    start_job(
        Job(
            job_id=job_id,
            filename=filename,
            size_bytes=len(payload),
            file_id=file_id,
        )
    )
    return JSONResponse(status_code=202, content={"jobId": job_id})
