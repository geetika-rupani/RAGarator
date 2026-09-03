"""Processing and retrieval efficiency relative to the document size."""

from __future__ import annotations

from app.models.schemas import ChunkingResult, RetrievalReport
from app.utils.helper import clamp


def processing_efficiency(
    chunking: ChunkingResult,
    retrieval: RetrievalReport,
    document_chars: int,
) -> float:
    """Reward low latency and a practical number of chunks for the document."""
    if chunking.chunk_count == 0:
        return 0.0
    expected_chunks = max(1.0, document_chars / 450.0)
    ratio = chunking.chunk_count / expected_chunks
    if 0.5 <= ratio <= 2.2:
        count_score = 1.0 - abs(1.0 - ratio) / 3.0
    elif ratio < 0.5:
        count_score = clamp(ratio / 0.5)
    else:
        count_score = clamp(2.2 / ratio)

    total_ms = max(chunking.processing_ms + retrieval.retrieval_ms, 0.01)
    budget_ms = 40.0 + document_chars / 800.0
    time_score = clamp(budget_ms / max(total_ms, budget_ms * 0.25))
    tiny_chunk_penalty = 0.0
    if chunking.avg_char_count < 60 and chunking.chunk_count > 20:
        tiny_chunk_penalty = 0.25
    return round(clamp(0.55 * count_score + 0.45 * time_score - tiny_chunk_penalty), 4)
