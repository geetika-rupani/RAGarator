"""Intrinsic chunk quality: size suitability and semantic coherence."""

from __future__ import annotations

from app.config import settings
from app.models.schemas import ChunkingResult
from app.services.embeddings.embedder import pairwise_coherence
from app.utils.helper import clamp, coefficient_of_variation


def size_suitability(chunking: ChunkingResult, document_chars: int) -> float:
    """Score how well average chunk length matches a RAG-friendly band.

    Very short documents get a relaxed target so they are not punished for
    producing fewer, shorter chunks.
    """
    if chunking.chunk_count == 0:
        return 0.0
    low, high = settings.optimal_chunk_chars
    if document_chars < settings.small_document_chars:
        low = max(settings.chunk_chars_hard_min, document_chars // 6)
        high = max(low + 40, min(document_chars, 400))
    avg = chunking.avg_char_count
    if low <= avg <= high:
        center = (low + high) / 2
        span = max((high - low) / 2, 1.0)
        return round(clamp(1.0 - abs(avg - center) / (span * 2.5)), 4)

    if avg < settings.chunk_chars_hard_min:
        return 0.05
    if avg > settings.chunk_chars_hard_max:
        return 0.08
    if avg < low:
        return round(clamp(avg / low), 4)
    overshoot = (avg - high) / max(settings.chunk_chars_hard_max - high, 1.0)
    return round(clamp(1.0 - overshoot), 4)


def semantic_coherence(chunking: ChunkingResult) -> float:
    """Adjacent-chunk cosine similarity as a proxy for local continuity."""
    if chunking.chunk_count == 0:
        return 0.0
    if chunking.chunk_count == 1:
        return 1.0
    texts = [chunk.text for chunk in chunking.chunks]
    return round(clamp(pairwise_coherence(texts)), 4)


def length_stability(chunking: ChunkingResult) -> float:
    """Lower coefficient of variation of chunk lengths is more stable."""
    if chunking.chunk_count <= 1:
        return 1.0
    lengths = [float(chunk.char_count) for chunk in chunking.chunks]
    cv = coefficient_of_variation(lengths)
    return round(clamp(1.0 / (1.0 + cv)), 4)
