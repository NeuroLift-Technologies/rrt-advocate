"""
CDE Layer 3: Behavioral Pattern Analysis
Local-first — pure Python, no external dependencies.

Tracks response latency, message complexity, and looping patterns
across a session to detect behavioral indicators of distress that
may not be visible in the text content alone.

Privacy note: Only message metadata (timing, length, word overlap) is
stored — never message content in the behavioral record.
"""

import hashlib
import hmac
import logging
import os
import re
import secrets
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

_TOKEN_HASH_KEY = (
    os.environ["RRT_BEHAVIORAL_TOKEN_KEY"].encode("utf-8")
    if os.environ.get("RRT_BEHAVIORAL_TOKEN_KEY")
    else secrets.token_bytes(32)
)


def _hash_token(word: str) -> str:
    """Return a non-reversible token for a normalized word.

    Hashing keeps set-overlap (Jaccard) behaviour identical to using the raw
    words while ensuring no plaintext message content is retained in memory or
    serialized records.
    """
    return hmac.new(_TOKEN_HASH_KEY, word.encode("utf-8"), hashlib.sha256).hexdigest()


@dataclass
class MessageRecord:
    """Metadata record for a single user message. No content stored."""
    timestamp: float        # Unix timestamp (time.time())
    word_count: int
    char_count: int
    sentence_count: int
    punctuation_density: float  # Punctuation chars / total chars
    word_set: frozenset         # For looping detection (Jaccard similarity)


@dataclass
class BehavioralAnalysisResult:
    """Result of Layer 3 behavioral pattern analysis."""
    response_latency: Optional[float]   # Seconds since last message (None if first)
    latency_anomaly: bool               # True if latency is anomalously high
    message_complexity: float           # Normalized complexity score (0.0–1.0)
    complexity_trend: str               # "normal" | "simplifying" | "fragmenting"
    looping_detected: bool              # True if recent messages are suspiciously similar
    looping_similarity: float           # Jaccard similarity to recent messages
    confidence_score: float             # Layer 3 contribution to overall crisis confidence
    metrics: Dict[str, Any] = field(default_factory=dict)


