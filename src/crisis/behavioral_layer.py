"""
CDE Layer 3 — Behavioural Pattern Analysis.

Tracks response latency, message complexity, and looping behaviour
across a rolling window.  All analysis is local-first.
"""

from __future__ import annotations

import re
from collections import deque
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Optional, Tuple

from src.models import CDESignal

_WINDOW_SIZE = 20


class BehavioralLayer:
    """Layer 3 of the CDE — behavioural / temporal pattern tracker."""

    def __init__(self) -> None:
        self._timestamps: Deque[datetime] = deque(maxlen=_WINDOW_SIZE)
        self._messages: Deque[str] = deque(maxlen=_WINDOW_SIZE)
        self._word_counts: Deque[int] = deque(maxlen=_WINDOW_SIZE)

    def analyse(self, text: str, timestamp: Optional[datetime] = None) -> CDESignal:
        ts = timestamp or datetime.now()
        words = text.split()
        wc = len(words)

        self._timestamps.append(ts)
        self._messages.append(text.strip().lower())
        self._word_counts.append(wc)

        indicators: List[str] = []
        scores: Dict[str, float] = {}

        latency_score = self._latency_anomaly()
        if latency_score > 0:
            scores["latency_anomaly"] = latency_score
            indicators.append("response_latency_change")

        complexity_score = self._complexity_drop()
        if complexity_score > 0:
            scores["complexity_drop"] = complexity_score
            indicators.append("message_complexity_drop")

        loop_score = self._looping_detection()
        if loop_score > 0:
            scores["looping"] = loop_score
            indicators.append("message_looping")

        overall = min(sum(scores.values()) / max(len(scores), 1), 1.0) if scores else 0.0

        return CDESignal(
            layer="behavioral",
            score=overall,
            indicators=indicators,
            metadata={"sub_scores": scores},
        )

    # ------------------------------------------------------------------
    # Sub-analyses
    # ------------------------------------------------------------------

    def _latency_anomaly(self) -> float:
        """Detect unusual gaps or sudden bursts in response timing."""
        if len(self._timestamps) < 3:
            return 0.0
        deltas = [
            (self._timestamps[i] - self._timestamps[i - 1]).total_seconds()
            for i in range(1, len(self._timestamps))
        ]
        avg = sum(deltas) / len(deltas)
        last = deltas[-1]
        if avg == 0:
            return 0.0
        ratio = abs(last - avg) / max(avg, 0.01)
        return min(ratio / 5.0, 1.0)

    def _complexity_drop(self) -> float:
        """Detect a sudden drop in message word-count."""
        if len(self._word_counts) < 3:
            return 0.0
        recent = list(self._word_counts)
        baseline = sum(recent[:-1]) / max(len(recent) - 1, 1)
        if baseline == 0:
            return 0.0
        current = recent[-1]
        drop = max(baseline - current, 0) / baseline
        return min(drop, 1.0)

    def _looping_detection(self) -> float:
        """Detect repeated/similar messages (fixation indicator)."""
        if len(self._messages) < 3:
            return 0.0
        recent = list(self._messages)
        last = recent[-1]
        duplicates = sum(1 for m in recent[:-1] if self._similarity(last, m) > 0.7)
        return min(duplicates / max(len(recent) - 1, 1), 1.0)

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        """Token-overlap Jaccard similarity."""
        sa = set(a.split())
        sb = set(b.split())
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)
