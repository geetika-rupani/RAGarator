"""Top-k cosine retrieval over an embedded chunk corpus."""

from __future__ import annotations

from typing import List

import numpy as np

from app.models.schemas import ChunkRecord, RetrievedChunk
from app.services.embeddings.embedder import EmbeddedCorpus, cosine_scores, fit_corpus
from app.utils.helper import preview_text


def build_corpus(chunks: List[ChunkRecord]) -> EmbeddedCorpus:
    """Fit embeddings on chunk text."""
    return fit_corpus([chunk.text for chunk in chunks])


def retrieve(
    chunks: List[ChunkRecord],
    corpus: EmbeddedCorpus,
    query: str,
    k: int,
    gold_excerpt: str = "",
) -> List[RetrievedChunk]:
    """Return the top-k chunks for a query with gold-span overlap flags."""
    if not chunks:
        return []
    scores = cosine_scores(corpus, query)
    k = max(1, min(k, len(chunks)))
    order = np.argsort(scores)[::-1][:k]
    gold = gold_excerpt.strip().lower()
    results: List[RetrievedChunk] = []
    for rank, index in enumerate(order, start=1):
        chunk = chunks[int(index)]
        contains_gold = bool(gold) and _contains_gold(chunk.text, gold)
        results.append(
            RetrievedChunk(
                rank=rank,
                chunk_index=chunk.index,
                similarity=round(float(scores[int(index)]), 4),
                preview=preview_text(chunk.text, 180),
                text=chunk.text,
                contains_gold=contains_gold,
            )
        )
    return results


def _contains_gold(chunk_text: str, gold: str) -> bool:
    haystack = " ".join(chunk_text.lower().split())
    needle = " ".join(gold.split())
    if needle and needle in haystack:
        return True
    gold_tokens = needle.split()
    if len(gold_tokens) < 6:
        return False
    window = gold_tokens[:12]
    return " ".join(window) in haystack
