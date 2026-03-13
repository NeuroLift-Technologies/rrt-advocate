"""
Layer 2 — Sentiment & Emotional Tone Analysis.

Entirely local.  Implements a lexicon-based polarity scorer augmented with
ADHD-specific emotional intensity markers.  Tracks polarity drops across a
short message history to detect deteriorating emotional states.

No cloud calls are made.  The analyser intentionally uses a lightweight
approach (word-valence lookup + intensity modifiers) to preserve privacy
and run on-device.
"""
from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field

from .models import CrisisSignal

# ---------------------------------------------------------------------------
# Minimal valence lexicon — positive/negative word scores
# ---------------------------------------------------------------------------
_VALENCE: dict[str, float] = {
    # Positive
    "okay": 0.2, "fine": 0.2, "good": 0.4, "great": 0.6, "happy": 0.5,
    "calm": 0.4, "safe": 0.4, "better": 0.3, "hopeful": 0.5, "loved": 0.5,
    "supported": 0.4, "capable": 0.5, "strong": 0.4, "managed": 0.3,
    # Negative
    "bad": -0.3, "awful": -0.6, "terrible": -0.7, "horrible": -0.7,
    "sad": -0.4, "angry": -0.4, "scared": -0.5, "anxious": -0.5,
    "hopeless": -0.8, "worthless": -0.9, "useless": -0.7, "broken": -0.7,
    "empty": -0.6, "numb": -0.5, "stuck": -0.4, "lost": -0.4,
    "exhausted": -0.5, "drained": -0.5, "overwhelmed": -0.6, "panicking": -0.7,
    "hate": -0.6, "despair": -0.8, "desperate": -0.7, "trapped": -0.7,
}

_INTENSIFIERS: dict[str, float] = {
    "so": 1.4, "very": 1.3, "really": 1.3, "extremely": 1.6,
    "completely": 1.5, "totally": 1.5, "absolutely": 1.5, "utterly": 1.6,
}

_NEGATORS = {"not", "never", "no", "don't", "didn't", "can't", "won't", "isn't", "aren't"}

_ELLIPSIS_PATTERN = re.compile(r"\.{3,}|…")
_ALL_CAPS_PATTERN = re.compile(r"\b[A-Z]{3,}\b")


@dataclass
class _PolarityRecord:
    polarity: float
    timestamp_idx: int


@dataclass
class SentimentAnalyzer:
    """
    Stateful sentiment analyser that tracks a sliding window of message
    polarities to detect deteriorating emotional tone.
    """

    window_size: int = 5
    drop_threshold: float = 0.4
    """Polarity drop across the window that triggers a signal."""

    _history: deque[_PolarityRecord] = field(
        default_factory=lambda: deque(maxlen=5), init=False
    )
    _message_idx: int = field(default=0, init=False)

    def analyse(self, text: str) -> tuple[float, list[CrisisSignal]]:
        """
        Analyse a single message for emotional tone.

        Returns (layer_score, signals).
        """
        polarity = self._compute_polarity(text)
        self._history.append(_PolarityRecord(polarity, self._message_idx))
        self._message_idx += 1

        signals: list[CrisisSignal] = []
        scores: list[float] = []

        # 1. Raw polarity severity
        if polarity < -0.4:
            severity = min(1.0, abs(polarity))
            signals.append(
                CrisisSignal(
                    source_layer=2,
                    signal_type="negative_polarity",
                    score=severity,
                    evidence=f"polarity={polarity:.3f}",
                )
            )
            scores.append(severity)

        # 2. Polarity drop across window
        if len(self._history) >= 2:
            oldest = self._history[0].polarity
            newest = self._history[-1].polarity
            drop = oldest - newest
            if drop >= self.drop_threshold:
                drop_severity = min(1.0, drop / 1.0)
                signals.append(
                    CrisisSignal(
                        source_layer=2,
                        signal_type="polarity_drop",
                        score=drop_severity,
                        evidence=f"drop={drop:.3f} over {len(self._history)} messages",
                    )
                )
                scores.append(drop_severity)

        # 3. Emotional intensity markers in text
        caps_matches = _ALL_CAPS_PATTERN.findall(text)
        ellipsis_count = len(_ELLIPSIS_PATTERN.findall(text))

        if len(caps_matches) >= 2:
            signals.append(
                CrisisSignal(
                    source_layer=2,
                    signal_type="emotional_intensity_caps",
                    score=0.4,
                    evidence=f"caps words: {', '.join(caps_matches[:3])}",
                )
            )
            scores.append(0.4)

        if ellipsis_count >= 2:
            signals.append(
                CrisisSignal(
                    source_layer=2,
                    signal_type="fragmented_expression",
                    score=0.3,
                    evidence=f"ellipsis count: {ellipsis_count}",
                )
            )
            scores.append(0.3)

        layer_score = sum(scores) / max(1, len(scores)) if scores else 0.0
        return min(1.0, layer_score), signals

    def _compute_polarity(self, text: str) -> float:
        """Compute a simple [-1, +1] polarity score for the text."""
        tokens = re.findall(r"\b\w+\b", text.lower())
        if not tokens:
            return 0.0

        score = 0.0
        negated = False
        intensifier = 1.0

        for i, token in enumerate(tokens):
            if token in _NEGATORS:
                negated = True
                continue
            if token in _INTENSIFIERS:
                intensifier = _INTENSIFIERS[token]
                continue

            if token in _VALENCE:
                val = _VALENCE[token] * intensifier
                score += -val if negated else val

            negated = False
            intensifier = 1.0

        return max(-1.0, min(1.0, score / max(1, len(tokens)) * 3))

    def reset_history(self) -> None:
        """Clear the polarity history (e.g. at the start of a new session)."""
        self._history.clear()
        self._message_idx = 0
