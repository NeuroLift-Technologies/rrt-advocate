"""
CDE Layer 2: Sentiment & Emotional Tone Analysis
Local-first — uses vaderSentiment for on-device polarity analysis.

Tracks sentiment polarity over a sliding window of messages to detect
polarity drops indicative of deteriorating emotional state.
vaderSentiment is specifically tuned for social/informal text, making it
well-suited for detecting distress in casual conversation.
"""

import logging
import re
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Attempt to import vaderSentiment; fall back gracefully if not installed.
# Note: do NOT log at import time — that is a global side effect that produces
# noise in environments where the optional extra is intentionally omitted (and
# even during tooling like `pip` inspection). The fallback notice is emitted
# once, lazily, when a SentimentLayer is first instantiated without VADER.
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _VADER_AVAILABLE = True
except ImportError:
    SentimentIntensityAnalyzer = None
    _VADER_AVAILABLE = False

_fallback_notice_emitted = False


@dataclass
class SentimentReading:
    """A single sentiment analysis reading from one message."""
    compound: float    # Overall polarity: -1.0 (very negative) to +1.0 (very positive)
    positive: float
    negative: float
    neutral: float
    text_snippet: str  # First 60 chars for debugging

    def is_distressed(self) -> bool:
        return self.compound < -0.3

    def is_severely_distressed(self) -> bool:
        return self.compound < -0.6


@dataclass
class SentimentAnalysisResult:
    """Result of Layer 2 sentiment analysis for a single message."""
    current_reading: SentimentReading
    polarity_drop: float          # Drop from recent window average (negative = drop)
    window_average: float         # Average compound over the window
    trend: str                    # "stable" | "declining" | "sharply_declining" | "recovering"
    confidence_score: float       # Contribution to overall crisis confidence
    window_readings: List[float] = field(default_factory=list)

    def is_declining(self) -> bool:
        return self.trend in ("declining", "sharply_declining")


class SentimentLayer:
    """
    CDE Layer 2: Sentiment & Emotional Tone Analysis.

    Maintains a sliding window of recent sentiment readings to detect
    polarity drops and deteriorating emotional trends.

    Uses vaderSentiment if available; falls back to a simple heuristic
    lexicon if not (ensuring offline/local-first operation).
    """

    # Polarity drop thresholds for trend classification
    _DECLINE_THRESHOLD = -0.15
    _SHARP_DECLINE_THRESHOLD = -0.30

    def __init__(self, window_size: int = 5):
        """
        Args:
            window_size: Number of recent messages to track for trend analysis.
        """
        self.window_size = window_size
        self._window: deque = deque(maxlen=window_size)
        self._analyzer = SentimentIntensityAnalyzer() if _VADER_AVAILABLE else None
        if self._analyzer is None:
            global _fallback_notice_emitted
            if not _fallback_notice_emitted:
                logger.info(
                    "vaderSentiment not installed; Layer 2 using heuristic fallback. "
                    "Install the optional extra for better accuracy: pip install vaderSentiment"
                )
                _fallback_notice_emitted = True

    def analyze(self, text: str) -> SentimentAnalysisResult:
        """
        Analyze the sentiment of a message and update the sliding window.

        Args:
            text: User message text.

        Returns:
            SentimentAnalysisResult with current polarity and trend.
        """
        reading = self._score_text(text)
        window_values = list(self._window)
        window_average = (
            sum(window_values) / len(window_values) if window_values else reading.compound
        )
        polarity_drop = reading.compound - window_average

        # Add current reading to the window
        self._window.append(reading.compound)

        trend = self._classify_trend(reading.compound, window_average, polarity_drop)
        confidence = self._compute_confidence(reading, polarity_drop, trend)

        result = SentimentAnalysisResult(
            current_reading=reading,
            polarity_drop=polarity_drop,
            window_average=window_average,
            trend=trend,
            confidence_score=confidence,
            window_readings=list(self._window),
        )

        logger.debug(
            "Sentiment: compound=%.3f, drop=%.3f, trend=%s, confidence=%.3f",
            reading.compound, polarity_drop, trend, confidence,
        )

        return result

    def _score_text(self, text: str) -> SentimentReading:
        """Score text polarity using VADER or fallback heuristic."""
        snippet = text[:60] if len(text) > 60 else text

        if self._analyzer is not None:
            scores = self._analyzer.polarity_scores(text)
            return SentimentReading(
                compound=scores["compound"],
                positive=scores["pos"],
                negative=scores["neg"],
                neutral=scores["neu"],
                text_snippet=snippet,
            )
        else:
            return self._fallback_score(text, snippet)

    def _fallback_score(self, text: str, snippet: str) -> SentimentReading:
        """
        Simple heuristic polarity scorer for when VADER is unavailable.

        Counts positive and negative indicator words for a rough compound score.
        Not as accurate as VADER but maintains local-first operation.
        """
        text_lower = text.lower()
        positive_words = {
            "good", "great", "okay", "fine", "better", "calm", "happy",
            "relieved", "hopeful", "grateful", "thank", "love", "safe",
        }
        negative_words = {
            "bad", "terrible", "awful", "horrible", "hate", "depressed",
            "anxious", "scared", "hopeless", "worthless", "useless",
            "pain", "hurt", "suffering", "stuck", "broken", "lost",
            "fail", "can't", "cannot", "never", "worst", "empty",
        }
        words = set(re.sub(r"[^a-z\s]", "", text_lower).split())
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)
        total = pos_count + neg_count
        if total == 0:
            compound = 0.0
        else:
            compound = (pos_count - neg_count) / (total + 2)  # Damped
        neg_ratio = neg_count / max(total, 1)
        return SentimentReading(
            compound=max(-1.0, min(1.0, compound)),
            positive=pos_count / max(total, 1),
            negative=neg_ratio,
            neutral=1.0 - abs(compound),
            text_snippet=snippet,
        )

    def _classify_trend(
        self, current: float, window_avg: float, polarity_drop: float
    ) -> str:
        if len(self._window) < 2:
            if current < -0.3:
                return "declining"
            return "stable"

        if polarity_drop <= self._SHARP_DECLINE_THRESHOLD:
            return "sharply_declining"
        elif polarity_drop <= self._DECLINE_THRESHOLD:
            return "declining"
        elif polarity_drop >= 0.15:
            return "recovering"
        else:
            return "stable"

    def _compute_confidence(
        self, reading: SentimentReading, polarity_drop: float, trend: str
    ) -> float:
        """Compute the Layer 2 contribution to overall crisis confidence."""
        confidence = 0.0

        # Base from current compound score (very negative = high confidence)
        if reading.compound < -0.6:
            confidence += 0.30
        elif reading.compound < -0.3:
            confidence += 0.15
        elif reading.compound < 0.0:
            confidence += 0.05

        # Bonus for sharp or sustained decline
        if trend == "sharply_declining":
            confidence += 0.20
        elif trend == "declining":
            confidence += 0.10

        return min(1.0, confidence)

    def reset_window(self):
        """Reset the sliding window (e.g., after session break)."""
        self._window.clear()

    def get_window_summary(self) -> Dict[str, Any]:
        values = list(self._window)
        return {
            "window_size": self.window_size,
            "readings_count": len(values),
            "average": sum(values) / len(values) if values else 0.0,
            "trend": self._window[-1] - self._window[0] if len(values) >= 2 else 0.0,
        }
