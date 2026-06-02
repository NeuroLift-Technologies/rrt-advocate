"""
Crisis Detector — 3-Layer Unified Pipeline
RRT AIdvocAIte — Protective Layer of the Solidarity Framework

Orchestrates all three CDE layers and aggregates their outputs into a
unified CrisisIndicators object for the CrisisAssessor.

Local-first design: all three layers run on-device.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

from .keyword_layer import KeywordLayer, KeywordAnalysisResult, KeywordSemanticField
from .sentiment_layer import SentimentLayer, SentimentAnalysisResult
from .behavioral_layer import BehavioralLayer, BehavioralAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class CrisisIndicators:
    """
    Aggregated output from all three CDE layers.

    Passed to the CrisisAssessor for final crisis level determination.
    """
    timestamp: datetime
    raw_text: str

    # Layer outputs
    keyword_result: Optional[KeywordAnalysisResult] = None
    sentiment_result: Optional[SentimentAnalysisResult] = None
    behavioral_result: Optional[BehavioralAnalysisResult] = None

    # Aggregated signals
    self_harm_risk: bool = False
    detected_semantic_fields: List[str] = field(default_factory=list)
    sentiment_trend: str = "stable"
    looping_detected: bool = False
    behavioral_complexity: float = 1.0

    # Aggregated confidence (weighted average of all layers)
    layer1_confidence: float = 0.0
    layer2_confidence: float = 0.0
    layer3_confidence: float = 0.0
    aggregate_confidence: float = 0.0

    # Layer weights for aggregation
    _LAYER_WEIGHTS: Dict[str, float] = field(
        default_factory=lambda: {"layer1": 0.45, "layer2": 0.35, "layer3": 0.20}
    )

    def compute_aggregate(self):
        """Recompute aggregate_confidence from layer scores and weights."""
        if self.self_harm_risk:
            self.aggregate_confidence = 1.0
            return
        weights = self._LAYER_WEIGHTS
        self.aggregate_confidence = min(
            1.0,
            (
                self.layer1_confidence * weights["layer1"]
                + self.layer2_confidence * weights["layer2"]
                + self.layer3_confidence * weights["layer3"]
            ),
        )

    def get_primary_indicators(self) -> List[str]:
        """Return a human-readable list of the primary detected indicators."""
        indicators = []
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
    """
    Crisis Detector — 3-Layer Local-First Pipeline.

    Accepts user message text and returns CrisisIndicators aggregated
    across all three analytical layers.

    Layer 1 (keyword) weight: 0.45
    Layer 2 (sentiment) weight: 0.35
    Layer 3 (behavioral) weight: 0.20
    """

    def __init__(self, config_path: str = "config/crisis_thresholds.yaml"):
        """Initialize the 3-layer detector.

        Args:
            config_path: Retained for interface symmetry with the assessor and
                advocate. The detector itself is **config-free** — the YAML
                thresholds are consumed by the CrisisAssessor, not here — so
                this value does not affect detection behavior.
        """
        self.config_path = config_path
        self._keyword_layer = KeywordLayer()
        self._sentiment_layer = SentimentLayer(window_size=5)
        self._behavioral_layer = BehavioralLayer(window_size=5)
        logger.info("CrisisDetector initialized (local-first, 3-layer pipeline)")

    async def detect_crisis_indicators(
        self, message: str = "", timestamp: Optional[datetime] = None
    ) -> CrisisIndicators:
        """
        Run the full 3-layer analysis on a user message.

        Args:
            message: User message text.
            timestamp: Message timestamp (defaults to now).

        Returns:
            CrisisIndicators aggregated from all layers.
        """
        ts = timestamp or datetime.now()

        # Run all three layers (synchronous but wrapped for async interface)
        keyword_result = self._keyword_layer.analyze(message)
        sentiment_result = self._sentiment_layer.analyze(message)
        behavioral_result = self._behavioral_layer.analyze(message)

        indicators = CrisisIndicators(
            timestamp=ts,
            raw_text=message,
            keyword_result=keyword_result,
            sentiment_result=sentiment_result,
            behavioral_result=behavioral_result,
            self_harm_risk=keyword_result.self_harm_detected,
            detected_semantic_fields=[
                f.value for f in keyword_result.detected_fields
            ],
            sentiment_trend=sentiment_result.trend,
            looping_detected=behavioral_result.looping_detected,
            behavioral_complexity=behavioral_result.message_complexity,
            layer1_confidence=keyword_result.confidence_score,
            layer2_confidence=sentiment_result.confidence_score,
            layer3_confidence=behavioral_result.confidence_score,
        )

        indicators.compute_aggregate()

        if indicators.self_harm_risk:
            logger.critical(
                "SELF_HARM_RISK detected — immediate escalation required (session=%s)",
                ts.isoformat(),
            )

        logger.info(
            "CDE analysis: L1=%.2f L2=%.2f L3=%.2f → aggregate=%.2f fields=%s",
            indicators.layer1_confidence,
            indicators.layer2_confidence,
            indicators.layer3_confidence,
            indicators.aggregate_confidence,
            indicators.detected_semantic_fields,
        )

        return indicators

    def reset_session(self):
        """Reset all layer state for a new session."""
        self._sentiment_layer.reset_window()
        self._behavioral_layer.reset()
        logger.info("CrisisDetector session reset")
