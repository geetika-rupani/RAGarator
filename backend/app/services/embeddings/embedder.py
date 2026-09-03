"""TF-IDF embeddings with cosine similarity.

A local TF-IDF representation keeps the benchmark deterministic, fast, and
free of external model APIs while still measuring lexical retrieval quality
on the user's document.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class EmbeddedCorpus:
    """Vectorized corpus plus the fitted vectorizer."""

    vectorizer: TfidfVectorizer
    matrix: np.ndarray
    texts: List[str]


def fit_corpus(texts: Sequence[str]) -> EmbeddedCorpus:
    """Fit a TF-IDF vectorizer on chunk texts and transform them."""
    cleaned = [text if text.strip() else " " for text in texts]
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_df=1.0,
        norm="l2",
        sublinear_tf=True,
        token_pattern=r"(?u)\b\w+\b",
    )
    try:
        matrix = vectorizer.fit_transform(cleaned)
    except ValueError:
        vectorizer = TfidfVectorizer(
            lowercase=True,
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=1,
        )
        matrix = vectorizer.fit_transform(cleaned)
    return EmbeddedCorpus(vectorizer=vectorizer, matrix=matrix, texts=list(cleaned))


def embed_query(corpus: EmbeddedCorpus, query: str) -> np.ndarray:
    """Transform a query with the corpus vectorizer."""
    return corpus.vectorizer.transform([query or " "])


def cosine_scores(corpus: EmbeddedCorpus, query: str) -> np.ndarray:
    """Return cosine similarity of the query against every corpus vector."""
    query_vec = embed_query(corpus, query)
    scores = cosine_similarity(query_vec, corpus.matrix)[0]
    return np.clip(scores.astype(float), 0.0, 1.0)


def pairwise_coherence(texts: Sequence[str]) -> float:
    """Mean cosine similarity of each chunk to the next sequential chunk."""
    if len(texts) < 2:
        return 1.0 if texts else 0.0
    corpus = fit_corpus(texts)
    if corpus.matrix.shape[0] < 2:
        return 1.0
    sims = cosine_similarity(corpus.matrix)
    adjacent = [float(sims[i, i + 1]) for i in range(len(texts) - 1)]
    return float(sum(adjacent) / len(adjacent))
