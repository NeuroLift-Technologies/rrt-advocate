"""
Layer 3 — Behavioral Pattern Analysis.

Entirely local.  Tracks three behavioural signals across a session:

  1. Response latency spikes (time between messages).
  2. Message complexity drops (proxy for cognitive load / shutdown).
  3. Looping / repetition (same themes or near-identical messages repeatedly).

No persistent storage is required; state lives in the BehavioralAnalyzer
instance for the duration of a session.
"""
from __future__ import annotations

import re
import time
from collections import deque
from dataclasses import dataclass, field

from .models import CrisisSignal


@dataclass
class _MessageRecord:
    text: str
    timestamp: float
    word_count: int
    unique_ratio: float


@dataclass
class BehavioralAnalyzer:
    """
    Stateful analyser that accumulates behavioural patterns across multiple
    messages in a session.
    """

    latency_spike_threshold: float = 120.0
    """Seconds of silence that counts as a latency spike (2 minutes)."""

    complexity_drop_threshold: float = 0.4
    """If avg word count drops below this fraction of session baseline, signal."""

    loop_window: int = 5
    """Number of recent messages to check for topic repetition."""

    loop_similarity_threshold: float = 0.6
    """Jaccard-like token overlap that flags a message as a loop repetition."""

    _history: deque[_MessageRecord] = field(
        default_factory=lambda: deque(maxlen=20), init=False
    )
    _last_timestamp: float | None = field(default=None, init=False)
    _baseline_word_count: float | None = field(default=None, init=False)

    def analyse(self, text: str, timestamp: float | None = None) -> tuple[float, list[CrisisSignal]]:
        """
        Record a new message and analyse the behavioural pattern so far.

        Parameters
        ----------
        text:
            The user's message text.
        timestamp:
            Unix timestamp of the message.  Defaults to ``time.time()``.

        Returns
        -------
        (layer_score, signals)
        """
        ts = timestamp if timestamp is not None else time.time()
        tokens = self._tokenise(text)
        word_count = len(tokens)
        unique_ratio = len(set(tokens)) / max(1, word_count)

        record = _MessageRecord(
            text=text,
            timestamp=ts,
            word_count=word_count,
            unique_ratio=unique_ratio,
        )
        self._history.append(record)

        signals: list[CrisisSignal] = []
        scores: list[float] = []

        # --- Signal 1: Response latency spike ---
        if self._last_timestamp is not None:
            latency = ts - self._last_timestamp
            if latency >= self.latency_spike_threshold:
                severity = min(1.0, latency / (self.latency_spike_threshold * 5))
                signals.append(
                    CrisisSignal(
                        source_layer=3,
                        signal_type="response_latency_spike",
                        score=severity,
                        evidence=f"latency={latency:.0f}s",
                    )
                )
                scores.append(severity)
        self._last_timestamp = ts

        # --- Signal 2: Message complexity drop ---
        if self._baseline_word_count is None and len(self._history) >= 3:
            self._baseline_word_count = sum(
                r.word_count for r in list(self._history)[:3]
            ) / 3.0

        if self._baseline_word_count and self._baseline_word_count > 0:
            ratio = word_count / self._baseline_word_count
            if ratio < self.complexity_drop_threshold and word_count < 10:
                severity = min(1.0, 1.0 - ratio)
                signals.append(
                    CrisisSignal(
                        source_layer=3,
                        signal_type="complexity_drop",
                        score=severity,
                        evidence=f"words={word_count}, baseline={self._baseline_word_count:.1f}",
                    )
                )
                scores.append(severity)

        # --- Signal 3: Looping / repetition ---
        loop_score = self._check_looping(record)
        if loop_score > 0:
            signals.append(
                CrisisSignal(
                    source_layer=3,
                    signal_type="looping_repetition",
                    score=loop_score,
                    evidence=f"repetition_score={loop_score:.2f}",
                )
            )
            scores.append(loop_score)

        layer_score = sum(scores) / max(1, len(scores)) if scores else 0.0
        return min(1.0, layer_score), signals

    def _check_looping(self, current: _MessageRecord) -> float:
        """
        Compute a looping score based on token overlap with recent messages.
        Returns 0.0 if no repetition detected, up to 1.0 for heavy looping.
        """
        if len(self._history) < 2:
            return 0.0

        current_tokens = set(self._tokenise(current.text))
        if len(current_tokens) < 3:
            return 0.0

        recent = list(self._history)[:-1][-self.loop_window:]
        overlaps: list[float] = []

        for rec in recent:
            past_tokens = set(self._tokenise(rec.text))
            if not past_tokens:
                continue
            union = current_tokens | past_tokens
            intersection = current_tokens & past_tokens
            jaccard = len(intersection) / len(union)
            overlaps.append(jaccard)

        if not overlaps:
            return 0.0

        max_overlap = max(overlaps)
        if max_overlap >= self.loop_similarity_threshold:
            return min(1.0, max_overlap)
        return 0.0

    def _tokenise(self, text: str) -> list[str]:
        """Simple whitespace + punctuation tokeniser (no external libraries)."""
        return [
            t.lower()
            for t in re.findall(r"\b\w{2,}\b", text)
            if t.lower() not in _STOPWORDS
        ]

    def reset(self) -> None:
        """Clear all session state."""
        self._history.clear()
        self._last_timestamp = None
        self._baseline_word_count = None


_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "is", "it", "i", "me", "my", "we", "you", "he",
    "she", "they", "be", "do", "did", "have", "has", "had", "are",
    "was", "were", "will", "would", "can", "could", "so", "if",
    "as", "up", "by", "with", "about", "just", "that", "this",
}
