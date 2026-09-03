"""Fixed-size character window chunking with overlap."""

from __future__ import annotations

from typing import List

from app.config import settings
from app.models.schemas import ChunkRecord
from app.services.chunkers.base import build_chunk_records


def chunk_fixed(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> List[ChunkRecord]:
    """Slice the document into overlapping character windows.

    Windows prefer whitespace boundaries so words are not split unless a
    long token exceeds the configured window.
    """
    size = chunk_size or settings.fixed_chunk_size
    overlap = settings.fixed_overlap if overlap is None else overlap
    size = max(80, size)
    overlap = max(0, min(overlap, size // 2))
    if not text.strip():
        return []
    if len(text) <= size:
        return build_chunk_records([text])

    step = max(1, size - overlap)
    slices: List[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(length, start + size)
        if end < length:
            boundary = text.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        piece = text[start:end].strip()
        if piece:
            slices.append(piece)
        if end >= length:
            break
        start = max(end - overlap, start + step)
        if start >= length:
            break
    return build_chunk_records(slices)
