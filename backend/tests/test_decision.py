"""Unit tests for scoring fairness, confidence, and pipeline safety."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import settings
from app.models.schemas import DocumentProfile, StrategyMetrics
from app.services.chunkers.manager import run_all_chunkers
from app.services.decision.confidence import assess_confidence
from app.services.decision.scoring import ranked_strategies, score_strategies
from app.services.pipeline.analyzer import analyze_file
from app.utils.errors import DocumentTooSmallError, EmptyDocumentError


SAMPLE = Path(__file__).resolve().parents[2] / "samples" / "rag_methods.txt"


def _metrics(**overrides) -> StrategyMetrics:
    base = dict(
        strategy="fixed",
        label="Fixed-size",
        chunk_count=10,
        avg_chunk_chars=400.0,
        median_chunk_chars=400.0,
        min_chunk_chars=300,
        max_chunk_chars=500,
        chunk_size_cv=0.1,
        overlap_ratio=0.1,
        semantic_coherence=0.4,
        size_suitability=0.8,
        consistency=0.7,
        efficiency=0.6,
        processing_ms=5.0,
        retrieval_ms=8.0,
        avg_top1=0.3,
        avg_top3=0.25,
        avg_best=0.32,
        gold_hit_rate=0.5,
        mean_reciprocal_rank=0.4,
        empty_chunk_count=0,
        warnings=[],
    )
    base.update(overrides)
    return StrategyMetrics(**base)


def _document(chars: int = 5000, sentences: int = 40, small: bool = False) -> DocumentProfile:
    return DocumentProfile(
        file_id="abc",
        filename="doc.txt",
        extension=".txt",
        char_count=chars,
        word_count=800,
        sentence_count=sentences,
        paragraph_count=12,
        estimated_tokens=700,
        avg_sentence_chars=120.0,
        avg_paragraph_chars=400.0,
        heading_count=4,
        is_small_document=small,
        warnings=[],
        preview="preview",
    )


def test_minmax_does_not_let_milliseconds_dominate():
    metrics = {
        "fixed": _metrics(strategy="fixed", label="Fixed-size", avg_top1=0.40, processing_ms=5, efficiency=0.9),
        "recursive": _metrics(
            strategy="recursive",
            label="Recursive",
            avg_top1=0.20,
            processing_ms=5000,
            efficiency=0.1,
        ),
        "sentence": _metrics(strategy="sentence", label="Sentence-based", avg_top1=0.21, efficiency=0.2),
        "token": _metrics(strategy="token", label="Token-based", avg_top1=0.19, efficiency=0.2),
    }
    scores = score_strategies(metrics)
    ranking = ranked_strategies(scores)
    assert ranking[0].strategy == "fixed"
    assert scores["fixed"].factors["top1_similarity"].normalized == 1.0
    assert scores["recursive"].factors["top1_similarity"].normalized == pytest.approx(
        (0.20 - 0.19) / (0.40 - 0.19), abs=1e-3
    )


def test_tied_factor_uses_raw_instead_of_half():
    metrics = {
        name: _metrics(strategy=name, label=name, avg_top1=0.33)
        for name in ("fixed", "recursive", "sentence", "token")
    }
    scores = score_strategies(metrics)
    for item in scores.values():
        assert item.factors["top1_similarity"].normalized == pytest.approx(0.33)


def test_confidence_is_not_the_winning_score():
    metrics = {
        "fixed": _metrics(
            strategy="fixed",
            label="Fixed-size",
            avg_top1=0.301,
            avg_top3=0.250,
            avg_best=0.310,
            consistency=0.70,
            size_suitability=0.70,
            efficiency=0.60,
        ),
        "recursive": _metrics(
            strategy="recursive",
            label="Recursive",
            avg_top1=0.300,
            avg_top3=0.249,
            avg_best=0.309,
            consistency=0.699,
            size_suitability=0.699,
            efficiency=0.599,
        ),
        "sentence": _metrics(
            strategy="sentence",
            label="Sentence-based",
            avg_top1=0.10,
            avg_top3=0.09,
            avg_best=0.11,
            consistency=0.2,
            size_suitability=0.2,
            efficiency=0.2,
        ),
        "token": _metrics(
            strategy="token",
            label="Token-based",
            avg_top1=0.09,
            avg_top3=0.08,
            avg_best=0.10,
            consistency=0.2,
            size_suitability=0.2,
            efficiency=0.2,
        ),
    }
    scores = score_strategies(metrics)
    winner = ranked_strategies(scores)[0]
    confidence = assess_confidence(scores, _document(chars=400, sentences=4, small=True), query_count=3)
    assert confidence.percentage != pytest.approx(winner.total * 100, abs=0.5)
    assert confidence.percentage <= 72.0
    assert any(factor.code == "narrow_margin" for factor in confidence.factors)


def test_high_margin_on_long_doc_is_more_confident():
    metrics = {
        "recursive": _metrics(
            strategy="recursive",
            label="Recursive",
            avg_top1=0.45,
            avg_top3=0.40,
            avg_best=0.48,
            size_suitability=0.95,
            consistency=0.9,
            efficiency=0.8,
            gold_hit_rate=0.9,
        ),
        "fixed": _metrics(strategy="fixed", label="Fixed-size", avg_top1=0.20, consistency=0.4),
        "sentence": _metrics(strategy="sentence", label="Sentence-based", avg_top1=0.18),
        "token": _metrics(strategy="token", label="Token-based", avg_top1=0.16),
    }
    scores = score_strategies(metrics)
    confidence = assess_confidence(scores, _document(), query_count=8)
    assert confidence.percentage >= 70
    assert confidence.level in {"moderate", "high"}


def test_chunkers_handle_small_and_normal_text():
    tiny = run_all_chunkers("Too short.")
    assert all(result.chunk_count <= 1 for result in tiny.values())
    text = SAMPLE.read_text(encoding="utf-8")
    results = run_all_chunkers(text)
    assert set(results) == set(settings.strategy_order)
    for result in results.values():
        assert result.chunk_count >= 1
        assert result.empty_chunk_count == 0


def test_analyze_rejects_empty_and_tiny_files(tmp_path: Path):
    empty = tmp_path / "deadbeefdeadbeef.txt"
    empty.write_text("   \n", encoding="utf-8")
    with pytest.raises(EmptyDocumentError):
        analyze_file("deadbeefdeadbeef", tmp_path)

    tiny = tmp_path / "cafebabecafebabe.txt"
    tiny.write_text("Hello world. " * 2, encoding="utf-8")
    with pytest.raises(DocumentTooSmallError):
        analyze_file("cafebabecafebabe", tmp_path)


def test_pipeline_on_sample(tmp_path: Path):
    file_id = "a" * 16
    target = tmp_path / f"{file_id}.txt"
    target.write_text(SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    result = analyze_file(file_id, tmp_path)
    rec = result.recommendation
    assert rec.recommended_strategy in settings.strategy_order
    assert 0 <= rec.confidence.percentage <= 100
    assert len(rec.ranking) == 4
    assert rec.reasons
    assert "Good retrieval quality" not in " ".join(rec.reasons)
    assert any("Top-1" in reason for reason in rec.reasons)
    assert rec.evidence
    assert rec.uncertainty
