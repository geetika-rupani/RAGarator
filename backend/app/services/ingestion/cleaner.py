"""Normalize extracted document text before chunking."""

from __future__ import annotations

import re

from app.utils.helper import HYPHEN_BREAK_RE, normalize_whitespace

CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
PAGE_NUMBER_RE = re.compile(r"\n\s*(?:page\s*)?\d{1,4}\s*(?:/\s*\d{1,4})?\s*\n", re.I)


def clean_text(raw: str) -> str:
    """Repair extraction artifacts without deleting document meaning."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = CONTROL_RE.sub("", text)
    text = HYPHEN_BREAK_RE.sub(r"\1\2", text)
    text = text.replace("\u00ad", "")
    text = PAGE_NUMBER_RE.sub("\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = normalize_whitespace(text)
    return text
