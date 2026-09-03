"""Generate grounded benchmark queries from the uploaded document.

Queries are derived from actual sentences so gold excerpts exist in the
text. That keeps retrieval evaluation honest: a hit means the chunk
contains the source span, not a synthetic label.
"""

from __future__ import annotations

import re
from typing import List

from app.config import settings
from app.models.schemas import DocumentProfile, QuerySpec
from app.utils.helper import split_sentences, unique

STOPWORDS = {
    "the", "and", "for", "that", "with", "this", "from", "have", "were",
    "been", "will", "they", "their", "which", "into", "about", "would",
    "there", "could", "should", "after", "before", "where", "when", "what",
    "your", "you", "are", "was", "not", "but", "all", "can", "has", "had",
    "its", "also", "than", "then", "them", "these", "those", "over", "under",
    "such", "only", "other", "more", "most", "some", "any", "each", "per",
}

GENERIC_PREFIXES = (
    "What does the document say about {topic}?",
    "Which details describe {topic}?",
    "How is {topic} explained in the document?",
    "What evidence is given for {topic}?",
    "Summarize the document's claim about {topic}.",
    "Where is {topic} discussed and what is stated?",
    "What outcome or result is associated with {topic}?",
    "What definition or description is provided for {topic}?",
)


def generate_queries(text: str, document: DocumentProfile) -> List[QuerySpec]:
    """Build a bounded set of document-specific queries with gold excerpts."""
    sentences = [
        sentence
        for sentence in split_sentences(text)
        if 40 <= len(sentence) <= 320
    ]
    if not sentences:
        fallback = text.strip()[:240]
        if not fallback:
            return []
        return [
            QuerySpec(
                query_id="q1",
                query="What is the main content of this document?",
                source="fallback",
                gold_excerpt=fallback,
                reason="The document is too short to extract multiple distinctive sentences.",
            )
        ]

    scored = sorted(sentences, key=_sentence_information, reverse=True)
    selected = _diversify(scored, limit=settings.target_query_count)
    if len(selected) < settings.min_query_count:
        selected = scored[: max(settings.min_query_count, len(scored))]

    queries: List[QuerySpec] = []
    used_topics: List[str] = []
    for index, sentence in enumerate(selected):
        topic = _topic_phrase(sentence, used_topics)
        used_topics.append(topic)
        template = GENERIC_PREFIXES[index % len(GENERIC_PREFIXES)]
        query = template.format(topic=topic)
        queries.append(
            QuerySpec(
                query_id=f"q{index + 1}",
                query=query,
                source="document_sentence",
                gold_excerpt=sentence,
                reason=(
                    f"Derived from a high-information sentence ({len(sentence)} chars) "
                    f"so the gold span is guaranteed to exist in the source text."
                ),
            )
        )
    if document.heading_count and len(queries) < settings.target_query_count:
        heading_query = _heading_query(text, len(queries) + 1)
        if heading_query:
            queries.append(heading_query)
    return queries[: settings.target_query_count]


def _sentence_information(sentence: str) -> float:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", sentence)
    content = [token for token in tokens if token.lower() not in STOPWORDS]
    digits = len(re.findall(r"\d+", sentence))
    proper = sum(1 for token in content if token[:1].isupper())
    length_bonus = min(len(sentence) / 180.0, 1.2)
    return len(content) + 1.5 * digits + 0.4 * proper + length_bonus


def _diversify(sentences: List[str], limit: int) -> List[str]:
    chosen: List[str] = []
    for sentence in sentences:
        if len(chosen) >= limit:
            break
        if all(_jaccard(sentence, existing) < 0.45 for existing in chosen):
            chosen.append(sentence)
    return chosen


def _jaccard(left: str, right: str) -> float:
    a = set(left.lower().split())
    b = set(right.lower().split())
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _topic_phrase(sentence: str, used: List[str]) -> str:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", sentence)
    content = [token for token in tokens if token.lower() not in STOPWORDS]
    if not content:
        snippet = sentence[:48].rstrip()
        return snippet.lower()
    candidates = []
    for size in (3, 2, 1):
        if len(content) >= size:
            phrase = " ".join(content[:size]).lower()
            candidates.append(phrase)
    for phrase in unique(candidates):
        if phrase not in used:
            return phrase
    return content[0].lower()


def _heading_query(text: str, next_id: int) -> QuerySpec | None:
    for line in text.splitlines():
        stripped = line.strip()
        if 8 <= len(stripped) <= 80 and stripped.isupper():
            return QuerySpec(
                query_id=f"q{next_id}",
                query=f"What does the section '{stripped.title()}' cover?",
                source="heading",
                gold_excerpt=stripped,
                reason="Uses a detected heading as a grounded retrieval target.",
            )
    return None
