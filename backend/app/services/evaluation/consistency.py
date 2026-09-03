"""Chunk consistency: length stability, overlap sanity, and empty-chunk penalties."""

from __future__ import annotations

from app.models.schemas import ChunkingResult
from app.services.evaluation.chunk_quality import length_stability, semantic_coherence
from app.utils.helper import clamp


def chunk_consistency(
    chunking: ChunkingResult,
    coherence: float | None = None,
) -> float:
    """Combine length regularity, local coherence, and structural hygiene."""
    if chunking.chunk_count == 0:
        return 0.0
    stability = length_stability(chunking)
    coherence = semantic_coherence(chunking) if coherence is None else coherence
    overlap = chunking.overlap_ratio
    if overlap <= 0.25:
        overlap_score = 1.0
    elif overlap <= 0.45:
        overlap_score = clamp(1.0 - (overlap - 0.25) / 0.40)
    else:
        overlap_score = clamp(0.45 - (overlap - 0.45))
    empty_penalty = 0.0
    if chunking.empty_chunk_count:
        empty_penalty = min(0.4, chunking.empty_chunk_count / max(chunking.chunk_count, 1))
    singleton_penalty = 0.12 if chunking.chunk_count == 1 and chunking.avg_char_count > 900 else 0.0
    score = 0.45 * stability + 0.35 * coherence + 0.20 * overlap_score
    return round(clamp(score - empty_penalty - singleton_penalty), 4)
