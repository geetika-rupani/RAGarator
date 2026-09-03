"""Build a document profile used by query generation and explanations."""

from __future__ import annotations

import re

from app.config import settings
from app.models.schemas import DocumentProfile
from app.utils.helper import count_tokens, preview_text, safe_mean, split_sentences

def profile_document(
    file_id: str,
    filename: str,
    extension: str,
    text: str,
) -> DocumentProfile:
    """Compute structural statistics for the cleaned document."""
    sentences = split_sentences(text)
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", text) if part.strip()]
    words = text.split()
    sentence_lengths = [len(sentence) for sentence in sentences]
    paragraph_lengths = [len(paragraph) for paragraph in paragraphs]
    headings = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and _looks_like_heading(line.strip())
    ]
    warnings: list[str] = []
    is_small = len(text) < settings.small_document_chars
    if is_small:
        warnings.append(
            f"Document is short ({len(text)} characters). Retrieval margins will be narrower "
            "and confidence will be capped."
        )
    if len(sentences) < 4:
        warnings.append(
            f"Only {len(sentences)} sentences were detected, so benchmark queries are limited."
        )
    if len(paragraphs) <= 1:
        warnings.append(
            "The document has little paragraph structure, which typically favors sentence "
            "or token chunking over recursive splits."
        )
    return DocumentProfile(
        file_id=file_id,
        filename=filename,
        extension=extension,
        char_count=len(text),
        word_count=len(words),
        sentence_count=len(sentences),
        paragraph_count=len(paragraphs),
        estimated_tokens=count_tokens(text),
        avg_sentence_chars=round(safe_mean(sentence_lengths), 1),
        avg_paragraph_chars=round(safe_mean(paragraph_lengths), 1),
        heading_count=len(headings),
        is_small_document=is_small,
        warnings=warnings,
        preview=preview_text(text, 280),
    )


def _looks_like_heading(line: str) -> bool:
    if len(line) > 90 or len(line) < 6:
        return False
    if line.endswith("."):
        return False
    letters = [char for char in line if char.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(char.isupper() for char in letters) / len(letters)
    return upper_ratio > 0.7 or bool(re.match(r"^\d+(\.\d+)*\s+\S", line))
