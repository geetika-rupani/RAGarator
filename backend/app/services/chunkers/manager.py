"""Run every chunking strategy and collect comparable results."""

from __future__ import annotations

import time
from typing import Callable, Dict, List

from app.config import settings
from app.models.schemas import ChunkRecord, ChunkingResult
from app.services.chunkers.fixed import chunk_fixed
from app.services.chunkers.recursive import chunk_recursive
from app.services.chunkers.sentence import chunk_sentence
from app.services.chunkers.token import chunk_token
from app.utils.helper import median, safe_mean, safe_std

ChunkFn = Callable[[str], List[ChunkRecord]]

STRATEGY_FNS: Dict[str, ChunkFn] = {
    "fixed": chunk_fixed,
    "recursive": chunk_recursive,
    "sentence": chunk_sentence,
    "token": chunk_token,
}


def run_all_chunkers(text: str) -> Dict[str, ChunkingResult]:
    """Apply each configured strategy to the same cleaned document."""
    results: Dict[str, ChunkingResult] = {}
    for strategy in settings.strategy_order:
        started = time.perf_counter()
        chunks = STRATEGY_FNS[strategy](text)
        elapsed_ms = (time.perf_counter() - started) * 1000
        results[strategy] = summarize_chunks(strategy, chunks, elapsed_ms)
    return results


def summarize_chunks(
    strategy: str,
    chunks: List[ChunkRecord],
    processing_ms: float,
) -> ChunkingResult:
    """Compute overlap and length statistics for a chunk list."""
    char_counts = [chunk.char_count for chunk in chunks]
    overlap_ratio = _overlap_ratio(chunks)
    empty_count = sum(1 for chunk in chunks if not chunk.text.strip())
    return ChunkingResult(
        strategy=strategy,
        label=settings.strategy_labels[strategy],
        chunks=chunks,
        chunk_count=len(chunks),
        avg_char_count=round(safe_mean(char_counts), 1),
        median_char_count=round(median(char_counts), 1),
        std_char_count=round(safe_std(char_counts), 1),
        min_char_count=min(char_counts) if char_counts else 0,
        max_char_count=max(char_counts) if char_counts else 0,
        overlap_ratio=round(overlap_ratio, 4),
        empty_chunk_count=empty_count,
        processing_ms=round(processing_ms, 2),
    )


def _overlap_ratio(chunks: List[ChunkRecord]) -> float:
    if len(chunks) < 2:
        return 0.0
    ratios: List[float] = []
    for left, right in zip(chunks, chunks[1:]):
        shared = _shared_token_fraction(left.text, right.text)
        ratios.append(shared)
    return safe_mean(ratios)


def _shared_token_fraction(left: str, right: str) -> float:
    left_tokens = left.lower().split()
    right_tokens = right.lower().split()
    if not left_tokens or not right_tokens:
        return 0.0
    window = min(40, len(left_tokens), len(right_tokens))
    left_tail = left_tokens[-window:]
    right_head = right_tokens[:window]
    left_set = set(left_tail)
    if not left_set:
        return 0.0
    shared = sum(1 for token in right_head if token in left_set)
    return shared / window
