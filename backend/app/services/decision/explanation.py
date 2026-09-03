"""Build document-specific reasons, trade-offs, and retrieval evidence."""

from __future__ import annotations

from typing import Dict, List

from app.config import settings
from app.models.schemas import (
    DocumentProfile,
    EvidenceItem,
    QuerySpec,
    RetrievalReport,
    StrategyScore,
    TradeOff,
)
from app.services.decision.scoring import FACTOR_LABELS, ranked_strategies
from app.services.evaluation.retrieval_quality import compare_query_winners, strongest_queries
from app.utils.helper import preview_text


def build_reasons(
    scores: Dict[str, StrategyScore],
    document: DocumentProfile,
    queries: List[QuerySpec],
) -> List[str]:
    """Explain the ranking with actual numbers from this document."""
    ranking = ranked_strategies(scores)
    if not ranking:
        return ["No strategies produced a score."]
    winner = ranking[0]
    reasons: List[str] = []
    reasons.append(
        f"{winner.label} is recommended for '{document.filename}' "
        f"({document.char_count} characters, {document.sentence_count} sentences, "
        f"{document.paragraph_count} paragraphs) with a weighted score of "
        f"{winner.total:.3f}."
    )
    if len(ranking) > 1:
        runner = ranking[1]
        delta_top1 = winner.metrics.avg_top1 - runner.metrics.avg_top1
        direction = "outperforming" if delta_top1 >= 0 else "trailing"
        reasons.append(
            f"{winner.label} achieved {winner.metrics.avg_top1:.3f} average Top-1 "
            f"similarity, {direction} {runner.label} ({runner.metrics.avg_top1:.3f}), "
            f"while using {winner.metrics.chunk_count} chunks averaging "
            f"{winner.metrics.avg_chunk_chars:.0f} characters."
        )
        reasons.append(
            f"Top-3 similarity was {winner.metrics.avg_top3:.3f} for {winner.label} "
            f"versus {runner.metrics.avg_top3:.3f} for {runner.label}; gold-span hit "
            f"rate was {winner.metrics.gold_hit_rate:.0%} vs "
            f"{runner.metrics.gold_hit_rate:.0%} across {len(queries)} queries."
        )
    reasons.append(
        f"Chunk size suitability is {winner.metrics.size_suitability:.3f} because the "
        f"average chunk is {winner.metrics.avg_chunk_chars:.0f} characters "
        f"(median {winner.metrics.median_chunk_chars:.0f}, min "
        f"{winner.metrics.min_chunk_chars}, max {winner.metrics.max_chunk_chars}) "
        f"on a document whose sentences average {document.avg_sentence_chars:.0f} "
        "characters."
    )
    reasons.append(
        f"Consistency is {winner.metrics.consistency:.3f}: length CV "
        f"{winner.metrics.chunk_size_cv:.2f}, adjacent-chunk coherence "
        f"{winner.metrics.semantic_coherence:.3f}, overlap "
        f"{winner.metrics.overlap_ratio:.0%}."
    )
    reasons.append(
        f"Efficiency is {winner.metrics.efficiency:.3f} after "
        f"{winner.metrics.processing_ms:.1f} ms of chunking and "
        f"{winner.metrics.retrieval_ms:.1f} ms of retrieval."
    )
    dominant = _dominant_factors(winner)
    if dominant:
        reasons.append(
            "The largest weighted contributions came from "
            + "; ".join(dominant)
            + "."
        )
    if document.heading_count >= 3:
        reasons.append(
            f"The document has {document.heading_count} detected headings, which "
            f"{_heading_fit(winner.strategy)}."
        )
    elif document.paragraph_count <= 2:
        reasons.append(
            "Little paragraph structure was detected, so strategies that split on "
            "sentences or tokens preserve more answer boundaries than recursive "
            "paragraph splits."
        )
    return reasons


