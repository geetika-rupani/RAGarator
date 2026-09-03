"""Evaluate every chunking strategy against the same query set."""

from __future__ import annotations

from typing import Dict, List, Tuple

from app.models.schemas import (
    ChunkingResult,
    QuerySpec,
    RetrievalReport,
    StrategyMetrics,
)
from app.services.evaluation.quality import build_strategy_metrics
from app.services.retrieval.evaluator import evaluate_retrieval


def evaluate_all_strategies(
    chunkings: Dict[str, ChunkingResult],
    queries: List[QuerySpec],
    document_chars: int,
) -> Tuple[Dict[str, RetrievalReport], Dict[str, StrategyMetrics]]:
    """Run retrieval evaluation and assemble per-strategy metrics."""
    reports: Dict[str, RetrievalReport] = {}
    metrics: Dict[str, StrategyMetrics] = {}
    for strategy, chunking in chunkings.items():
        report = evaluate_retrieval(chunking, queries)
        reports[strategy] = report
        metrics[strategy] = build_strategy_metrics(chunking, report, document_chars)
    return reports, metrics
