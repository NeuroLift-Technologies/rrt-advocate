"""
Crisis Detection Engine (CDE) — 3-layer local-first pipeline.

Orchestrates Layer 1 (keyword/semantic), Layer 2 (sentiment/tone), and
Layer 3 (behavioural) into a single composite DetectionResult.

Design principles:
  - Local-first: no network calls, no cloud telemetry.
  - Privacy-centric: nothing is persisted beyond the current session unless
    the user explicitly opts in.
  - Non-judgmental: internal variable names and log messages avoid language
    that shames or pathologises the user's experience.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from . import keyword_analyzer
from .behavioral_analyzer import BehavioralAnalyzer
from .models import CrisisLevel, CrisisSignal, DetectionResult
from .sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)

# Composite score → CrisisLevel mapping
_LEVEL_THRESHOLDS: list[tuple[float, CrisisLevel]] = [
    (0.9, CrisisLevel.BLACK),
    (0.70, CrisisLevel.RED),
    (0.45, CrisisLevel.ORANGE),
    (0.25, CrisisLevel.YELLOW),
    (0.0, CrisisLevel.GREEN),
]

# Layer weights for composite scoring
_LAYER_WEIGHTS = {
    "layer1": 0.50,
    "layer2": 0.30,
    "layer3": 0.20,
}

# Distress type → recommended personas mapping (mirrors FusionEngine)
_DISTRESS_PERSONA_MAP: dict[str, list[str]] = {
    "negative_self_talk": ["ECHO", "ASH"],
    "task_avoidance": ["SOL", "ASH"],
    "overwhelm": ["ASH", "MYRA"],
    "burnout": ["ASH", "MYRA"],
    "shutdown": ["MYRA"],
    "shame": ["ASH", "ECHO"],
    "hyperfocus_loop": ["KAI"],
    "self_harm_language": ["MYRA", "ASH"],
    "polarity_drop": ["MYRA", "ASH"],
    "looping_repetition": ["KAI", "ECHO"],
    "unknown": ["MYRA"],
}


@dataclass
class CrisisDetectionEngine:
    """
    The main CDE orchestrator.  Instantiate once per session and call
    ``analyse()`` for each incoming user message.
    """

    layer1_weight: float = 0.50
    layer2_weight: float = 0.30
    layer3_weight: float = 0.20

    _sentiment: SentimentAnalyzer = field(
        default_factory=SentimentAnalyzer, init=False
    )
    _behavioral: BehavioralAnalyzer = field(
        default_factory=BehavioralAnalyzer, init=False
    )

    def analyse(
        self,
        text: str,
        timestamp: float | None = None,
    ) -> DetectionResult:
        """
        Run all three layers and return a composite DetectionResult.

        Parameters
        ----------
        text:
            The user's message.
        timestamp:
            Unix timestamp of the message (defaults to now).
        """
        ts = timestamp or time.time()

        l1_score, l1_signals = keyword_analyzer.analyse(text)
        l2_score, l2_signals = self._sentiment.analyse(text)
        l3_score, l3_signals = self._behavioral.analyse(text, timestamp=ts)

        all_signals: list[CrisisSignal] = l1_signals + l2_signals + l3_signals

        composite = (
            self.layer1_weight * l1_score
            + self.layer2_weight * l2_score
            + self.layer3_weight * l3_score
        )
        composite = min(1.0, composite)

        # Self-harm language always elevates to at least RED regardless of composite
        if any(s.signal_type == "self_harm_language" for s in all_signals):
            composite = max(composite, 0.70)

        crisis_level = self._score_to_level(composite)

        dominant_type, recommended_personas = self._derive_distress_type(all_signals)

        confidence = self._estimate_confidence(all_signals, composite)

        escalation_required = (
            crisis_level >= CrisisLevel.RED
            or any(s.signal_type == "self_harm_language" for s in all_signals)
        )

        result = DetectionResult(
            crisis_level=crisis_level,
            composite_score=round(composite, 4),
            layer1_score=round(l1_score, 4),
            layer2_score=round(l2_score, 4),
            layer3_score=round(l3_score, 4),
            signals=all_signals,
            dominant_distress_type=dominant_type,
            confidence=round(confidence, 4),
            recommended_personas=recommended_personas,
            escalation_required=escalation_required,
        )

        logger.debug(
            "CDE result | level=%s | composite=%.3f | dominant=%s | escalation=%s",
            crisis_level.value,
            composite,
            dominant_type,
            escalation_required,
        )

        return result

    def _score_to_level(self, score: float) -> CrisisLevel:
        for threshold, level in _LEVEL_THRESHOLDS:
            if score >= threshold:
                return level
        return CrisisLevel.GREEN

    def _derive_distress_type(
        self,
        signals: list[CrisisSignal],
    ) -> tuple[str, list[str]]:
        """
        Identify the dominant distress type from the signals and return
        the recommended persona list for that type.
        """
        if not signals:
            return "unknown", ["MYRA"]

        top_signal = max(signals, key=lambda s: s.score)
        distress_type = top_signal.signal_type

        personas = _DISTRESS_PERSONA_MAP.get(distress_type, ["MYRA", "ASH"])
        return distress_type, personas

    def _estimate_confidence(
        self,
        signals: list[CrisisSignal],
        composite: float,
    ) -> float:
        """
        Estimate detection confidence based on signal count and agreement
        across layers.
        """
        if not signals:
            return 0.1

        layers_represented = len({s.source_layer for s in signals})
        layer_agreement_bonus = 0.1 * (layers_represented - 1)

        avg_signal_score = sum(s.score for s in signals) / len(signals)
        signal_count_bonus = min(0.2, 0.05 * len(signals))

        raw = (avg_signal_score * 0.7) + layer_agreement_bonus + signal_count_bonus
        return min(1.0, max(0.0, raw))

    def reset_session(self) -> None:
        """Reset all stateful analysers for a fresh session."""
        self._sentiment.reset_history()
        self._behavioral.reset()
