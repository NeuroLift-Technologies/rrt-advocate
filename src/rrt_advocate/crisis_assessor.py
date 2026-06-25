"""Crisis Assessor.

Faithful Python port of ``src/crisisAssessor.ts`` in
``@neurolift-technologies/rrt-advocate``. Maps :class:`CrisisIndicators` from
the 3-layer CDE to a specific :class:`CrisisLevel`, applying the thresholds from
``crisis_thresholds.yaml`` to produce a final :class:`CrisisAssessment`.
"""
from __future__ import annotations

import importlib.resources
import logging
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .crisis_detector import CrisisIndicators
from .types import CrisisAssessment, CrisisLevel

logger = logging.getLogger("rrt_advocate")

_CONFIG_FILENAME = "crisis_thresholds.yaml"

#: Lowercase config key for each crisis level (matches Python ``level.name.lower()``).
_LEVEL_KEY: Dict[CrisisLevel, str] = {
    CrisisLevel.GREEN: "green",
    CrisisLevel.YELLOW: "yellow",
    CrisisLevel.ORANGE: "orange",
    CrisisLevel.RED: "red",
    CrisisLevel.BLACK: "black",
}

# Aggregate confidence -> crisis level thresholds: (low, high, level).
_LEVEL_THRESHOLDS: Tuple[Tuple[float, float, CrisisLevel], ...] = (
    (0.0, 0.2, CrisisLevel.GREEN),
    (0.2, 0.4, CrisisLevel.YELLOW),
    (0.4, 0.7, CrisisLevel.ORANGE),
    (0.7, 0.9, CrisisLevel.RED),
    (0.9, 1.01, CrisisLevel.BLACK),
)

_DEFAULT_INTERVENTIONS: Dict[CrisisLevel, List[str]] = {
    CrisisLevel.GREEN: [],
    CrisisLevel.YELLOW: ["breathing_exercise", "grounding_technique"],
    CrisisLevel.ORANGE: ["guided_meditation", "cognitive_restructuring"],
    CrisisLevel.RED: ["intensive_grounding", "crisis_counseling"],
    CrisisLevel.BLACK: ["emergency_stabilization", "crisis_hotline"],
}

_ESCALATION_THRESHOLDS: Dict[CrisisLevel, float] = {
    CrisisLevel.GREEN: 0.4,
    CrisisLevel.YELLOW: 0.6,
    CrisisLevel.ORANGE: 0.75,
    CrisisLevel.RED: 0.9,
    CrisisLevel.BLACK: 1.0,
}


def _default_config_path() -> str:
    """Resolve the bundled ``crisis_thresholds.yaml`` shipped with the package."""
    ref = importlib.resources.files(__package__) / "config" / _CONFIG_FILENAME
    return str(ref)


class CrisisAssessor:
    def __init__(self, user_id: str, config_path: Optional[str] = None) -> None:
        """:param user_id: Stable, pseudonymous user identifier (used only for logging
            context; no content is persisted).
        :param config_path: Path to a ``crisis_thresholds.yaml``. Defaults to the
            copy bundled with this package.
        """
        self.user_id = user_id
        self._config = self._load_config(config_path)

    @staticmethod
    def _load_config(path: Optional[str]) -> Dict[str, Any]:
        try:
            if path is None:
                ref = importlib.resources.files(__package__) / "config" / _CONFIG_FILENAME
                raw = ref.read_text(encoding="utf-8")
            else:
                with open(path, "r", encoding="utf-8") as fh:
                    raw = fh.read()
            return yaml.safe_load(raw) or {}
        except Exception as error:
            # Safety-critical: never run silently on a missing/unreadable thresholds
            # file. Mirror the source, which logs a warning, so operators know the
            # assessor fell back to built-in default interventions.
            logger.warning(
                '[rrt-advocate] Could not load crisis thresholds from "%s"; '
                "falling back to built-in default interventions. %s",
                path if path is not None else _default_config_path(),
                error,
            )
            return {}

    def assess_crisis(self, indicators: CrisisIndicators) -> CrisisAssessment:
        """Produce a CrisisAssessment from CrisisIndicators."""
        confidence = indicators.aggregate_confidence
        level = self._map_confidence_to_level(confidence)

        # Self-harm always escalates to BLACK.
        if indicators.self_harm_risk:
            level = CrisisLevel.BLACK

        safety_score = self._compute_safety_score(indicators)
        interventions = self._get_recommended_interventions(level)
        primary = indicators.get_primary_indicators()

        return CrisisAssessment(
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

    def _map_confidence_to_level(self, confidence: float) -> CrisisLevel:
        for low, high, level in _LEVEL_THRESHOLDS:
            if low <= confidence < high:
                return level
        return CrisisLevel.BLACK

    def _compute_safety_score(self, indicators: CrisisIndicators) -> float:
        """Compute a user safety score (1.0 = fully safe, 0.0 = immediate danger).

        Inversely related to aggregate confidence, with extra penalties for
        self-harm risk and behavioral shutdown signals.
        """
        if indicators.self_harm_risk:
            return 0.05
        base = 1.0 - indicators.aggregate_confidence
        if indicators.looping_detected:
            base -= 0.1
        if indicators.behavioral_complexity < 0.1:
            base -= 0.15  # Shutdown signal
        if indicators.sentiment_trend == "sharply_declining":
            base -= 0.1
        return max(0.05, min(1.0, base))

    def _get_recommended_interventions(self, level: CrisisLevel) -> List[str]:
        mapping = self._config.get("intervention_mapping") or {}
        level_key = _LEVEL_KEY[level]
        entry = mapping.get(level_key)
        if entry:
            return entry.get("recommended_interventions") or []
        return _DEFAULT_INTERVENTIONS[level]

    def _get_escalation_threshold(self, level: CrisisLevel) -> float:
        return _ESCALATION_THRESHOLDS.get(level, 0.8)
