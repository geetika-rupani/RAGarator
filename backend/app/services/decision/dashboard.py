"""Map pipeline results onto the dashboard view model.

The React client never computes rankings or explanations. This module only
rescales existing engine metrics into the 0-100 dimension scores the UI
renders, and copies the official recommendation from the decision engine.
"""

from __future__ import annotations

from typing import Dict, List

from app.config import settings
from app.models.schemas import (
    AnalysisResponse,
    QuerySpec,
    RetrievalReport,
    StrategyScore,
)
from app.utils.helper import preview_text

STRATEGY_TAGS = {
    "fixed": "character window",
    "recursive": "structure-aware",
    "sentence": "linguistic split",
    "token": "fixed token window",
}

LEVEL_LABELS = {
    "high": "High confidence",
    "moderate": "Moderate confidence",
    "low": "Low confidence",
    "very_low": "Very low confidence",
}

DEFAULT_WEIGHTS = {
    "retrieval": 60,
    "quality": 15,
    "consistency": 15,
    "efficiency": 10,
}

BEST_FOR = {
    "recursive": "Structured docs with headings",
    "sentence": "Prose-heavy, few headers",
    "token": "Stable token-sized windows",
    "fixed": "Simple overlapping character windows",
}


def build_dashboard(
    analysis: AnalysisResponse,
    reports: Dict[str, RetrievalReport],
    filename: str,
    size_bytes: int,
) -> dict:
    """Build the JSON payload consumed by the React dashboard."""
    rec = analysis.recommendation
    scores = rec.scores
    ranked = sorted(scores.values(), key=lambda item: item.total, reverse=True)
    strategies = [
        _strategy_card(score, reports, analysis.queries) for score in ranked
    ]
    winner = scores[rec.recommended_strategy]
    runner = ranked[1] if len(ranked) > 1 else None
    gap = (winner.total - runner.total) * 100 if runner else winner.total * 100
    query = analysis.queries[0].query if analysis.queries else ""
    return {
        "document": {
            "name": filename,
            "sizeLabel": _size_label(size_bytes),
            "pageCount": max(1, analysis.document.char_count // 2800),
            "chunkCount": winner.metrics.chunk_count,
        },
        "defaultWeights": DEFAULT_WEIGHTS,
        "recommendedStrategyId": rec.recommended_strategy,
        "confidence": {
            "label": f"{LEVEL_LABELS.get(rec.confidence.level, rec.confidence.level)} ({rec.confidence.percentage:.0f}%)",
            "gap": round(gap, 1),
            "detail": rec.confidence.summary,
        },
        "evidenceQuery": query,
        "strategies": strategies,
        "reasoning": rec.reasons,
        "uncertainty": {
            "summary": _uncertainty_summary(rec.confidence.summary, rec.uncertainty),
        },
        "tradeoffs": {"rows": _tradeoff_rows(ranked, rec.trade_offs)},
    }


def _strategy_card(
    score: StrategyScore,
    reports: Dict[str, RetrievalReport],
    queries: List[QuerySpec],
) -> dict:
    metrics = score.metrics
    factors = score.factors
    retrieval = _weighted_dim(
        factors,
        (("top1_similarity", 0.25), ("top3_similarity", 0.20), ("best_retrieval", 0.15)),
        0.60,
    )
    quality = int(round(100 * factors["chunk_size_suitability"].normalized))
    consistency = int(round(100 * factors["chunk_consistency"].normalized))
    efficiency = int(round(100 * factors["efficiency"].normalized))
    report = reports.get(score.strategy)
    evidence = _evidence(report)
    avg_tokens = max(1, int(round(metrics.avg_chunk_chars / 4)))
    return {
        "id": score.strategy,
        "name": score.label,
        "tag": STRATEGY_TAGS.get(score.strategy, score.strategy),
        "overall": round(score.total * 100, 1),
        "dims": {
            "retrieval": retrieval,
            "quality": quality,
            "consistency": consistency,
            "efficiency": efficiency,
        },
        "raw": {
            "recall5": round(metrics.gold_hit_rate, 4),
            "mrr": round(metrics.mean_reciprocal_rank, 4),
            "coherence": round(metrics.semantic_coherence, 4),
            "boundary": round(metrics.size_suitability, 4),
            "variance": round(metrics.chunk_size_cv, 4),
            "embedTimeSec": round((metrics.processing_ms + metrics.retrieval_ms) / 1000.0, 3),
            "avgChunks": metrics.chunk_count,
            "avgTokens": avg_tokens,
        },
        "evidence": evidence,
    }


def _weighted_dim(factors: dict, parts: tuple, denom: float) -> int:
    total = sum(factors[name].normalized * weight for name, weight in parts)
    return int(round(100 * total / denom))


def _evidence(report: RetrievalReport | None) -> dict:
    if not report or not report.per_query:
        return {"clean": True, "text": "No chunk was retrieved for the sample query."}
    first = report.per_query[0]
    if not first.retrieved:
        return {"clean": True, "text": "No chunk was retrieved for the sample query."}
    top = first.retrieved[0]
    text = top.text.strip()
    return {"clean": _looks_clean(text), "text": preview_text(text, 520)}


def _looks_clean(text: str) -> bool:
    if not text:
        return False
    start = text[0]
    if start.islower():
        return False
    end = text[-1]
    if end.isalnum() and len(text) > 80:
        return False
    return True


def _uncertainty_summary(summary: str, factors: list) -> str:
    extras = [item.statement for item in factors[:2]]
    if not extras:
        return summary
    return summary + " " + " ".join(extras)


def _tradeoff_rows(ranked: List[StrategyScore], trade_offs: list) -> List[dict]:
    ids = [item.strategy for item in ranked]
    by_id = {item.strategy: item for item in ranked}
    weakest = {
        item.strategy: _weak_point(item, ranked) for item in ranked
    }
    rows = [
        {
            "label": "Best for",
            "values": {sid: BEST_FOR.get(sid, settings.strategy_labels.get(sid, sid)) for sid in ids},
        },
        {"label": "Weak point", "values": weakest},
        {
            "label": "Avg. chunk size",
            "values": {sid: f"{by_id[sid].metrics.avg_chunk_chars:.0f} chars" for sid in ids},
        },
        {
            "label": "Top-1 similarity",
            "values": {sid: f"{by_id[sid].metrics.avg_top1:.3f}" for sid in ids},
        },
        {
            "label": "Gold-span hit rate",
            "values": {sid: f"{by_id[sid].metrics.gold_hit_rate:.0%}" for sid in ids},
        },
    ]
    if trade_offs:
        extra = {
            "label": "Engine note",
            "values": {sid: "" for sid in ids},
        }
        extra["values"][ids[0]] = trade_offs[0].detail
        rows.append(extra)
    return rows


def _weak_point(score: StrategyScore, ranked: List[StrategyScore]) -> str:
    metrics = score.metrics
    if metrics.avg_chunk_chars < 120:
        return "Chunks are often too small to hold a full span"
    if metrics.avg_chunk_chars > 900:
        return "Large windows mix unrelated sentences"
    if metrics.gold_hit_rate < 0.4:
        return "Misses more gold spans than peers"
    lowest = min(ranked, key=lambda item: item.metrics.efficiency)
    if lowest.strategy == score.strategy:
        return "Higher processing cost on this document"
    return f"Trails the leader by {(ranked[0].total - score.total) * 100:.1f} weighted points"


def _size_label(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{max(1, round(size_bytes / 1024))} KB"
