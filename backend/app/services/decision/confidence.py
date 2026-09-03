"""Confidence is independent of the winning score.

It combines:
- margin between first and second strategy
- ranking stability (agreement between total score and retrieval rank)
- evidence quality (document size, query count, retrieval magnitude)
"""

from __future__ import annotations

from typing import Dict, List, Sequence

from app.config import settings
from app.models.schemas import (
    ConfidenceResult,
    DocumentProfile,
    StrategyScore,
    UncertaintyFactor,
)
from app.services.decision.scoring import ranked_strategies
from app.utils.helper import clamp


def assess_confidence(
    scores: Dict[str, StrategyScore],
    document: DocumentProfile,
    query_count: int,
) -> ConfidenceResult:
    """Compute a calibrated confidence percentage and supporting factors."""
    ranking = ranked_strategies(scores)
    if not ranking:
        return ConfidenceResult(
            percentage=0.0,
            level="none",
            margin=0.0,
            ranking_stability=0.0,
            evidence_quality=0.0,
            factors=[
                UncertaintyFactor(
                    code="no_scores",
                    severity="high",
                    statement="No strategy scores were produced, so confidence is zero.",
                )
            ],
            summary="No ranking is available.",
        )

    winner = ranking[0]
    runner = ranking[1] if len(ranking) > 1 else None
    margin = winner.total - runner.total if runner else winner.total
    margin_score = _margin_score(margin, winner.total)
    stability = _ranking_stability(ranking)
    evidence = _evidence_quality(ranking, document, query_count, winner)
    percentage = 100.0 * clamp(0.45 * margin_score + 0.25 * stability + 0.30 * evidence)
    factors = _uncertainty_factors(
        ranking, document, query_count, margin, stability, evidence, winner
    )
    if any(factor.severity == "high" for factor in factors):
        percentage = min(percentage, 62.0)
    elif document.is_small_document:
        percentage = min(percentage, 72.0)
    if runner and margin < 0.015:
        percentage = min(percentage, 55.0)
    level = _level(percentage)
    summary = _summary(winner, runner, percentage, level, margin, factors)
    return ConfidenceResult(
        percentage=round(percentage, 1),
        level=level,
        margin=round(margin, 4),
        ranking_stability=round(stability, 4),
        evidence_quality=round(evidence, 4),
        factors=factors,
        summary=summary,
    )


def _margin_score(margin: float, winner_total: float) -> float:
    if winner_total <= 0:
        return 0.0
    relative = margin / max(winner_total, 1e-6)
    return clamp(0.35 * clamp(margin / 0.12) + 0.65 * clamp(relative / 0.18))


def _ranking_stability(ranking: Sequence[StrategyScore]) -> float:
    by_retrieval = sorted(ranking, key=lambda item: item.metrics.avg_top1, reverse=True)
    by_consistency = sorted(ranking, key=lambda item: item.metrics.consistency, reverse=True)
    total_order = [item.strategy for item in ranking]
    retrieval_order = [item.strategy for item in by_retrieval]
    consistency_order = [item.strategy for item in by_consistency]
    top_agree = 1.0 if total_order[0] == retrieval_order[0] else 0.35
    kendall = _pairwise_agreement(total_order, retrieval_order)
    consistency_agree = 1.0 if total_order[0] == consistency_order[0] else 0.6
    return clamp(0.50 * top_agree + 0.35 * kendall + 0.15 * consistency_agree)


def _pairwise_agreement(left: List[str], right: List[str]) -> float:
    index_right = {name: i for i, name in enumerate(right)}
    pairs = 0
    agree = 0
    for i, a in enumerate(left):
        for b in left[i + 1 :]:
            pairs += 1
            if index_right[a] < index_right[b]:
                agree += 1
    return agree / pairs if pairs else 1.0


def _evidence_quality(
    ranking: Sequence[StrategyScore],
    document: DocumentProfile,
    query_count: int,
    winner: StrategyScore,
) -> float:
    size_score = clamp(document.char_count / 4000.0)
    query_score = clamp(query_count / float(settings.target_query_count))
    retrieval_score = clamp(winner.metrics.avg_top1 / 0.35)
    spread = ranking[0].total - ranking[-1].total if len(ranking) > 1 else 0.0
    spread_score = clamp(spread / 0.20)
    sentence_score = clamp(document.sentence_count / 12.0)
    return clamp(
        0.25 * size_score
        + 0.25 * query_score
        + 0.25 * retrieval_score
        + 0.15 * spread_score
        + 0.10 * sentence_score
    )


