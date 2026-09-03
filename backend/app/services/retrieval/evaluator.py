"""Run benchmark queries against one chunking strategy."""

from __future__ import annotations

import time
from typing import List, Optional

from app.config import settings
from app.models.schemas import (
    ChunkingResult,
    QueryResult,
    QuerySpec,
    RetrievalReport,
)
from app.services.retrieval.retriever import build_corpus, retrieve
from app.utils.helper import safe_mean


def evaluate_retrieval(
    chunking: ChunkingResult,
    queries: List[QuerySpec],
    k: int | None = None,
) -> RetrievalReport:
    """Retrieve for every query and aggregate Top-1 / Top-3 / gold-hit metrics."""
    top_k = k or settings.retrieval_k
    started = time.perf_counter()
    if not chunking.chunks or not queries:
        return RetrievalReport(
            strategy=chunking.strategy,
            query_count=len(queries),
            avg_top1=0.0,
            avg_top3=0.0,
            avg_best=0.0,
            gold_hit_rate=0.0,
            mean_reciprocal_rank=0.0,
            per_query=[],
            retrieval_ms=0.0,
        )

    corpus = build_corpus(chunking.chunks)
    per_query: List[QueryResult] = []
    gold_hits = 0
    rr_values: List[float] = []

    for spec in queries:
        retrieved = retrieve(
            chunking.chunks,
            corpus,
            spec.query,
            top_k,
            gold_excerpt=spec.gold_excerpt,
        )
        similarities = [item.similarity for item in retrieved]
        top1 = similarities[0] if similarities else 0.0
        top3 = safe_mean(similarities[:3])
        best = max(similarities) if similarities else 0.0
        gold_rank = _gold_rank(retrieved)
        if gold_rank is not None:
            gold_hits += 1
            rr_values.append(1.0 / gold_rank)
        else:
            rr_values.append(0.0)
        per_query.append(
            QueryResult(
                query_id=spec.query_id,
                query=spec.query,
                gold_excerpt=spec.gold_excerpt,
                top1_similarity=round(top1, 4),
                top3_similarity=round(top3, 4),
                best_similarity=round(best, 4),
                gold_hit_rank=gold_rank,
                retrieved=retrieved,
            )
        )

    elapsed_ms = (time.perf_counter() - started) * 1000
    return RetrievalReport(
        strategy=chunking.strategy,
        query_count=len(per_query),
        avg_top1=round(safe_mean([item.top1_similarity for item in per_query]), 4),
        avg_top3=round(safe_mean([item.top3_similarity for item in per_query]), 4),
        avg_best=round(safe_mean([item.best_similarity for item in per_query]), 4),
        gold_hit_rate=round(gold_hits / len(per_query), 4) if per_query else 0.0,
        mean_reciprocal_rank=round(safe_mean(rr_values), 4),
        per_query=per_query,
        retrieval_ms=round(elapsed_ms, 2),
    )


def _gold_rank(retrieved: List) -> Optional[int]:
    for item in retrieved:
        if item.contains_gold:
            return item.rank
    return None
