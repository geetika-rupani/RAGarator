"""Sentence-based chunking that packs complete sentences into windows."""

from __future__ import annotations

from typing import List

from app.config import settings
from app.models.schemas import ChunkRecord
from app.services.chunkers.base import build_chunk_records
from app.utils.helper import split_sentences


def chunk_sentence(
    text: str,
    target_chars: int | None = None,
) -> List[ChunkRecord]:
    """Group consecutive sentences until the target character budget is reached."""
    target = target_chars or settings.sentence_target_chars
    target = max(120, target)
    sentences = split_sentences(text)
    if not sentences:
        return build_chunk_records([text] if text.strip() else [])

    groups: List[str] = []
    buffer: List[str] = []
    buffer_len = 0
    for sentence in sentences:
        extra = len(sentence) + (1 if buffer else 0)
        if buffer and buffer_len + extra > target:
            groups.append(" ".join(buffer))
            buffer = [sentence]
            buffer_len = len(sentence)
        else:
            buffer.append(sentence)
            buffer_len += extra
    if buffer:
        groups.append(" ".join(buffer))
    return build_chunk_records(groups)
