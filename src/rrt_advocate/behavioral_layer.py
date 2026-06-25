"""CDE Layer 3: Behavioral Pattern Analysis.

Local-first - no external dependencies. Faithful Python port of
``src/behavioralLayer.ts`` in ``@neurolift-technologies/rrt-advocate``.

Tracks response latency, message complexity, and looping patterns across a
session to detect behavioral indicators of distress that may not be visible in
the text content alone.

Privacy note: only message metadata (timing, length, hashed word tokens) is
stored - never raw message content. Word tokens are passed through an
HMAC-SHA256 so set-overlap (Jaccard) behaviour is identical to using raw words
while remaining non-reversible.
"""
from __future__ import annotations

import hashlib
import hmac
import math
import os
import re
import time
from typing import List, Optional, Set

from .types import BehavioralAnalysisResult, BehavioralMetrics, ComplexityTrend

_TOKEN_HASH_KEY: bytes = (
    os.environ["RRT_BEHAVIORAL_TOKEN_KEY"].encode("utf-8")
    if os.environ.get("RRT_BEHAVIORAL_TOKEN_KEY")
    else os.urandom(32)
)

_WHITESPACE = re.compile(r"\s+")
_SENTENCE_SPLIT = re.compile(r"[.!?]+")

#: Punctuation stripped from word edges (mirrors Python ``str.strip(".,!?;:")``).
_EDGE_PUNCTUATION = frozenset(".,!?;:")

#: Punctuation chars counted toward density.
_DENSITY_PUNCTUATION = frozenset(".,!?;:()[]{}\"'")


def _hash_token(word: str) -> str:
    return hmac.new(_TOKEN_HASH_KEY, word.encode("utf-8"), hashlib.sha256).hexdigest()


def _strip_edge_punctuation(word: str) -> str:
    """Trim leading/trailing edge punctuation from a word."""
    start = 0
    end = len(word)
    while start < end and word[start] in _EDGE_PUNCTUATION:
        start += 1
    while end > start and word[end - 1] in _EDGE_PUNCTUATION:
        end -= 1
    return word[start:end]


def _round3(value: float) -> float:
    """Round to 3 decimals, matching JS ``Math.round(value*1000)/1000``.

    JS ``Math.round`` rounds half toward +Infinity, so use ``math.floor(x + 0.5)``
    rather than Python's banker's rounding to stay bit-identical.
    """
    return math.floor(value * 1000 + 0.5) / 1000


def _jaccard(a: Set[str], b: Set[str]) -> float:
    intersection = 0
    for t in a:
        if t in b:
            intersection += 1
    union = len(a) + len(b) - intersection
    return intersection / union if union > 0 else 0.0


class _MessageRecord:
    """Metadata record for a single user message. No content stored."""

    __slots__ = (
        "timestamp",
        "word_count",
        "char_count",
        "sentence_count",
        "punctuation_density",
        "word_set",
    )

    def __init__(
        self,
        timestamp: float,
        word_count: int,
        char_count: int,
        sentence_count: int,
        punctuation_density: float,
        word_set: Set[str],
    ) -> None:
        self.timestamp = timestamp
        self.word_count = word_count
        self.char_count = char_count
        self.sentence_count = sentence_count
        self.punctuation_density = punctuation_density
        self.word_set = word_set


