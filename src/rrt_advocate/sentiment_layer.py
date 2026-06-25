"""CDE Layer 2: Sentiment & Emotional Tone Analysis.

Local-first - uses a VADER-compatible analyzer for on-device polarity analysis
when available, and falls back to a simple heuristic lexicon otherwise (so the
layer always runs offline, mirroring the source which makes the VADER analyzer
an optional dependency).

Faithful Python port of ``src/sentimentLayer.ts`` in
``@neurolift-technologies/rrt-advocate``. Tracks sentiment polarity over a
sliding window of messages to detect polarity drops indicative of a
deteriorating emotional state.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Protocol, runtime_checkable

from .types import SentimentAnalysisResult, SentimentReading, SentimentTrend


@runtime_checkable
class PolarityAnalyzer(Protocol):
    """Minimal interface a pluggable VADER-compatible analyzer must satisfy.

    Returns a mapping with ``compound``, ``pos``, ``neg``, and ``neu`` keys
    (the shape produced by ``vaderSentiment.SentimentIntensityAnalyzer``).
    """

    def polarity_scores(self, text: str) -> Dict[str, float]:  # pragma: no cover - protocol
        ...


POSITIVE_WORDS = frozenset(
    [
        "good", "great", "okay", "fine", "better", "calm", "happy",
        "relieved", "hopeful", "grateful", "thank", "love", "safe",
    ]
)

NEGATIVE_WORDS = frozenset(
    [
        "bad", "terrible", "awful", "horrible", "hate", "depressed",
        "anxious", "scared", "hopeless", "worthless", "useless",
        "pain", "hurt", "suffering", "stuck", "broken", "lost",
        "fail", "can't", "cannot", "never", "worst", "empty",
    ]
)

_NON_ALPHA = re.compile(r"[^a-z\s]")

# Sentinel distinguishing "auto-detect VADER" from an explicit ``None`` analyzer.
_AUTO = object()


def _try_load_vader() -> Optional[PolarityAnalyzer]:
    """Attempt to load the optional ``vaderSentiment`` package.

    Returns a VADER-compatible analyzer, or None if the package is not installed.
    Mirrors the TypeScript loader, which auto-detects the optional ``vader-sentiment``
    dependency and otherwise falls back to the built-in heuristic.
    """
    try:
        from vaderSentiment.vaderSentiment import (  # type: ignore[import-not-found]
            SentimentIntensityAnalyzer,
        )

        analyzer = SentimentIntensityAnalyzer()
        return analyzer if callable(getattr(analyzer, "polarity_scores", None)) else None
    except Exception:
        return None


class SentimentLayer:
    # Polarity drop thresholds for trend classification.
    _DECLINE_THRESHOLD = -0.15
    _SHARP_DECLINE_THRESHOLD = -0.3

    def __init__(
        self,
        window_size: int = 5,
        analyzer: object = _AUTO,
    ) -> None:
        """:param window_size: Number of recent messages to track for trend analysis.
        :param analyzer: Optional VADER-compatible analyzer. When omitted, the
            layer auto-detects ``vaderSentiment`` and otherwise uses the built-in
            heuristic fallback. Pass ``None`` to force the heuristic fallback.
        """
        self.window_size = window_size
        self._window: List[float] = []
        if analyzer is _AUTO:
            self._analyzer: Optional[PolarityAnalyzer] = _try_load_vader()
        else:
            self._analyzer = analyzer  # type: ignore[assignment]

    def analyze(self, text: str) -> SentimentAnalysisResult:
        """Analyze the sentiment of a message and update the sliding window."""
        reading = self._score_text(text)
        window_values = list(self._window)
        window_average = (
            sum(window_values) / len(window_values) if window_values else reading.compound
        )
        polarity_drop = reading.compound - window_average

        # Add current reading to the window (bounded to window_size).
        self._window.append(reading.compound)
        if len(self._window) > self.window_size:
            self._window.pop(0)

        trend = self._classify_trend(reading.compound, polarity_drop)
        confidence = self._compute_confidence(reading, trend)

        return SentimentAnalysisResult(
            current_reading=reading,
            polarity_drop=polarity_drop,
            window_average=window_average,
            trend=trend,
            confidence_score=confidence,
            window_readings=list(self._window),
        )

    def _score_text(self, text: str) -> SentimentReading:
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
        return self._fallback_score(text, snippet)

    def _fallback_score(self, text: str, snippet: str) -> SentimentReading:
        """Simple heuristic polarity scorer for when VADER is unavailable.

        Counts positive and negative indicator words for a rough compound score.
        """
        text_lower = text.lower()
        cleaned = _NON_ALPHA.sub("", text_lower)
        # ``str.split()`` matches the TS ``split(/\s+/).filter(w => w)``: split on
        # whitespace runs, dropping empties.
        words = set(cleaned.split())

        pos_count = 0
        neg_count = 0
        for w in words:
            if w in POSITIVE_WORDS:
                pos_count += 1
            if w in NEGATIVE_WORDS:
                neg_count += 1

        total = pos_count + neg_count
        compound = 0.0 if total == 0 else (pos_count - neg_count) / (total + 2)  # Damped
        compound = max(-1.0, min(1.0, compound))
        neg_ratio = neg_count / max(total, 1)

        return SentimentReading(
            compound=compound,
            positive=pos_count / max(total, 1),
            negative=neg_ratio,
            neutral=1.0 - abs(compound),
            text_snippet=snippet,
        )

    def _classify_trend(self, current: float, polarity_drop: float) -> SentimentTrend:
        # Note: the window already contains the current reading at this point,
        # matching the source ordering (append before classify).
        if len(self._window) < 2:
            return "declining" if current < -0.3 else "stable"
        if polarity_drop <= SentimentLayer._SHARP_DECLINE_THRESHOLD:
            return "sharply_declining"
        if polarity_drop <= SentimentLayer._DECLINE_THRESHOLD:
            return "declining"
        if polarity_drop >= 0.15:
            return "recovering"
        return "stable"

    def _compute_confidence(self, reading: SentimentReading, trend: SentimentTrend) -> float:
        confidence = 0.0

        # Base from current compound score (very negative = high confidence).
        if reading.compound < -0.6:
            confidence += 0.3
        elif reading.compound < -0.3:
            confidence += 0.15
        elif reading.compound < 0.0:
            confidence += 0.05

        # Bonus for sharp or sustained decline.
        if trend == "sharply_declining":
            confidence += 0.2
        elif trend == "declining":
            confidence += 0.1

        return min(1.0, confidence)

    def reset_window(self) -> None:
        """Reset the sliding window (e.g., after a session break)."""
        self._window.clear()

    def get_window_summary(self) -> Dict[str, float]:
        values = self._window
        return {
            "window_size": self.window_size,
            "readings_count": len(values),
            "average": (sum(values) / len(values)) if values else 0.0,
            "trend": (values[-1] - values[0]) if len(values) >= 2 else 0.0,
        }
