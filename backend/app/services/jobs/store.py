"""Thread-safe in-memory job store."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


STAGE_ORDER = (
    "upload",
    "extract",
    "clean",
    "chunk",
    "embed",
    "retrieve",
    "evaluate",
    "decide",
)

STAGE_LABELS = {
    "upload": "Ingesting document",
    "extract": "Extracting text",
    "clean": "Cleaning text",
    "chunk": "Running chunking strategies",
    "embed": "Generating embeddings",
    "retrieve": "Benchmarking retrieval",
    "evaluate": "Scoring quality & consistency",
    "decide": "Running Decision Engine",
}


@dataclass
class Job:
    job_id: str
    filename: str
    size_bytes: int
    file_id: str
    status: str = "queued"
    stage: Optional[str] = "upload"
    logs: List[str] = field(default_factory=list)
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)


class JobStore:
    """Process-local job map used by the dashboard polling endpoints."""

    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **changes: Any) -> Optional[Job]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            for key, value in changes.items():
                setattr(job, key, value)
            return job

    def append_log(self, job_id: str, line: str, stage: str | None = None) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.logs.append(line)
            if stage is not None:
                job.stage = stage
            if job.status == "queued":
                job.status = "processing"


store = JobStore()
