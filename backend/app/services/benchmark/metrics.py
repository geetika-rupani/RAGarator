"""Numeric helpers specific to retrieval benchmarking."""

from __future__ import annotations

from typing import Iterable, Optional, Sequence

from app.utils.helper import safe_mean


def mean_reciprocal_rank(ranks: Sequence[Optional[int]]) -> float:
    """MRR over gold ranks; missing hits contribute 0."""
    values = [1.0 / rank if rank and rank > 0 else 0.0 for rank in ranks]
    return safe_mean(values)


def hit_rate(ranks: Iterable[Optional[int]]) -> float:
    ranks = list(ranks)
    if not ranks:
        return 0.0
    return sum(1 for rank in ranks if rank is not None) / len(ranks)
