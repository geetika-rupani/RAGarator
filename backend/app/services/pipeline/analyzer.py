"""Orchestrate ingestion, chunking, evaluation, and recommendation."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from app.config import settings
from app.models.schemas import AnalysisResponse, QuerySpec, RetrievalReport
from app.services.benchmark.evaluator import evaluate_all_strategies
from app.services.benchmark.queries import generate_queries
from app.services.chunkers.manager import run_all_chunkers
from app.services.decision.recommendation import recommend
from app.services.decision.scoring import score_strategies
from app.services.ingestion.cleaner import clean_text
from app.services.ingestion.loaders import load_document
from app.services.ingestion.metadata import profile_document
from app.utils.errors import (
    DocumentTooLargeError,
    DocumentTooSmallError,
    EmptyDocumentError,
    FileNotFoundError_,
    UnsupportedFileError,
)

ProgressFn = Callable[[str, str], None]


def analyze_file(
    file_id: str,
    upload_dir: Path | None = None,
    progress: Optional[ProgressFn] = None,
) -> AnalysisResponse | Tuple[AnalysisResponse, Dict[str, RetrievalReport]]:
    """Run the full RAGarator workflow for a previously uploaded file.

    When ``progress`` is provided, the function also returns retrieval reports
    so the dashboard presenter can cite real retrieved spans.
    """
    directory = upload_dir or settings.upload_dir
    _emit(progress, "upload", "file located")
    path = _resolve_upload(file_id, directory)
    _emit(progress, "extract", path.name)
    raw = load_document(path)
    _emit(progress, "clean", f"{len(raw)} raw characters")
    cleaned = clean_text(raw)
    _validate_text(cleaned, path.name)
    document = profile_document(file_id, path.name, path.suffix.lower(), cleaned)
    queries = generate_queries(cleaned, document)
    if not queries:
        raise DocumentTooSmallError(
            "Could not derive benchmark queries from this document. "
            "Upload a text-rich PDF, DOCX, or TXT file."
        )
    _emit(progress, "chunk", "fixed, recursive, sentence, token")
    chunkings = run_all_chunkers(cleaned)
    _emit(progress, "embed", "fitting TF-IDF on each strategy")
    _emit(progress, "retrieve", f"{len(queries)} grounded queries")
    reports, metrics = evaluate_all_strategies(chunkings, queries, document.char_count)
    _emit(progress, "evaluate", "size, consistency, efficiency")
    scores = score_strategies(metrics)
    _emit(progress, "decide", "ranking strategies")
    recommendation = recommend(scores, reports, document, queries)
    notes = _notes(document, queries, metrics)
    analysis = AnalysisResponse(
        file_id=file_id,
        document=document,
        queries=queries,
        strategies=metrics,
        recommendation=recommendation,
        notes=notes,
    )
    if progress is not None:
        return analysis, reports
    return analysis


def _emit(progress: Optional[ProgressFn], stage: str, message: str) -> None:
    if progress:
        progress(stage, message)


def _resolve_upload(file_id: str, directory: Path) -> Path:
    if not file_id or any(sep in file_id for sep in ("/", "\\", "..")):
        raise FileNotFoundError_("Invalid file id.")
    matches = list(directory.glob(f"{file_id}.*"))
    if not matches:
        raise FileNotFoundError_(
            f"No uploaded file found for id '{file_id}'. Upload a document first."
        )
    path = matches[0]
    if path.suffix.lower() not in settings.allowed_extensions:
        raise UnsupportedFileError(
            f"Unsupported file type '{path.suffix}'. Upload a PDF, DOCX, or TXT file."
        )
    return path


def _validate_text(text: str, filename: str) -> None:
    if not text.strip():
        raise EmptyDocumentError(
            f"{filename} produced no extractable text. Scanned PDFs without a text "
            "layer are not supported."
        )
    if len(text.strip()) < settings.min_document_chars:
        raise DocumentTooSmallError(
            f"{filename} has only {len(text.strip())} characters after cleaning. "
            f"Provide at least {settings.min_document_chars} characters so chunking "
            "and retrieval can be compared."
        )
    if len(text) > settings.max_document_chars:
        raise DocumentTooLargeError(
            f"{filename} is {len(text)} characters, above the "
            f"{settings.max_document_chars} character analysis limit."
        )


def _notes(document, queries: List[QuerySpec], metrics) -> List[str]:
    notes = list(document.warnings)
    notes.append(
        f"Generated {len(queries)} grounded queries from the document text; "
        "gold excerpts are source sentences, not synthetic labels."
    )
    empty = [item.label for item in metrics.values() if item.chunk_count == 0]
    if empty:
        notes.append("These strategies produced no chunks: " + ", ".join(empty) + ".")
    return notes