class BehavioralLayer:
    """
    CDE Layer 3: Behavioral Pattern Analysis.

    Tracks three behavioral signals:
    1. Response latency — very long gaps may indicate withdrawal/shutdown.
    2. Message complexity — very short/fragmented messages signal distress.
    3. Looping — repeated similar messages signal fixation or shutdown.
    """

    # Latency anomaly threshold: >5 minutes between messages is flagged
    _LATENCY_ANOMALY_THRESHOLD_SECONDS = 300

    # Complexity thresholds (word count per message)
    _VERY_SHORT_MESSAGE_WORDS = 5
    _NORMAL_MESSAGE_WORDS = 20

    # Looping detection: Jaccard similarity above this threshold = looping
    _LOOPING_SIMILARITY_THRESHOLD = 0.55

    def __init__(self, window_size: int = 5):
        """
        Args:
            window_size: Number of recent messages to analyze for trends.
        """
        self.window_size = window_size
        self._records: deque = deque(maxlen=window_size)
        self._last_message_time: Optional[float] = None

    def record_message(self, text: str) -> MessageRecord:
        """
        Parse a message and record its behavioral metadata.

        Args:
            text: The user message text.

        Returns:
            The created MessageRecord.
        """
        now = time.time()
        words = text.split() if text else []
        normalized_words = (w.lower().strip(".,!?;:") for w in words)
        word_set = frozenset(
            _hash_token(word) for word in normalized_words if len(word) > 2
        )
        sentences = re.split(r"[.!?]+", text)
        sentence_count = max(1, len([s for s in sentences if s.strip()]))
        punct_count = sum(1 for c in text if c in ".,!?;:()[]{}\"'")
        punct_density = punct_count / max(len(text), 1)

        record = MessageRecord(
            timestamp=now,
            word_count=len(words),
            char_count=len(text),
            sentence_count=sentence_count,
            punctuation_density=punct_density,
            word_set=word_set,
        )
        self._records.append(record)
        self._last_message_time = now
        return record

    def analyze(self, text: str) -> BehavioralAnalysisResult:
        """
        Analyze the behavioral signals of a new message.

        Records the message metadata, then computes latency, complexity,
        and looping signals.

        Args:
            text: The user message text.

        Returns:
            BehavioralAnalysisResult with all three signal analyses.
        """
        if not text or not text.strip():
            return BehavioralAnalysisResult(
                response_latency=None,
                latency_anomaly=False,
                message_complexity=0.0,
                complexity_trend="normal",
                looping_detected=False,
                looping_similarity=0.0,
                confidence_score=0.0,
                metrics={"word_count": 0, "char_count": 0, "sentence_count": 0, "punctuation_density": 0.0},
            )

        prev_time = self._last_message_time
        record = self.record_message(text)

        latency = None
        latency_anomaly = False
        if prev_time is not None:
            latency = record.timestamp - prev_time
            latency_anomaly = latency > self._LATENCY_ANOMALY_THRESHOLD_SECONDS

        complexity = self._compute_complexity(record)
        complexity_trend = self._compute_complexity_trend()
        looping_similarity = self._compute_looping_similarity(record)
        looping_detected = looping_similarity >= self._LOOPING_SIMILARITY_THRESHOLD

        confidence = self._compute_confidence(
            latency_anomaly, complexity, complexity_trend, looping_detected
        )

        result = BehavioralAnalysisResult(
            response_latency=latency,
            latency_anomaly=latency_anomaly,
            message_complexity=complexity,
            complexity_trend=complexity_trend,
            looping_detected=looping_detected,
            looping_similarity=looping_similarity,
            confidence_score=confidence,
            metrics={
                "word_count": record.word_count,
                "char_count": record.char_count,
                "sentence_count": record.sentence_count,
                "punctuation_density": record.punctuation_density,
            },
        )

        logger.debug(
            "Behavioral: latency=%.1fs, complexity=%.2f, trend=%s, looping=%s (sim=%.2f)",
            latency or 0,
            complexity,
            complexity_trend,
            looping_detected,
            looping_similarity,
        )

        return result

    def _compute_complexity(self, record: MessageRecord) -> float:
        """
        Compute a normalized complexity score.

        Very short or fragmented messages score low (0.0 = very simple/distressed).
        Normally complex messages score high (1.0 = rich, engaged).
        """
        # Word count component (0 → 0.0, 30+ → 1.0)
        word_score = min(record.word_count / 30.0, 1.0)
        # Sentence length component
        avg_words_per_sentence = record.word_count / record.sentence_count
        sentence_score = min(avg_words_per_sentence / 15.0, 1.0)
        return round((word_score * 0.6 + sentence_score * 0.4), 3)

    def _compute_complexity_trend(self) -> str:
        """Classify the trend in message complexity over the window."""
        records = list(self._records)
        if len(records) < 3:
            return "normal"

        complexities = [self._compute_complexity(r) for r in records]
        recent = complexities[-3:]
        delta = recent[-1] - recent[0]

        if delta < -0.3:
            return "fragmenting"  # Messages are becoming very short/simple
        elif delta < -0.15:
            return "simplifying"
        else:
            return "normal"

    def _compute_looping_similarity(self, current: MessageRecord) -> float:
        """
        Compute Jaccard similarity between the current message and recent history.

        Jaccard similarity = |A ∩ B| / |A ∪ B|

        High similarity (>0.55) across 3+ consecutive messages indicates looping.
        """
        records = list(self._records)
        if len(records) < 2:
            return 0.0

        # Compare current with previous message(s)
        prev_records = records[:-1]  # All records except the one just added
        if not prev_records:
            return 0.0

        similarities = []
        current_words = current.word_set
        if not current_words:
            return 0.0

        for prev in prev_records[-3:]:  # Look at up to 3 prior messages
            prev_words = prev.word_set
            if not prev_words:
                continue
            intersection = len(current_words & prev_words)
            union = len(current_words | prev_words)
            if union > 0:
                similarities.append(intersection / union)

        return round(max(similarities) if similarities else 0.0, 3)

    def _compute_confidence(
        self,
        latency_anomaly: bool,
        complexity: float,
        complexity_trend: str,
        looping_detected: bool,
    ) -> float:
        """Compute Layer 3 contribution to overall crisis confidence."""
        confidence = 0.0

        if latency_anomaly:
            confidence += 0.10

        # Very low complexity = possible shutdown
        if complexity < 0.10:
            confidence += 0.20
        elif complexity < 0.20:
            confidence += 0.10

        if complexity_trend == "fragmenting":
            confidence += 0.15
        elif complexity_trend == "simplifying":
            confidence += 0.05

        if looping_detected:
            confidence += 0.20

        return min(1.0, confidence)

    def reset(self):
        """Reset all behavioral tracking (new session)."""
        self._records.clear()
        self._last_message_time = None