class BehavioralLayer:
    # Latency anomaly threshold: >5 minutes between messages is flagged.
    _LATENCY_ANOMALY_THRESHOLD_SECONDS = 300
    # Looping detection: Jaccard similarity above this threshold = looping.
    _LOOPING_SIMILARITY_THRESHOLD = 0.55

    def __init__(self, window_size: int = 5) -> None:
        """:param window_size: Number of recent messages to analyze for trends."""
        self.window_size = window_size
        self._records: List[_MessageRecord] = []
        self._last_message_time: Optional[float] = None

    def record_message(self, text: str) -> _MessageRecord:
        """Parse a message and record its behavioral metadata."""
        now = time.time()
        words = [w for w in _WHITESPACE.split(text) if len(w) > 0] if text else []
        word_set: Set[str] = set()
        for w in words:
            normalized = _strip_edge_punctuation(w.lower())
            if len(normalized) > 2:
                word_set.add(_hash_token(normalized))
        sentences = [s for s in _SENTENCE_SPLIT.split(text) if s.strip()]
        sentence_count = max(1, len(sentences))
        punct_count = sum(1 for c in text if c in _DENSITY_PUNCTUATION)
        punct_density = punct_count / max(len(text), 1)

        record = _MessageRecord(
            timestamp=now,
            word_count=len(words),
            char_count=len(text),
            sentence_count=sentence_count,
            punctuation_density=punct_density,
            word_set=word_set,
        )
        self._records.append(record)
        if len(self._records) > self.window_size:
            self._records.pop(0)
        self._last_message_time = now
        return record

    def analyze(self, text: str) -> BehavioralAnalysisResult:
        """Analyze the behavioral signals of a new message."""
        if not text or not text.strip():
            return BehavioralAnalysisResult(
                response_latency=None,
                latency_anomaly=False,
                message_complexity=0.0,
                complexity_trend="normal",
                looping_detected=False,
                looping_similarity=0.0,
                confidence_score=0.0,
                metrics=BehavioralMetrics(
                    word_count=0,
                    char_count=0,
                    sentence_count=0,
                    punctuation_density=0.0,
                ),
            )

        prev_time = self._last_message_time
        record = self.record_message(text)

        latency: Optional[float] = None
        latency_anomaly = False
        if prev_time is not None:
            latency = record.timestamp - prev_time
            latency_anomaly = latency > BehavioralLayer._LATENCY_ANOMALY_THRESHOLD_SECONDS

        complexity = self._compute_complexity(record)
        complexity_trend = self._compute_complexity_trend()
        looping_similarity = self._compute_looping_similarity(record)
        looping_detected = looping_similarity >= BehavioralLayer._LOOPING_SIMILARITY_THRESHOLD

        confidence = self._compute_confidence(
            latency_anomaly, complexity, complexity_trend, looping_detected
        )

        return BehavioralAnalysisResult(
            response_latency=latency,
            latency_anomaly=latency_anomaly,
            message_complexity=complexity,
            complexity_trend=complexity_trend,
            looping_detected=looping_detected,
            looping_similarity=looping_similarity,
            confidence_score=confidence,
            metrics=BehavioralMetrics(
                word_count=record.word_count,
                char_count=record.char_count,
                sentence_count=record.sentence_count,
                punctuation_density=record.punctuation_density,
            ),
        )

    def _compute_complexity(self, record: _MessageRecord) -> float:
        """Compute a normalized complexity score.

        Very short or fragmented messages score low (0.0 = very simple/distressed);
        richly engaged messages score high (1.0).
        """
        word_score = min(record.word_count / 30.0, 1.0)
        avg_words_per_sentence = record.word_count / record.sentence_count
        sentence_score = min(avg_words_per_sentence / 15.0, 1.0)
        return _round3(word_score * 0.6 + sentence_score * 0.4)

    def _compute_complexity_trend(self) -> ComplexityTrend:
        """Classify the trend in message complexity over the window."""
        if len(self._records) < 3:
            return "normal"
        complexities = [self._compute_complexity(r) for r in self._records]
        recent = complexities[-3:]
        delta = recent[-1] - recent[0]
        if delta < -0.3:
            return "fragmenting"
        if delta < -0.15:
            return "simplifying"
        return "normal"

    def _compute_looping_similarity(self, current: _MessageRecord) -> float:
        """Compute Jaccard similarity between the current message and recent history.

        High similarity (>0.55) across consecutive messages indicates looping.
        """
        if len(self._records) < 2:
            return 0.0
        prev_records = self._records[:-1]  # all except the one just added
        if not prev_records:
            return 0.0
        current_words = current.word_set
        if len(current_words) == 0:
            return 0.0

        similarities: List[float] = []
        for prev in prev_records[-3:]:
            if len(prev.word_set) == 0:
                continue
            similarities.append(_jaccard(current_words, prev.word_set))
        return _round3(max(similarities)) if similarities else 0.0

    def _compute_confidence(
        self,
        latency_anomaly: bool,
        complexity: float,
        complexity_trend: ComplexityTrend,
        looping_detected: bool,
    ) -> float:
        confidence = 0.0
        if latency_anomaly:
            confidence += 0.1
        if complexity < 0.1:
            confidence += 0.2
        elif complexity < 0.2:
            confidence += 0.1
        if complexity_trend == "fragmenting":
            confidence += 0.15
        elif complexity_trend == "simplifying":
            confidence += 0.05
        if looping_detected:
            confidence += 0.2
        return min(1.0, confidence)

    def reset(self) -> None:
        """Reset all behavioral tracking (new session)."""
        self._records.clear()
        self._last_message_time = None
