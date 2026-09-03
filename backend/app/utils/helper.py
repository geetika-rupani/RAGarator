"""Text and numeric helpers shared across ingestion, chunking, and evaluation."""

from __future__ import annotations

import math
import re
from typing import Iterable, List, Sequence

TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?")
WHITESPACE_RE = re.compile(r"[ \t]+")
MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
HYPHEN_BREAK_RE = re.compile(r"(\w)-\n(\w)")


def normalize_whitespace(text: str) -> str:
    """Collapse messy whitespace while preserving paragraph breaks."""
    compact = WHITESPACE_RE.sub(" ", text)
    compact = MULTI_NEWLINE_RE.sub("\n\n", compact)
    return compact.strip()


def count_tokens(text: str) -> int:
    """Count word-like tokens used by the token chunker and metadata."""
    return len(TOKEN_RE.findall(text))


def tokenize(text: str) -> List[str]:
    """Return lowercase word-like tokens."""
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def split_sentences(text: str) -> List[str]:
    """Split text into sentences with a conservative regex splitter."""
    if not text.strip():
        return []
    parts = re.split(r"(?<=[.!?])\s+|\n{2,}", text.strip())
    sentences = [re.sub(r"\s+", " ", part).strip() for part in parts]
    return [sentence for sentence in sentences if sentence]


def preview_text(text: str, limit: int = 180) -> str:
    """Return a single-line preview suitable for API responses."""
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def safe_mean(values: Sequence[float], default: float = 0.0) -> float:
    if not values:
        return default
    return float(sum(values) / len(values))


def safe_std(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = safe_mean(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def coefficient_of_variation(values: Sequence[float]) -> float:
    mean = safe_mean(values)
    if mean <= 0:
        return 0.0
    return safe_std(values) / mean


def median(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return float(ordered[mid - 1] + ordered[mid]) / 2.0


def unique(items: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
