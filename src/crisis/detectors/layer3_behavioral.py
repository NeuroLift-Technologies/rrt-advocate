"""
Layer 3: Behavioral Pattern Analysis
Tracks response latency, message complexity, looping—all local.

No cloud processing. Uses sliding windows over recent interaction history.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re


@dataclass
class InteractionRecord:
    """Single interaction for behavioral analysis."""
    timestamp: datetime
    text: str
    char_count: int
    word_count: int


@dataclass
class BehavioralResult:
    """Result of behavioral pattern analysis."""
    avg_response_latency_seconds: Optional[float]
    message_complexity_trend: str  # "increasing", "decreasing", "stable"
    looping_detected: bool
    loop_similarity_threshold: float
    recent_count: int


class Layer3BehavioralAnalyzer:
    """
    Local-first behavioral pattern analyzer.
    Tracks latency, complexity trends, and message looping from recent history.
    """

    def __init__(
        self,
        window_size: int = 10,
        loop_similarity_threshold: float = 0.7,
        min_messages_for_trend: int = 3,
    ):
        self.window_size = window_size
        self.loop_similarity_threshold = loop_similarity_threshold
        self.min_messages_for_trend = min_messages_for_trend
        self._history: List[InteractionRecord] = []

    def add_interaction(self, text: str, timestamp: Optional[datetime] = None) -> None:
        """Append an interaction to the history (user message)."""
        ts = timestamp or datetime.now()
        words = len(re.findall(r"\b\w+\b", text or ""))
        self._history.append(
            InteractionRecord(
                timestamp=ts,
                text=(text or "").strip(),
                char_count=len(text or ""),
                word_count=words,
            )
        )
        # Keep only window_size most recent
        if len(self._history) > self.window_size:
            self._history = self._history[-self.window_size :]

    def _simple_similarity(self, a: str, b: str) -> float:
        """Jaccard-like similarity on word sets. 0–1."""
        if not a or not b:
            return 0.0
        wa = set(re.findall(r"\b\w+\b", a.lower()))
        wb = set(re.findall(r"\b\w+\b", b.lower()))
        if not wa and not wb:
            return 1.0
        if not wa or not wb:
            return 0.0
        inter = len(wa & wb)
        union = len(wa | wb)
        return inter / union if union > 0 else 0.0

    def analyze(
        self,
        last_message_timestamp: Optional[datetime] = None,
    ) -> BehavioralResult:
        """
        Analyze behavioral patterns from recent history.
        All computation is local.
        """
        recent = self._history[-self.window_size :]
        if not recent:
            return BehavioralResult(
                avg_response_latency_seconds=None,
                message_complexity_trend="stable",
                looping_detected=False,
                loop_similarity_threshold=self.loop_similarity_threshold,
                recent_count=0,
            )

        # Latency: time between consecutive messages
        latencies: List[float] = []
        for i in range(1, len(recent)):
            delta = (recent[i].timestamp - recent[i - 1].timestamp).total_seconds()
            latencies.append(delta)
        avg_latency = sum(latencies) / len(latencies) if latencies else None

        # Complexity trend: word count over time
        word_counts = [r.word_count for r in recent]
        trend = "stable"
        if len(word_counts) >= self.min_messages_for_trend:
            first_half = sum(word_counts[: len(word_counts) // 2]) / max(1, len(word_counts) // 2)
            second_half = sum(word_counts[len(word_counts) // 2 :]) / max(
                1, len(word_counts) - len(word_counts) // 2
            )
            if second_half > first_half * 1.2:
                trend = "increasing"
            elif second_half < first_half * 0.8:
                trend = "decreasing"

        # Looping: consecutive similar messages
        looping = False
        for i in range(len(recent) - 1):
            sim = self._simple_similarity(recent[i].text, recent[i + 1].text)
            if sim >= self.loop_similarity_threshold:
                looping = True
                break

        return BehavioralResult(
            avg_response_latency_seconds=round(avg_latency, 2) if avg_latency is not None else None,
            message_complexity_trend=trend,
            looping_detected=looping,
            loop_similarity_threshold=self.loop_similarity_threshold,
            recent_count=len(recent),
        )
