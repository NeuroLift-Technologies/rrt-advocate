"""
Crisis Assessor
Maps CrisisIndicators to a CrisisAssessment using the threshold configuration.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

import yaml

from crisis.detectors.crisis_detector import CrisisIndicators

logger = logging.getLogger(__name__)

# Avoid circular import by importing rrt_advocate types inline
# These enums are redefined here to break the circular dependency
from enum import Enum


class CrisisLevel(Enum):
    GREEN = "stable"
    YELLOW = "elevated"
    ORANGE = "high"
    RED = "critical"
    BLACK = "emergency"


class CrisisAssessor:
    """
    Maps CrisisIndicators from the 3-layer CDE to a specific CrisisLevel.

    Uses the thresholds from crisis_thresholds.yaml and applies contextual
    modifiers (time of day, behavioral signals) to produce a final assessment.
    """

    # Aggregate confidence → crisis level thresholds
    _LEVEL_THRESHOLDS = [
        (0.0, 0.20, CrisisLevel.GREEN),
        (0.20, 0.40, CrisisLevel.YELLOW),
        (0.40, 0.70, CrisisLevel.ORANGE),
        (0.70, 0.90, CrisisLevel.RED),
        (0.90, 1.01, CrisisLevel.BLACK),
    ]

    def __init__(
        self,
        user_id: str,
        config_path: str = "config/crisis_thresholds.yaml",
    ):
        self.user_id = user_id
        self.config = self._load_config(config_path)

    def _load_config(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        logger.warning("crisis_thresholds.yaml not found at %s", path)
        return {}

    async def assess_crisis(self, indicators: CrisisIndicators) -> "CrisisAssessment":
        """
        Produce a CrisisAssessment from CrisisIndicators.

        Args:
            indicators: Aggregated CDE output.

        Returns:
            CrisisAssessment with crisis level, safety score, and recommendations.
        """
        # Import here to avoid circular dependency
        from rrt_advocate import CrisisAssessment

        confidence = indicators.aggregate_confidence
        level = self._map_confidence_to_level(confidence)

        # Self-harm always escalates to BLACK
        if indicators.self_harm_risk:
            level = CrisisLevel.BLACK

        safety_score = self._compute_safety_score(indicators, level)
        interventions = self._get_recommended_interventions(level)
        primary = indicators.get_primary_indicators()

        assessment = CrisisAssessment(
            timestamp=indicators.timestamp,
            crisis_level=level,
            primary_indicators=primary,
            secondary_indicators=indicators.detected_semantic_fields,
            confidence_score=confidence,
            estimated_duration=None,
            recommended_interventions=interventions,
            escalation_threshold=self._get_escalation_threshold(level),
            user_safety_score=safety_score,
            context_factors={
                "self_harm_risk": indicators.self_harm_risk,
                "sentiment_trend": indicators.sentiment_trend,
                "looping_detected": indicators.looping_detected,
                "behavioral_complexity": indicators.behavioral_complexity,
                "layer_scores": {
                    "keyword": indicators.layer1_confidence,
                    "sentiment": indicators.layer2_confidence,
                    "behavioral": indicators.layer3_confidence,
                },
            },
        )

        logger.info(
            "CrisisAssessor: user=%s level=%s confidence=%.2f safety=%.2f",
            self.user_id,
            level.value,
            confidence,
            safety_score,
        )

        return assessment

    def _map_confidence_to_level(self, confidence: float) -> CrisisLevel:
        for low, high, level in self._LEVEL_THRESHOLDS:
            if low <= confidence < high:
                return level
        return CrisisLevel.BLACK

    def _compute_safety_score(
        self, indicators: CrisisIndicators, level: CrisisLevel
    ) -> float:
        """
        Compute a user safety score (1.0 = fully safe, 0.0 = immediate danger).

        Inversely related to the aggregate confidence, with extra penalties
        for self-harm risk and behavioral shutdown signals.
        """
        if indicators.self_harm_risk:
            return 0.05

        base = 1.0 - indicators.aggregate_confidence

        if indicators.looping_detected:
            base -= 0.10
        if indicators.behavioral_complexity < 0.10:
            base -= 0.15  # Shutdown signal
        if indicators.sentiment_trend == "sharply_declining":
            base -= 0.10

        return max(0.05, min(1.0, base))

    def _get_recommended_interventions(self, level: CrisisLevel) -> list:
        mapping = self.config.get("intervention_mapping", {})
        level_key = level.name.lower()
        if level_key in mapping:
            return mapping[level_key].get("recommended_interventions", [])
        defaults = {
            CrisisLevel.GREEN: [],
            CrisisLevel.YELLOW: ["breathing_exercise", "grounding_technique"],
            CrisisLevel.ORANGE: ["guided_meditation", "cognitive_restructuring"],
            CrisisLevel.RED: ["intensive_grounding", "crisis_counseling"],
            CrisisLevel.BLACK: ["emergency_stabilization", "crisis_hotline"],
        }
        return defaults.get(level, [])

    def _get_escalation_threshold(self, level: CrisisLevel) -> float:
        thresholds = {
            CrisisLevel.GREEN: 0.4,
            CrisisLevel.YELLOW: 0.6,
            CrisisLevel.ORANGE: 0.75,
            CrisisLevel.RED: 0.90,
            CrisisLevel.BLACK: 1.0,
        }
        return thresholds.get(level, 0.8)
