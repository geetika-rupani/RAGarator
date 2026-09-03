"""Pydantic schemas used internally and returned by the API."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    extension: str
    size_bytes: int
    message: str


class DocumentProfile(BaseModel):
    file_id: str
    filename: str
    extension: str
    char_count: int
    word_count: int
    sentence_count: int
    paragraph_count: int
    estimated_tokens: int
    avg_sentence_chars: float
    avg_paragraph_chars: float
    heading_count: int
    is_small_document: bool
    warnings: List[str] = Field(default_factory=list)
    preview: str


class ChunkRecord(BaseModel):
    index: int
    text: str
    char_count: int
    token_count: int
    sentence_count: int
    preview: str


class ChunkingResult(BaseModel):
    strategy: str
    label: str
    chunks: List[ChunkRecord]
    chunk_count: int
    avg_char_count: float
    median_char_count: float
    std_char_count: float
    min_char_count: int
    max_char_count: int
    overlap_ratio: float
    empty_chunk_count: int
    processing_ms: float


class QuerySpec(BaseModel):
    query_id: str
    query: str
    source: str
    gold_excerpt: str
    reason: str


class RetrievedChunk(BaseModel):
    rank: int
    chunk_index: int
    similarity: float
    preview: str
    text: str
    contains_gold: bool


class QueryResult(BaseModel):
    query_id: str
    query: str
    gold_excerpt: str
    top1_similarity: float
    top3_similarity: float
    best_similarity: float
    gold_hit_rank: Optional[int]
    retrieved: List[RetrievedChunk]


class RetrievalReport(BaseModel):
    strategy: str
    query_count: int
    avg_top1: float
    avg_top3: float
    avg_best: float
    gold_hit_rate: float
    mean_reciprocal_rank: float
    per_query: List[QueryResult]
    retrieval_ms: float


class StrategyMetrics(BaseModel):
    strategy: str
    label: str
    chunk_count: int
    avg_chunk_chars: float
    median_chunk_chars: float
    min_chunk_chars: int
    max_chunk_chars: int
    chunk_size_cv: float
    overlap_ratio: float
    semantic_coherence: float
    size_suitability: float
    consistency: float
    efficiency: float
    processing_ms: float
    retrieval_ms: float
    avg_top1: float
    avg_top3: float
    avg_best: float
    gold_hit_rate: float
    mean_reciprocal_rank: float
    empty_chunk_count: int
    warnings: List[str] = Field(default_factory=list)


class FactorScore(BaseModel):
    name: str
    raw: float
    normalized: float
    weight: float
    weighted: float
    interpretation: str


class StrategyScore(BaseModel):
    strategy: str
    label: str
    total: float
    factors: Dict[str, FactorScore]
    metrics: StrategyMetrics


class RankingEntry(BaseModel):
    rank: int
    strategy: str
    label: str
    score: float
    score_gap_to_leader: float
    avg_top1: float
    avg_chunk_chars: float
    chunk_count: int
    consistency: float
    efficiency: float


class UncertaintyFactor(BaseModel):
    code: str
    severity: str
    statement: str


class ConfidenceResult(BaseModel):
    percentage: float
    level: str
    margin: float
    ranking_stability: float
    evidence_quality: float
    factors: List[UncertaintyFactor]
    summary: str


class EvidenceItem(BaseModel):
    query: str
    winner_preview: str
    winner_similarity: float
    runner_up_preview: Optional[str]
    runner_up_similarity: Optional[float]
    gold_excerpt: str
    note: str


class TradeOff(BaseModel):
    title: str
    detail: str


class RecommendationResult(BaseModel):
    recommended_strategy: str
    recommended_label: str
    confidence: ConfidenceResult
    ranking: List[RankingEntry]
    scores: Dict[str, StrategyScore]
    reasons: List[str]
    uncertainty: List[UncertaintyFactor]
    trade_offs: List[TradeOff]
    evidence: List[EvidenceItem]
    caveats: List[str]


class AnalysisResponse(BaseModel):
    file_id: str
    document: DocumentProfile
    queries: List[QuerySpec]
    strategies: Dict[str, StrategyMetrics]
    recommendation: RecommendationResult
    notes: List[str] = Field(default_factory=list)
