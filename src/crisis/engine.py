"""
Crisis Detection Engine (CDE) — orchestrates the 3-layer local-first pipeline.

Pipeline:
  Layer 1  Keyword / Semantic Field Analysis
  Layer 2  Sentiment & Emotional Tone Analysis
  Layer 3  Behavioural Pattern Analysis

The aggregate score maps to a CrisisLevel via the thresholds in the YAML config.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import yaml

from src.crisis.behavioral_layer import BehavioralLayer
from src.crisis.keyword_layer import KeywordLayer
from src.crisis.sentiment_layer import SentimentLayer
from src.models import CDESignal, CrisisAssessment, CrisisLevel

logger = logging.getLogger(__name__)

_DEFAULT_THRESHOLDS = {
    CrisisLevel.GREEN: (0.0, 0.2),
    CrisisLevel.YELLOW: (0.2, 0.4),
    CrisisLevel.ORANGE: (0.4, 0.7),
    CrisisLevel.RED: (0.7, 0.9),
    CrisisLevel.BLACK: (0.9, 1.01),
}

_DEFAULT_LAYER_WEIGHTS = {
    "keyword": 0.40,
    "sentiment": 0.35,
    "behavioral": 0.25,
}


class CrisisDetectionEngine:
    """
    Local-first, 3-layer CDE.

    All processing is on-device.  No user data leaves the machine.
    """

    def __init__(self, config_path: Optional[str] = None):
        self._keyword = KeywordLayer()
        self._sentiment = SentimentLayer()
        self._behavioral = BehavioralLayer()

        self._thresholds = dict(_DEFAULT_THRESHOLDS)
        self._layer_weights = dict(_DEFAULT_LAYER_WEIGHTS)

        if config_path:
            self._load_config(config_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyse(
        self,
        text: str,
        timestamp: Optional[datetime] = None,
    ) -> CrisisAssessment:
        """
        Run the full 3-layer pipeline on a user message and return a
        CrisisAssessment.
        """
        ts = timestamp or datetime.now()

        sig_kw = self._keyword.analyse(text)
        sig_sent = self._sentiment.analyse(text)
        sig_beh = self._behavioral.analyse(text, ts)
        signals = [sig_kw, sig_sent, sig_beh]

        aggregate = self._weighted_aggregate(signals)
        level = self._map_to_level(aggregate)

        all_indicators = []
        for s in signals:
            all_indicators.extend(s.indicators)

        return CrisisAssessment(
            timestamp=ts,
            crisis_level=level,
            primary_indicators=all_indicators,
            secondary_indicators=[],
            confidence_score=round(aggregate, 3),
            estimated_duration=None,
            recommended_interventions=self._recommend(level),
            escalation_threshold=0.8,
            user_safety_score=round(1.0 - aggregate, 3),
            cde_signals=signals,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _weighted_aggregate(self, signals: List[CDESignal]) -> float:
        total = 0.0
        for sig in signals:
            w = self._layer_weights.get(sig.layer, 0.0)
            total += sig.score * w
        return min(total, 1.0)

    def _map_to_level(self, score: float) -> CrisisLevel:
        for level, (lo, hi) in self._thresholds.items():
            if lo <= score < hi:
                return level
        return CrisisLevel.BLACK if score >= 0.9 else CrisisLevel.GREEN

    @staticmethod
    def _recommend(level: CrisisLevel) -> List[str]:
        mapping = {
            CrisisLevel.GREEN: [],
            CrisisLevel.YELLOW: ["breathing_exercise", "grounding_technique"],
            CrisisLevel.ORANGE: ["guided_meditation", "cognitive_restructuring", "break_scheduling"],
            CrisisLevel.RED: ["intensive_grounding", "crisis_counseling", "safety_planning"],
            CrisisLevel.BLACK: ["emergency_stabilization", "crisis_hotline", "professional_contact"],
        }
        return mapping.get(level, [])

    def _load_config(self, path: str) -> None:
        try:
            with open(path, "r") as fh:
                data = yaml.safe_load(fh) or {}
            levels = data.get("crisis_levels", {})
            for key, spec in levels.items():
                try:
                    cl = CrisisLevel(spec.get("name", key).lower())
                except ValueError:
                    cl_map = {
                        "green": CrisisLevel.GREEN,
                        "yellow": CrisisLevel.YELLOW,
                        "orange": CrisisLevel.ORANGE,
                        "red": CrisisLevel.RED,
                        "black": CrisisLevel.BLACK,
                    }
                    cl = cl_map.get(key.lower())
                    if cl is None:
                        continue
                rng = spec.get("threshold_range", [0, 1])
                self._thresholds[cl] = (float(rng[0]), float(rng[1]))
            logger.info("CDE config loaded from %s", path)
        except Exception as exc:
            logger.warning("Could not load CDE config from %s: %s — using defaults", path, exc)
