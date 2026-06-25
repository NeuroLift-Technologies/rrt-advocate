"""Crisis Detector - 3-Layer Unified Pipeline.

Faithful Python port of ``src/crisisDetector.ts`` in
``@neurolift-technologies/rrt-advocate``. Orchestrates all three CDE layers and
aggregates their outputs into a unified :class:`CrisisIndicators` object for the
CrisisAssessor.

Local-first design: all three layers run on-device::

    Layer 1 (keyword)    weight: 0.45
    Layer 2 (sentiment)  weight: 0.35
    Layer 3 (behavioral) weight: 0.20
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from .behavioral_layer import BehavioralLayer
from .keyword_layer import KeywordLayer
from .sentiment_layer import PolarityAnalyzer, SentimentLayer, _AUTO
from .types import (
    BehavioralAnalysisResult,
    KeywordAnalysisResult,
    KeywordSemanticField,
    SentimentAnalysisResult,
    SentimentTrend,
)

_LAYER_WEIGHTS = {"layer1": 0.45, "layer2": 0.35, "layer3": 0.2}


class CrisisIndicators:
    """Aggregated output from all three CDE layers, passed to the CrisisAssessor
    for final crisis level determination."""

    def __init__(self, timestamp: datetime, raw_text: str) -> None:
        self.timestamp = timestamp
        self.raw_text = raw_text

        self.keyword_result: Optional[KeywordAnalysisResult] = None
        self.sentiment_result: Optional[SentimentAnalysisResult] = None
        self.behavioral_result: Optional[BehavioralAnalysisResult] = None

        self.self_harm_risk = False
        self.detected_semantic_fields: List[str] = []
        self.sentiment_trend: SentimentTrend = "stable"
        self.looping_detected = False
        self.behavioral_complexity = 1.0

        self.layer1_confidence = 0.0
        self.layer2_confidence = 0.0
        self.layer3_confidence = 0.0
        self.aggregate_confidence = 0.0

    def compute_aggregate(self) -> None:
        """Recompute aggregate_confidence from layer scores and weights."""
        if self.self_harm_risk:
            self.aggregate_confidence = 1.0
            return
        self.aggregate_confidence = min(
            1.0,
            self.layer1_confidence * _LAYER_WEIGHTS["layer1"]
            + self.layer2_confidence * _LAYER_WEIGHTS["layer2"]
            + self.layer3_confidence * _LAYER_WEIGHTS["layer3"],
        )

    def get_primary_indicators(self) -> List[str]:
        """Return a human-readable list of the primary detected indicators."""
        indicators: List[str] = []
        if self.self_harm_risk:
            indicators.append("SELF_HARM_RISK")
        indicators.extend(self.detected_semantic_fields)
        if self.sentiment_trend in ("declining", "sharply_declining"):
            indicators.append(f"sentiment_trend:{self.sentiment_trend}")
        if self.looping_detected:
            indicators.append("behavioral_looping")
        if self.behavioral_complexity < 0.15:
            indicators.append("behavioral_shutdown_signal")
        return indicators


class CrisisDetector:
    def __init__(self, sentiment_analyzer: object = _AUTO) -> None:
        """:param sentiment_analyzer: Optional VADER-compatible analyzer for Layer 2.
        When omitted, Layer 2 auto-detects ``vaderSentiment`` and otherwise uses its
        built-in heuristic fallback. Pass ``None`` to force the heuristic fallback.
        """
        self._keyword_layer = KeywordLayer()
        self._sentiment_layer = SentimentLayer(5, sentiment_analyzer)
        self._behavioral_layer = BehavioralLayer(5)

    def detect_crisis_indicators(
        self, message: str = "", timestamp: Optional[datetime] = None
    ) -> CrisisIndicators:
        """Run the full 3-layer analysis on a user message.

        :param message: User message text.
        :param timestamp: Message timestamp (defaults to now).
        :returns: CrisisIndicators aggregated from all layers.
        """
        ts = timestamp if timestamp is not None else datetime.now()

        keyword_result = self._keyword_layer.analyze(message)
        sentiment_result = self._sentiment_layer.analyze(message)
        behavioral_result = self._behavioral_layer.analyze(message)

        indicators = CrisisIndicators(ts, message)
        indicators.keyword_result = keyword_result
        indicators.sentiment_result = sentiment_result
        indicators.behavioral_result = behavioral_result
        indicators.self_harm_risk = keyword_result.self_harm_detected
        indicators.detected_semantic_fields = [
            f.value if isinstance(f, KeywordSemanticField) else str(f)
            for f in keyword_result.detected_fields
        ]
        indicators.sentiment_trend = sentiment_result.trend
        indicators.looping_detected = behavioral_result.looping_detected
        indicators.behavioral_complexity = behavioral_result.message_complexity
        indicators.layer1_confidence = keyword_result.confidence_score
        indicators.layer2_confidence = sentiment_result.confidence_score
        indicators.layer3_confidence = behavioral_result.confidence_score

        indicators.compute_aggregate()
        return indicators

    def reset_session(self) -> None:
        """Reset all layer state for a new session."""
        self._sentiment_layer.reset_window()
        self._behavioral_layer.reset()