def _uncertainty_factors(
    ranking: Sequence[StrategyScore],
    document: DocumentProfile,
    query_count: int,
    margin: float,
    stability: float,
    evidence: float,
    winner: StrategyScore,
) -> List[UncertaintyFactor]:
    factors: List[UncertaintyFactor] = []
    runner = ranking[1] if len(ranking) > 1 else None
    if runner and margin < 0.02:
        factors.append(
            UncertaintyFactor(
                code="narrow_margin",
                severity="high",
                statement=(
                    f"{winner.label} leads {runner.label} by only {margin:.3f} on the "
                    f"weighted score ({winner.total:.3f} vs {runner.total:.3f}), so the "
                    "ranking could flip if a few queries change."
                ),
            )
        )
    elif runner and margin < 0.05:
        factors.append(
            UncertaintyFactor(
                code="modest_margin",
                severity="medium",
                statement=(
                    f"The gap between {winner.label} ({winner.total:.3f}) and "
                    f"{runner.label} ({runner.total:.3f}) is {margin:.3f}, which is "
                    "directionally useful but not decisive."
                ),
            )
        )
    retrieval_leader = max(ranking, key=lambda item: item.metrics.avg_top1)
    if retrieval_leader.strategy != winner.strategy:
        factors.append(
            UncertaintyFactor(
                code="score_retrieval_disagreement",
                severity="high",
                statement=(
                    f"{winner.label} wins the weighted score, but {retrieval_leader.label} "
                    f"has a higher Top-1 similarity ({retrieval_leader.metrics.avg_top1:.3f} "
                    f"vs {winner.metrics.avg_top1:.3f}). The recommendation blends factors "
                    "rather than optimizing retrieval alone."
                ),
            )
        )
    if document.is_small_document:
        factors.append(
            UncertaintyFactor(
                code="short_document",
                severity="high",
                statement=(
                    f"The document is only {document.char_count} characters and "
                    f"{document.sentence_count} sentences, so every strategy sees a "
                    "small evidence set and retrieval scores compress together."
                ),
            )
        )
    if query_count < settings.target_query_count:
        factors.append(
            UncertaintyFactor(
                code="few_queries",
                severity="medium",
                statement=(
                    f"Only {query_count} benchmark queries could be generated from this "
                    f"document (target {settings.target_query_count}), which reduces "
                    "ranking stability."
                ),
            )
        )
    if winner.metrics.avg_top1 < 0.18:
        factors.append(
            UncertaintyFactor(
                code="weak_retrieval",
                severity="high",
                statement=(
                    f"Even the recommended strategy's average Top-1 similarity is "
                    f"{winner.metrics.avg_top1:.3f}. That is weak lexical evidence, so "
                    "the ranking is relative rather than an absolute quality claim."
                ),
            )
        )
    if winner.metrics.chunk_count <= 2:
        factors.append(
            UncertaintyFactor(
                code="too_few_chunks",
                severity="medium",
                statement=(
                    f"{winner.label} produced {winner.metrics.chunk_count} chunk(s), "
                    "so Top-k ranking has little opportunity to miss or hit a gold span."
                ),
            )
        )
    if evidence < 0.4:
        factors.append(
            UncertaintyFactor(
                code="thin_evidence",
                severity="medium",
                statement=(
                    f"Evidence quality scored {evidence:.2f} because of document length, "
                    "query count, and retrieval magnitude. Treat the recommendation as "
                    "a starting point, not a production default."
                ),
            )
        )
    if stability < 0.55:
        factors.append(
            UncertaintyFactor(
                code="unstable_rank",
                severity="medium",
                statement=(
                    f"Ranking stability is {stability:.2f}: weighted scores and raw "
                    "Top-1 order do not fully agree, which increases uncertainty."
                ),
            )
        )
    if not factors:
        factors.append(
            UncertaintyFactor(
                code="stable_evidence",
                severity="low",
                statement=(
                    f"{winner.label} leads by {margin:.3f} with ranking stability "
                    f"{stability:.2f} and evidence quality {evidence:.2f} on a "
                    f"{document.char_count}-character document and {query_count} queries."
                ),
            )
        )
    return factors


def _level(percentage: float) -> str:
    if percentage >= 80:
        return "high"
    if percentage >= 60:
        return "moderate"
    if percentage >= 40:
        return "low"
    return "very_low"


def _summary(
    winner: StrategyScore,
    runner: StrategyScore | None,
    percentage: float,
    level: str,
    margin: float,
    factors: List[UncertaintyFactor],
) -> str:
    high_count = sum(1 for factor in factors if factor.severity == "high")
    if runner:
        return (
            f"Confidence is {percentage:.1f}% ({level}) because {winner.label} beats "
            f"{runner.label} by {margin:.3f} weighted points. "
            f"{high_count} high-severity uncertainty factor(s) remain."
        )
    return (
        f"Confidence is {percentage:.1f}% ({level}) based on a single scored strategy "
        f"({winner.label})."
    )
