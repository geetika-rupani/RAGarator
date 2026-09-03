"""Application configuration for RAGarator."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and defaults."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "RAGarator"
    app_version: str = "1.0.0"
    debug: bool = False

    upload_dir: Path = Path(__file__).resolve().parent.parent / "uploads"
    max_file_size_mb: int = 50
    max_document_chars: int = 400_000
    allowed_extensions: Tuple[str, ...] = (".pdf", ".docx", ".txt")

    min_document_chars: int = 80
    small_document_chars: int = 800
    target_query_count: int = 8
    min_query_count: int = 3
    retrieval_k: int = 3

    fixed_chunk_size: int = 500
    fixed_overlap: int = 80
    recursive_chunk_size: int = 500
    recursive_overlap: int = 80
    sentence_target_chars: int = 450
    token_chunk_size: int = 128
    token_overlap: int = 20

    optimal_chunk_chars: Tuple[int, int] = (220, 800)
    chunk_chars_hard_min: int = 40
    chunk_chars_hard_max: int = 1800

    score_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "top1_similarity": 0.25,
            "top3_similarity": 0.20,
            "best_retrieval": 0.15,
            "chunk_size_suitability": 0.15,
            "chunk_consistency": 0.15,
            "efficiency": 0.10,
        }
    )

    strategy_labels: Dict[str, str] = Field(
        default_factory=lambda: {
            "fixed": "Fixed-size",
            "recursive": "Recursive",
            "sentence": "Sentence-based",
            "token": "Token-based",
        }
    )
    strategy_order: List[str] = Field(
        default_factory=lambda: ["fixed", "recursive", "sentence", "token"]
    )

    @property
    def max_file_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()
