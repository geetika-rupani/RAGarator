"""Helpers that interpret retrieval metrics for explanations."""

from __future__ import annotations

from typing import Dict, List, Tuple

from app.models.schemas import QueryResult, RetrievalReport


def strongest_queries(report: RetrievalReport, limit: int = 3) -> List[QueryResult]:
    """Queries where this strategy's Top-1 similarity was highest."""
    ranked = sorted(report.per_query, key=lambda item: item.top1_similarity, reverse=True)
    return ranked[:limit]


def weakest_queries(report: RetrievalReport, limit: int = 2) -> List[QueryResult]:
    ranked = sorted(report.per_query, key=lambda item: item.top1_similarity)
    return ranked[:limit]


def compare_query_winners(
    reports: Dict[str, RetrievalReport],
) -> List[Tuple[str, str, QueryResult, QueryResult | None]]:
    """For each query, identify the strategy with the best Top-1 hit."""
    if not reports:
        return []
    any_report = next(iter(reports.values()))
    rows: List[Tuple[str, str, QueryResult, QueryResult | None]] = []
    for index, spec_result in enumerate(any_report.per_query):
        best_strategy = None
        best_result: QueryResult | None = None
        second_strategy = None
        second_result: QueryResult | None = None
        for strategy, report in reports.items():
            if index >= len(report.per_query):
                continue
            result = report.per_query[index]
            if best_result is None or result.top1_similarity > best_result.top1_similarity:
                second_strategy, second_result = best_strategy, best_result
                best_strategy, best_result = strategy, result
            elif second_result is None or result.top1_similarity > second_result.top1_similarity:
                second_strategy, second_result = strategy, result
        if best_strategy and best_result:
            rows.append((best_strategy, second_strategy or "", best_result, second_result))
    return rows
