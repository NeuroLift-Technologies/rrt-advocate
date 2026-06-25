"""Shared types for the RRT Advocate Crisis Detection Engine (CDE).

This is a faithful Python port of the TypeScript CDE in
``@neurolift-technologies/rrt-advocate`` (itself a port of the canonical
Python ``src/crisis/``). Field names are idiomatic snake_case; the underlying
semantics, weights, thresholds, and formulas are preserved exactly from the
TypeScript source of truth.

Local-first by design: every type here is produced by on-device analysis with
no external API calls.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class KeywordSemanticField(str, Enum):
    """Semantic fields representing distinct flavors of neurodivergent distress.

    Each field maps to a set of keyword patterns. Multiple field activations
    compound the overall crisis confidence score.
    """

    NEGATIVE_SELF_TALK = "negative_self_talk"
    TASK_AVOIDANCE = "task_avoidance"
    OVERWHELM = "overwhelm"
    MELTDOWN = "meltdown"
    SHUTDOWN = "shutdown"
    HYPERFOCUS_LOOP = "hyperfocus_loop"
    #: High-priority escalation trigger.
    SELF_HARM_RISK = "self_harm_risk"


class CrisisLevel(str, Enum):
    """Crisis severity level. Values mirror the canonical Python ``CrisisLevel``."""

    GREEN = "stable"
    YELLOW = "elevated"
    ORANGE = "high"
    RED = "critical"
    BLACK = "emergency"


#: Sentiment trend classification over the sliding window.
#: One of: ``"stable"`` | ``"declining"`` | ``"sharply_declining"`` | ``"recovering"``.
SentimentTrend = str

#: Message complexity trend classification.
#: One of: ``"normal"`` | ``"simplifying"`` | ``"fragmenting"``.
ComplexityTrend = str


@dataclass
class KeywordMatch:
    """A single keyword pattern match within a semantic field."""

    field: KeywordSemanticField
    #: The source regex pattern string that matched.
    pattern: str
    #: The exact substring that matched.
    matched_text: str
    #: Character offset of the match within the message.
    position: int


@dataclass
class KeywordAnalysisResult:
    """Result of Layer 1 keyword/semantic field analysis."""

    detected_fields: List[KeywordSemanticField]
    matches: List[KeywordMatch]
    confidence_score: float
    self_harm_detected: bool
    primary_field: Optional[KeywordSemanticField]


@dataclass
class SentimentReading:
    """A single sentiment analysis reading from one message."""

    #: Overall polarity: -1.0 (very negative) to +1.0 (very positive).
    compound: float
    positive: float
    negative: float
    neutral: float
    #: First 60 chars for debugging.
    text_snippet: str


@dataclass
class SentimentAnalysisResult:
    """Result of Layer 2 sentiment analysis for a single message."""

    current_reading: SentimentReading
    #: Drop from recent window average (negative = drop).
    polarity_drop: float
    #: Average compound over the window (prior to this message).
    window_average: float
    trend: SentimentTrend
    #: Contribution to overall crisis confidence.
    confidence_score: float
    window_readings: List[float]


@dataclass
class BehavioralMetrics:
    """Per-message behavioral metrics (mirrors the TS ``metrics`` object)."""

    word_count: int
    char_count: int
    sentence_count: int
    punctuation_density: float


@dataclass
class BehavioralAnalysisResult:
    """Result of Layer 3 behavioral pattern analysis."""

    #: Seconds since last message (None if first message in session).
    response_latency: Optional[float]
    latency_anomaly: bool
    #: Normalized complexity score (0.0-1.0).
    message_complexity: float
    complexity_trend: ComplexityTrend
    looping_detected: bool
    #: Jaccard similarity to recent messages.
    looping_similarity: float
    confidence_score: float
    metrics: BehavioralMetrics


@dataclass
class CrisisAssessment:
    """Comprehensive crisis assessment, mirroring the Python ``CrisisAssessment``."""

    timestamp: datetime
    crisis_level: CrisisLevel
    primary_indicators: List[str]
    secondary_indicators: List[str]
    confidence_score: float
    #: Estimated duration in milliseconds, or None when unknown.
    estimated_duration: Optional[float]
    recommended_interventions: List[str]
    escalation_threshold: float
    user_safety_score: float
    context_factors: Dict[str, Any] = field(default_factory=dict)
