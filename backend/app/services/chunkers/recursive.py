"""Recursive character splitting that respects document structure."""

from __future__ import annotations

from typing import List

from app.config import settings
from app.models.schemas import ChunkRecord
from app.services.chunkers.base import build_chunk_records

SEPARATORS = ("\n\n", "\n", ". ", " ", "")


def chunk_recursive(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> List[ChunkRecord]:
    """Split on the coarsest separator that keeps pieces near chunk_size."""
    size = chunk_size or settings.recursive_chunk_size
    overlap = settings.recursive_overlap if overlap is None else overlap
    size = max(80, size)
    overlap = max(0, min(overlap, size // 2))
    if not text.strip():
        return []
    pieces = _split_recursive(text.strip(), size, SEPARATORS)
    merged = _merge_with_overlap(pieces, size, overlap)
    return build_chunk_records(merged)


def _split_recursive(text: str, chunk_size: int, separators: tuple[str, ...]) -> List[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    if not separators:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    separator, *rest = separators
    if separator == "":
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    parts = [part for part in text.split(separator) if part.strip()]
    if len(parts) <= 1:
        return _split_recursive(text, chunk_size, tuple(rest))

    chunks: List[str] = []
    buffer = ""
    join_token = separator
    for part in parts:
        candidate = f"{buffer}{join_token}{part}" if buffer else part
        if len(candidate) <= chunk_size:
            buffer = candidate
            continue
        if buffer:
            chunks.extend(_split_recursive(buffer, chunk_size, tuple(rest)))
            buffer = ""
        if len(part) > chunk_size:
            chunks.extend(_split_recursive(part, chunk_size, tuple(rest)))
        else:
            buffer = part
    if buffer:
        chunks.extend(_split_recursive(buffer, chunk_size, tuple(rest)))
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def _merge_with_overlap(pieces: List[str], chunk_size: int, overlap: int) -> List[str]:
    if not pieces:
        return []
    merged: List[str] = []
    current = pieces[0]
    for piece in pieces[1:]:
        candidate = f"{current}\n\n{piece}"
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        merged.append(current)
        if overlap > 0 and len(current) > overlap:
            tail = current[-overlap:].lstrip()
            current = f"{tail}\n\n{piece}" if tail else piece
            if len(current) > chunk_size * 2:
                current = piece
        else:
            current = piece
    merged.append(current)
    return merged
