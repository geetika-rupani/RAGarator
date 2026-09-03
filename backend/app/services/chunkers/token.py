"""Token-window chunking using word-like tokens rather than model tokens."""

from __future__ import annotations

from typing import List

from app.config import settings
from app.models.schemas import ChunkRecord
from app.services.chunkers.base import build_chunk_records
from app.utils.helper import TOKEN_RE


def chunk_token(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> List[ChunkRecord]:
    """Slide a token window across the document and reconstruct original spans."""
    size = chunk_size or settings.token_chunk_size
    overlap = settings.token_overlap if overlap is None else overlap
    size = max(16, size)
    overlap = max(0, min(overlap, size - 1))
    matches = list(TOKEN_RE.finditer(text))
    if not matches:
        return build_chunk_records([text] if text.strip() else [])
    if len(matches) <= size:
        return build_chunk_records([text])

    step = max(1, size - overlap)
    slices: List[str] = []
    for start in range(0, len(matches), step):
        window = matches[start : start + size]
        if not window:
            break
        span_start = window[0].start()
        span_end = window[-1].end()
        piece = text[span_start:span_end].strip()
        if piece:
            slices.append(piece)
        if start + size >= len(matches):
            break
    return build_chunk_records(slices)
