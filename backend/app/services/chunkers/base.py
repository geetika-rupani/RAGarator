"""Shared helpers for converting raw text slices into ChunkRecord objects."""

from __future__ import annotations

from typing import List, Sequence

from app.models.schemas import ChunkRecord
from app.utils.helper import count_tokens, preview_text, split_sentences


def build_chunk_records(texts: Sequence[str]) -> List[ChunkRecord]:
    """Drop empty slices and attach length statistics."""
    records: List[ChunkRecord] = []
    for text in texts:
        cleaned = text.strip()
        if not cleaned:
            continue
        records.append(
            ChunkRecord(
                index=len(records),
                text=cleaned,
                char_count=len(cleaned),
                token_count=count_tokens(cleaned),
                sentence_count=len(split_sentences(cleaned)),
                preview=preview_text(cleaned, 160),
            )
        )
    return records


def sliding_windows(items: Sequence[str], size: int, overlap: int) -> List[str]:
    """Join sequential items into overlapping windows."""
    if not items:
        return []
    size = max(1, size)
    overlap = max(0, min(overlap, size - 1))
    step = max(1, size - overlap)
    windows: List[str] = []
    for start in range(0, len(items), step):
        window = items[start : start + size]
        if not window:
            break
        joined = " ".join(item.strip() for item in window if item.strip()).strip()
        if joined:
            windows.append(joined)
        if start + size >= len(items):
            break
    return windows
