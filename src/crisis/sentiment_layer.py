"""
CDE Layer 2 — Sentiment & Emotional Tone Analysis.

Tracks polarity drops across a rolling window of user messages.
Implemented locally using a lightweight lexicon-based approach — no
cloud NLP services.
"""

from __future__ import annotations

import re
from collections import deque
from typing import Deque, List

from src.models import CDESignal

# ---------------------------------------------------------------------------
# Minimal sentiment lexicon (positive / negative word sets)
# ---------------------------------------------------------------------------

_POSITIVE: set[str] = {
    "good", "great", "happy", "love", "fine", "okay", "better", "hopeful",
    "calm", "safe", "proud", "strong", "grateful", "glad", "relief",
    "capable", "confident", "peaceful", "joyful", "excited", "thanks",
}

_NEGATIVE: set[str] = {
    "bad", "terrible", "awful", "hate", "hurt", "pain", "worse", "hopeless",
    "scared", "angry", "sad", "anxious", "panic", "dread", "afraid",
    "worthless", "miserable", "exhausted", "numb", "broken", "lonely",
    "ashamed", "guilty", "disgusted", "furious", "helpless", "trapped",
    "overwhelmed", "stressed", "frustrated", "crying", "sobbing",
}

_INTENSIFIERS: set[str] = {
    "very", "so", "extremely", "really", "absolutely", "completely",
    "totally", "utterly", "incredibly",
}

_NEGATORS: set[str] = {"not", "no", "never", "don't", "can't", "won't", "isn't"}

_WORD_RE = re.compile(r"[a-z']+")

_WINDOW_SIZE = 10


def _tokenise(text: str) -> List[str]:
    return _WORD_RE.findall(text.lower())


class SentimentLayer:
    """Layer 2 of the CDE — local sentiment & polarity-drop tracker."""

    def __init__(self) -> None:
        self._history: Deque[float] = deque(maxlen=_WINDOW_SIZE)

    def analyse(self, text: str) -> CDESignal:
        tokens = _tokenise(text)
        polarity = self._score_polarity(tokens)
        self._history.append(polarity)
        drop = self._detect_polarity_drop()

        distress_score = 0.0
        indicators: list[str] = []

        if polarity < -0.3:
            distress_score += min(abs(polarity), 1.0) * 0.6
            indicators.append("negative_polarity")

        if drop > 0.3:
            distress_score += min(drop, 1.0) * 0.4
            indicators.append("polarity_drop")

        distress_score = min(distress_score, 1.0)

        return CDESignal(
            layer="sentiment",
            score=distress_score,
            indicators=indicators,
            metadata={
                "polarity": round(polarity, 3),
                "drop": round(drop, 3),
                "window_size": len(self._history),
            },
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _score_polarity(tokens: List[str]) -> float:
        """Compute a simple polarity score in [-1.0, 1.0]."""
        pos = neg = 0.0
        multiplier = 1.0
        negate = False

        for tok in tokens:
            if tok in _NEGATORS:
                negate = True
                continue
            if tok in _INTENSIFIERS:
                multiplier = 1.5
                continue

            if tok in _POSITIVE:
                if negate:
                    neg += multiplier
                else:
                    pos += multiplier
            elif tok in _NEGATIVE:
                if negate:
                    pos += multiplier
                else:
                    neg += multiplier

            multiplier = 1.0
            negate = False

        total = pos + neg
        if total == 0:
            return 0.0
        return (pos - neg) / total

    def _detect_polarity_drop(self) -> float:
        """Return the magnitude of the largest recent polarity drop."""
        if len(self._history) < 2:
            return 0.0
        recent = list(self._history)
        drops: list[float] = []
        for i in range(1, len(recent)):
            delta = recent[i - 1] - recent[i]
            if delta > 0:
                drops.append(delta)
        return max(drops) if drops else 0.0
