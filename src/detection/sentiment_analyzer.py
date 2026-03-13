"""
Layer 2 — Sentiment & Emotional Tone Analysis.

Local-first polarity tracking.  Uses a lightweight lexicon-based
approach (no external API) to detect polarity drops, emotional
volatility, and tonal shifts across a sliding window of messages.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional

POSITIVE_WORDS = frozenset({
    "good", "great", "okay", "fine", "happy", "better", "thanks",
    "love", "hope", "calm", "peaceful", "grateful", "safe",
    "proud", "strong", "relief", "comfortable", "wonderful",
    "amazing", "positive", "bright", "kind", "warm",
})

NEGATIVE_WORDS = frozenset({
    "bad", "terrible", "awful", "horrible", "hate", "angry",
    "sad", "hopeless", "scared", "anxious", "worried", "hurt",
    "pain", "broken", "worthless", "guilty", "ashamed", "afraid",
    "miserable", "desperate", "exhausted", "overwhelmed", "lost",
    "alone", "trapped", "stuck", "useless", "stupid", "failed",
    "failing", "dying", "numb", "empty", "dark", "drained",
})

INTENSIFIERS = frozenset({
    "very", "extremely", "incredibly", "so", "really", "absolutely",
    "completely", "totally", "utterly",
})

NEGATORS = frozenset({
    "not", "no", "never", "neither", "nor", "don't", "doesn't",
    "didn't", "can't", "couldn't", "won't", "wouldn't", "isn't",
    "aren't", "wasn't", "weren't",
})


@dataclass
class SentimentResult:
    """Output of Layer 2 analysis for a single message."""
    polarity: float
    magnitude: float
    polarity_drop: float
    emotional_volatility: float
    dominant_emotion: str
    window_trend: str


class SentimentAnalyzer:
    """
    Layer 2 of the CDE.  Maintains a sliding window of polarity scores
    to detect trends and drops.
    """

    def __init__(self, window_size: int = 10) -> None:
        self.window_size = window_size
        self._history: deque[float] = deque(maxlen=window_size)

    def analyse(self, text: str) -> SentimentResult:
        tokens = text.lower().split()

        pos_count = 0
        neg_count = 0
        intensity = 1.0
        negate_next = False

        for token in tokens:
            clean = token.strip(".,!?;:'\"()[]")
            if clean in INTENSIFIERS:
                intensity = 1.5
                continue
            if clean in NEGATORS:
                negate_next = True
                continue

            is_pos = clean in POSITIVE_WORDS
            is_neg = clean in NEGATIVE_WORDS

            if negate_next:
                is_pos, is_neg = is_neg, is_pos
                negate_next = False

            if is_pos:
                pos_count += intensity
            if is_neg:
                neg_count += intensity
            intensity = 1.0

        total = pos_count + neg_count
        if total == 0:
            polarity = 0.0
            magnitude = 0.0
        else:
            polarity = round((pos_count - neg_count) / total, 4)
            magnitude = round(total / max(len(tokens), 1), 4)

        self._history.append(polarity)

        polarity_drop = self._compute_polarity_drop()
        volatility = self._compute_volatility()
        trend = self._compute_trend()
        dominant = self._dominant_emotion(polarity, magnitude)

        return SentimentResult(
            polarity=polarity,
            magnitude=magnitude,
            polarity_drop=round(polarity_drop, 4),
            emotional_volatility=round(volatility, 4),
            dominant_emotion=dominant,
            window_trend=trend,
        )

    def reset(self) -> None:
        self._history.clear()

    def _compute_polarity_drop(self) -> float:
        if len(self._history) < 2:
            return 0.0
        recent = self._history[-1]
        previous_avg = sum(list(self._history)[:-1]) / (len(self._history) - 1)
        drop = previous_avg - recent
        return max(drop, 0.0)

    def _compute_volatility(self) -> float:
        if len(self._history) < 3:
            return 0.0
        values = list(self._history)
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return min(math.sqrt(variance), 1.0)

    def _compute_trend(self) -> str:
        if len(self._history) < 3:
            return "insufficient_data"
        recent_half = list(self._history)[len(self._history) // 2 :]
        older_half = list(self._history)[: len(self._history) // 2]
        recent_avg = sum(recent_half) / len(recent_half) if recent_half else 0
        older_avg = sum(older_half) / len(older_half) if older_half else 0
        diff = recent_avg - older_avg
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        return "stable"

    @staticmethod
    def _dominant_emotion(polarity: float, magnitude: float) -> str:
        if magnitude < 0.05:
            return "neutral"
        if polarity > 0.3:
            return "positive"
        if polarity < -0.3:
            return "distressed"
        return "mixed"
