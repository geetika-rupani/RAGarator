"""Compose the final recommendation payload from scored strategies."""

from __future__ import annotations

from typing import Dict, List

from app.models.schemas import (
    DocumentProfile,
    QuerySpec,
    RankingEntry,
    RecommendationResult,
    RetrievalReport,
    StrategyScore,
)
from app.services.decision.confidence import assess_confidence
from app.services.decision.explanation import build_evidence, build_reasons, build_tradeoffs
from app.services.decision.scoring import ranked_strategies


def recommend(
    scores: Dict[str, StrategyScore],
    reports: Dict[str, RetrievalReport],
    document: DocumentProfile,
    queries: List[QuerySpec],
) -> RecommendationResult:
    """Select a winner and attach ranking, reasons, uncertainty, and evidence."""
    ranking_scores = ranked_strategies(scores)
    if not ranking_scores:
        raise ValueError("Cannot recommend a strategy without scores.")
    winner = ranking_scores[0]
    confidence = assess_confidence(scores, document, len(queries))
    ranking = [
        RankingEntry(
            rank=index,
            strategy=item.strategy,
            label=item.label,
            score=item.total,
            score_gap_to_leader=round(winner.total - item.total, 4),
            avg_top1=item.metrics.avg_top1,
            avg_chunk_chars=item.metrics.avg_chunk_chars,
            chunk_count=item.metrics.chunk_count,
            consistency=item.metrics.consistency,
            efficiency=item.metrics.efficiency,
        )
        for index, item in enumerate(ranking_scores, start=1)
    ]
    caveats = list(document.warnings)
    for metric in (item.metrics for item in ranking_scores):
        for warning in metric.warnings:
            labeled = f"{metric.label}: {warning}"
            if labeled not in caveats:
                caveats.append(labeled)
    if document.char_count < 1200:
        caveats.append(
            "Because this document is short, consider re-running the benchmark after "
            "adding more representative pages."
        )
    return RecommendationResult(
        recommended_strategy=winner.strategy,
        recommended_label=winner.label,
        confidence=confidence,
        ranking=ranking,
        scores=scores,
        reasons=build_reasons(scores, document, queries),
        uncertainty=confidence.factors,
        trade_offs=build_tradeoffs(scores),
        evidence=build_evidence(winner.strategy, scores, reports),
        caveats=caveats,
    )
