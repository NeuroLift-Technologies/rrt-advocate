"""
Layer 3 — Behavioral Pattern Analysis.

Tracks response latency, message complexity, and conversational
looping to detect behavioral signals of crisis escalation.
All analysis is local and stateful within the session.
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class BehavioralResult:
    """Output of Layer 3 analysis."""
    latency_score: float
    complexity_score: float
    looping_score: float
    overall_score: float
    flags: List[str]


@dataclass
class _MessageRecord:
    text: str
    timestamp: float
    word_count: int
    char_count: int


class BehavioralAnalyzer:
    """
    Layer 3 of the CDE.  Maintains per-session message history and
    derives behavioral risk signals.
    """

    def __init__(self, window_size: int = 20) -> None:
        self.window_size = window_size
        self._history: deque[_MessageRecord] = deque(maxlen=window_size)
        self._baseline_latency: Optional[float] = None
        self._baseline_complexity: Optional[float] = None

    def record_message(self, text: str, timestamp: Optional[float] = None) -> BehavioralResult:
        ts = timestamp or time.time()
        words = text.split()
        record = _MessageRecord(
            text=text,
            timestamp=ts,
            word_count=len(words),
            char_count=len(text),
        )
        self._history.append(record)

        if len(self._history) >= 3 and self._baseline_latency is None:
            self._set_baselines()

        latency = self._latency_score()
        complexity = self._complexity_score()
        looping = self._looping_score()

        overall = round(
            0.30 * latency + 0.30 * complexity + 0.40 * looping, 4
        )

        flags = self._generate_flags(latency, complexity, looping)

        return BehavioralResult(
            latency_score=round(latency, 4),
            complexity_score=round(complexity, 4),
            looping_score=round(looping, 4),
            overall_score=min(overall, 1.0),
            flags=flags,
        )

    def reset(self) -> None:
        self._history.clear()
        self._baseline_latency = None
        self._baseline_complexity = None

    def _set_baselines(self) -> None:
        records = list(self._history)
        latencies = []
        for i in range(1, len(records)):
            latencies.append(records[i].timestamp - records[i - 1].timestamp)
        self._baseline_latency = sum(latencies) / len(latencies) if latencies else 5.0
        complexities = [r.word_count for r in records]
        self._baseline_complexity = sum(complexities) / len(complexities) if complexities else 10.0

    def _latency_score(self) -> float:
        """High score = abnormally slow responses (possible shutdown)."""
        if len(self._history) < 2 or self._baseline_latency is None:
            return 0.0
        last_two = list(self._history)[-2:]
        latency = last_two[1].timestamp - last_two[0].timestamp
        if self._baseline_latency <= 0:
            return 0.0
        ratio = latency / self._baseline_latency
        return min(max((ratio - 1.0) / 4.0, 0.0), 1.0)

    def _complexity_score(self) -> float:
        """
        High score = messages getting simpler over time (cognitive
        load collapse) or extremely short messages.
        """
        if len(self._history) < 3 or self._baseline_complexity is None:
            return 0.0
        recent = list(self._history)[-3:]
        avg_recent = sum(r.word_count for r in recent) / len(recent)
        if self._baseline_complexity <= 0:
            return 0.0
        ratio = avg_recent / self._baseline_complexity
        if ratio < 1.0:
            return min(1.0 - ratio, 1.0)
        return 0.0

    def _looping_score(self) -> float:
        """
        High score = repetitive phrasing across recent messages
        (cognitive loops, perseveration).
        """
        if len(self._history) < 3:
            return 0.0
        recent_texts = [r.text.lower().strip() for r in list(self._history)[-5:]]
        if len(recent_texts) < 2:
            return 0.0

        pair_similarities = []
        for i in range(len(recent_texts)):
            for j in range(i + 1, len(recent_texts)):
                pair_similarities.append(
                    self._jaccard(recent_texts[i], recent_texts[j])
                )
        avg_sim = sum(pair_similarities) / len(pair_similarities) if pair_similarities else 0.0
        return min(avg_sim * 1.5, 1.0)

    @staticmethod
    def _jaccard(a: str, b: str) -> float:
        set_a = set(a.split())
        set_b = set(b.split())
        if not set_a and not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)

    @staticmethod
    def _generate_flags(
        latency: float, complexity: float, looping: float
    ) -> List[str]:
        flags: List[str] = []
        if latency > 0.6:
            flags.append("response_delay_elevated")
        if complexity > 0.5:
            flags.append("message_complexity_dropping")
        if looping > 0.5:
            flags.append("conversational_looping_detected")
        if latency > 0.8 and complexity > 0.6:
            flags.append("possible_shutdown")
        return flags
