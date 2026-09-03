"""Assemble per-strategy metrics from chunking and retrieval reports."""

from __future__ import annotations

from typing import List

from app.models.schemas import ChunkingResult, RetrievalReport, StrategyMetrics
from app.services.evaluation.chunk_quality import semantic_coherence, size_suitability
from app.services.evaluation.consistency import chunk_consistency
from app.services.evaluation.efficiency import processing_efficiency


def build_strategy_metrics(
    chunking: ChunkingResult,
    retrieval: RetrievalReport,
    document_chars: int,
) -> StrategyMetrics:
    """Merge intrinsic and retrieval metrics into one comparable record."""
    warnings: List[str] = []
    if chunking.chunk_count == 0:
        warnings.append("No chunks were produced.")
    elif chunking.chunk_count == 1:
        warnings.append(
            f"Only 1 chunk was produced ({chunking.avg_char_count:.0f} characters), "
            "so retrieval ranking has little room to differentiate passages."
        )
    if chunking.avg_char_count < 80:
        warnings.append(
            f"Average chunk size is {chunking.avg_char_count:.0f} characters, which is "
            "likely too small to contain a complete answer span."
        )
    if chunking.avg_char_count > 1400:
        warnings.append(
            f"Average chunk size is {chunking.avg_char_count:.0f} characters, which "
            "dilutes retrieval by packing unrelated sentences together."
        )
    coherence = semantic_coherence(chunking)
    return StrategyMetrics(
        strategy=chunking.strategy,
        label=chunking.label,
        chunk_count=chunking.chunk_count,
        avg_chunk_chars=chunking.avg_char_count,
        median_chunk_chars=chunking.median_char_count,
        min_chunk_chars=chunking.min_char_count,
        max_chunk_chars=chunking.max_char_count,
        chunk_size_cv=round(
            (chunking.std_char_count / chunking.avg_char_count)
            if chunking.avg_char_count
            else 0.0,
            4,
        ),
        overlap_ratio=chunking.overlap_ratio,
        semantic_coherence=coherence,
        size_suitability=size_suitability(chunking, document_chars),
        consistency=chunk_consistency(chunking, coherence=coherence),
        efficiency=processing_efficiency(chunking, retrieval, document_chars),
        processing_ms=chunking.processing_ms,
        retrieval_ms=retrieval.retrieval_ms,
        avg_top1=retrieval.avg_top1,
        avg_top3=retrieval.avg_top3,
        avg_best=retrieval.avg_best,
        gold_hit_rate=retrieval.gold_hit_rate,
        mean_reciprocal_rank=retrieval.mean_reciprocal_rank,
        empty_chunk_count=chunking.empty_chunk_count,
        warnings=warnings,
    )
