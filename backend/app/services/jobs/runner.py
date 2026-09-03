"""Run analysis jobs in a background thread with stage updates."""

from __future__ import annotations

import threading
import uuid
from pathlib import Path

from app.config import settings
from app.services.decision.dashboard import build_dashboard
from app.services.jobs.store import STAGE_LABELS, Job, store
from app.services.pipeline.analyzer import analyze_file
from app.utils.errors import RagaratorError


def start_job(job: Job) -> None:
    """Persist the job and run the pipeline off the request thread."""
    store.create(job)
    thread = threading.Thread(target=_run, args=(job.job_id,), daemon=True)
    thread.start()


def _run(job_id: str) -> None:
    job = store.get(job_id)
    if not job:
        return
    store.update(job_id, status="processing", stage="upload")
    store.append_log(job_id, f"{STAGE_LABELS['upload']} — {job.filename}")

    def on_stage(stage: str, message: str) -> None:
        label = STAGE_LABELS.get(stage, stage)
        store.append_log(job_id, f"{label} — {message}", stage=stage)

    try:
        analysis, reports = analyze_file(
            job.file_id,
            progress=on_stage,
        )
        dashboard = build_dashboard(analysis, reports, job.filename, job.size_bytes)
        store.append_log(job_id, "Decision Engine — complete", stage="decide")
        store.update(
            job_id,
            status="complete",
            stage=None,
            result=dashboard,
            error=None,
        )
    except RagaratorError as exc:
        store.update(job_id, status="error", error=exc.message, stage=None)
        store.append_log(job_id, f"Error — {exc.message}")
    except Exception as exc:
        store.update(job_id, status="error", error=str(exc), stage=None)
        store.append_log(job_id, f"Error — {exc}")


def persist_upload(filename: str, payload: bytes) -> str:
    """Write uploaded bytes and return the file_id used by the pipeline."""
    suffix = Path(filename).suffix.lower() or ".txt"
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex
    destination = settings.upload_dir / f"{file_id}{suffix}"
    destination.write_bytes(payload)
    return file_id
