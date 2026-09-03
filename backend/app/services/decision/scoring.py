"""Normalize per-factor metrics and compute weighted strategy scores.

Normalization is min-max across the four strategies for each factor so a
metric measured in milliseconds cannot dominate a metric measured in
cosine similarity. When all strategies tie on a factor, every strategy
receives the raw value (already 0-1) instead of an arbitrary 0.5.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from app.config import settings
from app.models.schemas import FactorScore, StrategyMetrics, StrategyScore
from app.utils.helper import clamp

FACTOR_EXTRACTORS: Dict[str, str] = {
    "top1_similarity": "avg_top1",
    "top3_similarity": "avg_top3",
    "best_retrieval": "avg_best",
    "chunk_size_suitability": "size_suitability",
    "chunk_consistency": "consistency",
    "efficiency": "efficiency",
}

FACTOR_LABELS: Dict[str, str] = {
    "top1_similarity": "Top-1 retrieval similarity",
    "top3_similarity": "Top-3 retrieval similarity",
    "best_retrieval": "Best retrieval score",
    "chunk_size_suitability": "Chunk size suitability",
    "chunk_consistency": "Chunk consistency",
    "efficiency": "Processing/retrieval efficiency",
}


def score_strategies(metrics: Dict[str, StrategyMetrics]) -> Dict[str, StrategyScore]:
    """Return a StrategyScore for every strategy using configured weights."""
    weights = _normalized_weights(settings.score_weights)
    raw_table = _raw_factor_table(metrics)
    normalized = _minmax_normalize(raw_table)
    scores: Dict[str, StrategyScore] = {}
    for strategy, metric in metrics.items():
        factors: Dict[str, FactorScore] = {}
        total = 0.0
        for factor, raw in raw_table[strategy].items():
            norm = normalized[strategy][factor]
            weight = weights[factor]
            weighted = norm * weight
            total += weighted
            factors[factor] = FactorScore(
                name=factor,
                raw=round(raw, 4),
                normalized=round(norm, 4),
                weight=round(weight, 4),
                weighted=round(weighted, 4),
                interpretation=_interpret_factor(factor, raw, metric),
            )
        scores[strategy] = StrategyScore(
            strategy=strategy,
            label=metric.label,
            total=round(total, 4),
            factors=factors,
            metrics=metric,
        )
    return scores


def ranked_strategies(scores: Dict[str, StrategyScore]) -> List[StrategyScore]:
    """Sort by total score, breaking remaining ties with retrieval then size."""
    def key(item: StrategyScore) -> Tuple[float, float, float, float]:
        return (
            item.total,
            item.metrics.avg_top1,
            item.metrics.gold_hit_rate,
            item.metrics.size_suitability,
        )

    return sorted(scores.values(), key=key, reverse=True)


def _raw_factor_table(metrics: Dict[str, StrategyMetrics]) -> Dict[str, Dict[str, float]]:
    table: Dict[str, Dict[str, float]] = {}
    for strategy, metric in metrics.items():
        table[strategy] = {
            factor: float(getattr(metric, attr))
            for factor, attr in FACTOR_EXTRACTORS.items()
        }
    return table


def _minmax_normalize(
    raw_table: Dict[str, Dict[str, float]],
) -> Dict[str, Dict[str, float]]:
    factors = list(FACTOR_EXTRACTORS.keys())
    bounds: Dict[str, Tuple[float, float]] = {}
    for factor in factors:
        values = [raw_table[strategy][factor] for strategy in raw_table]
        bounds[factor] = (min(values), max(values))

    normalized: Dict[str, Dict[str, float]] = {}
    for strategy, raw_factors in raw_table.items():
        normalized[strategy] = {}
        for factor, raw in raw_factors.items():
            low, high = bounds[factor]
            if high - low < 1e-9:
                normalized[strategy][factor] = clamp(raw)
            else:
                normalized[strategy][factor] = (raw - low) / (high - low)
    return normalized


def _normalized_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(weights.values()) or 1.0
    return {key: value / total for key, value in weights.items()}


def _interpret_factor(factor: str, raw: float, metric: StrategyMetrics) -> str:
    label = FACTOR_LABELS[factor]
    if factor == "top1_similarity":
        return (
            f"{label} averaged {raw:.3f} across {metric.chunk_count} chunks "
            f"(gold-hit rate {metric.gold_hit_rate:.0%})."
        )
    if factor == "top3_similarity":
        return f"{label} averaged {raw:.3f}, showing how stable the top hits were."
    if factor == "best_retrieval":
        return f"{label} was {raw:.3f} (mean reciprocal rank {metric.mean_reciprocal_rank:.3f})."
    if factor == "chunk_size_suitability":
        return (
            f"Average chunk size was {metric.avg_chunk_chars:.0f} characters "
            f"(median {metric.median_chunk_chars:.0f}, range "
            f"{metric.min_chunk_chars}-{metric.max_chunk_chars})."
        )
    if factor == "chunk_consistency":
        return (
            f"Length CV was {metric.chunk_size_cv:.2f} with adjacent-chunk "
            f"coherence {metric.semantic_coherence:.3f} and overlap "
            f"{metric.overlap_ratio:.0%}."
        )
    return (
        f"Chunking took {metric.processing_ms:.1f} ms and retrieval took "
        f"{metric.retrieval_ms:.1f} ms for {metric.chunk_count} chunks."
    )