def build_tradeoffs(scores: Dict[str, StrategyScore]) -> List[TradeOff]:
    ranking = ranked_strategies(scores)
    if len(ranking) < 2:
        return []
    winner = ranking[0]
    tradeoffs: List[TradeOff] = []
    densest = min(ranking, key=lambda item: item.metrics.avg_chunk_chars or 10**9)
    largest = max(ranking, key=lambda item: item.metrics.avg_chunk_chars)
    fastest = max(ranking, key=lambda item: item.metrics.efficiency)
    most_consistent = max(ranking, key=lambda item: item.metrics.consistency)
    best_retrieval = max(ranking, key=lambda item: item.metrics.avg_top1)

    if densest.strategy != winner.strategy:
        tradeoffs.append(
            TradeOff(
                title=f"{densest.label} produces smaller chunks",
                detail=(
                    f"{densest.label} averages {densest.metrics.avg_chunk_chars:.0f} "
                    f"characters across {densest.metrics.chunk_count} chunks versus "
                    f"{winner.metrics.avg_chunk_chars:.0f} for {winner.label}. Smaller "
                    "windows can isolate a fact but drop surrounding context."
                ),
            )
        )
    if largest.strategy != winner.strategy and largest.metrics.avg_chunk_chars > winner.metrics.avg_chunk_chars + 80:
        tradeoffs.append(
            TradeOff(
                title=f"{largest.label} keeps more context per chunk",
                detail=(
                    f"{largest.label} averages {largest.metrics.avg_chunk_chars:.0f} "
                    f"characters (max {largest.metrics.max_chunk_chars}), which can help "
                    "multi-sentence answers at the cost of noisier retrieval."
                ),
            )
        )
    if fastest.strategy != winner.strategy:
        tradeoffs.append(
            TradeOff(
                title=f"{fastest.label} is cheaper to run",
                detail=(
                    f"{fastest.label} scored {fastest.metrics.efficiency:.3f} efficiency "
                    f"({fastest.metrics.processing_ms:.1f} + {fastest.metrics.retrieval_ms:.1f} ms) "
                    f"versus {winner.metrics.efficiency:.3f} for {winner.label}."
                ),
            )
        )
    if most_consistent.strategy != winner.strategy:
        tradeoffs.append(
            TradeOff(
                title=f"{most_consistent.label} is more uniform",
                detail=(
                    f"{most_consistent.label} consistency is {most_consistent.metrics.consistency:.3f} "
                    f"(CV {most_consistent.metrics.chunk_size_cv:.2f}) compared with "
                    f"{winner.metrics.consistency:.3f} for {winner.label}."
                ),
            )
        )
    if best_retrieval.strategy != winner.strategy:
        tradeoffs.append(
            TradeOff(
                title=f"{best_retrieval.label} retrieves slightly better in isolation",
                detail=(
                    f"Top-1 similarity is {best_retrieval.metrics.avg_top1:.3f} for "
                    f"{best_retrieval.label} versus {winner.metrics.avg_top1:.3f} for "
                    f"{winner.label}. The recommended strategy still wins after size, "
                    "consistency, and efficiency are included."
                ),
            )
        )
    if not tradeoffs:
        runner = ranking[1]
        tradeoffs.append(
            TradeOff(
                title=f"{runner.label} is the closest alternative",
                detail=(
                    f"{runner.label} scores {runner.total:.3f} against "
                    f"{winner.total:.3f}. Use it if you prefer its "
                    f"{runner.metrics.avg_chunk_chars:.0f}-character chunks over "
                    f"{winner.label}'s {winner.metrics.avg_chunk_chars:.0f}-character chunks."
                ),
            )
        )
    return tradeoffs


def build_evidence(
    winner_strategy: str,
    scores: Dict[str, StrategyScore],
    reports: Dict[str, RetrievalReport],
) -> List[EvidenceItem]:
    """Cite real retrieved spans rather than generic quality claims."""
    ranking = ranked_strategies(scores)
    runner = ranking[1].strategy if len(ranking) > 1 else None
    winner_report = reports.get(winner_strategy)
    if not winner_report:
        return []
    items: List[EvidenceItem] = []
    query_winners = compare_query_winners(reports)
    for best_strategy, second_strategy, best_result, second_result in query_winners:
        if best_strategy != winner_strategy:
            continue
        top = best_result.retrieved[0] if best_result.retrieved else None
        runner_preview = None
        runner_sim = None
        if runner and runner in reports:
            match = next(
                (q for q in reports[runner].per_query if q.query_id == best_result.query_id),
                None,
            )
            if match and match.retrieved:
                runner_preview = match.retrieved[0].preview
                runner_sim = match.retrieved[0].similarity
        note = (
            f"For the query '{best_result.query}', {settings.strategy_labels[winner_strategy]} "
            f"ranked a chunk at similarity {best_result.top1_similarity:.3f}"
        )
        if runner_sim is not None:
            note += f" versus {settings.strategy_labels.get(runner, runner)} at {runner_sim:.3f}"
        if top and top.contains_gold:
            note += ", and the retrieved chunk contains the gold excerpt"
        note += "."
        items.append(
            EvidenceItem(
                query=best_result.query,
                winner_preview=top.preview if top else "",
                winner_similarity=best_result.top1_similarity,
                runner_up_preview=runner_preview,
                runner_up_similarity=runner_sim,
                gold_excerpt=preview_text(best_result.gold_excerpt, 160),
                note=note,
            )
        )
        if len(items) >= 3:
            break
    if not items:
        for result in strongest_queries(winner_report, 2):
            top = result.retrieved[0] if result.retrieved else None
            items.append(
                EvidenceItem(
                    query=result.query,
                    winner_preview=top.preview if top else "",
                    winner_similarity=result.top1_similarity,
                    runner_up_preview=None,
                    runner_up_similarity=None,
                    gold_excerpt=preview_text(result.gold_excerpt, 160),
                    note=(
                        f"{settings.strategy_labels[winner_strategy]} retrieved "
                        f"'{preview_text(top.preview if top else '', 90)}' at "
                        f"{result.top1_similarity:.3f} for '{result.query}'."
                    ),
                )
            )
    return items


def _dominant_factors(score: StrategyScore) -> List[str]:
    ordered = sorted(score.factors.values(), key=lambda item: item.weighted, reverse=True)
    parts: List[str] = []
    for factor in ordered[:3]:
        parts.append(
            f"{FACTOR_LABELS[factor.name]} (raw {factor.raw:.3f}, "
            f"weighted {factor.weighted:.3f})"
        )
    return parts


def _heading_fit(strategy: str) -> str:
    if strategy == "recursive":
        return "usually favors recursive splitting on headings and paragraphs"
    if strategy == "sentence":
        return "still leaves sentence packing competitive when headings are short"
    if strategy == "fixed":
        return "does not align with heading boundaries, which is a cost of fixed windows"
    return "is only weakly used by token windows, which ignore heading structure"
