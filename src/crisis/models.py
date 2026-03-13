"""Crisis data models used across the three detection layers."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CrisisLevel(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"
    BLACK = "black"

    @property
    def numeric(self) -> int:
        return {"green": 0, "yellow": 1, "orange": 2, "red": 3, "black": 4}[self.value]

    def __lt__(self, other: "CrisisLevel") -> bool:
        return self.numeric < other.numeric

    def __gt__(self, other: "CrisisLevel") -> bool:
        return self.numeric > other.numeric

    def __le__(self, other: "CrisisLevel") -> bool:
        return self.numeric <= other.numeric

    def __ge__(self, other: "CrisisLevel") -> bool:
        return self.numeric >= other.numeric


@dataclass
class CrisisSignal:
    """A single detected signal from one of the three CDE layers."""

    source_layer: int
    """1 = keyword/semantic, 2 = sentiment/tone, 3 = behavioural."""

    signal_type: str
    """E.g. 'negative_self_talk', 'polarity_drop', 'response_latency_spike'."""

    score: float
    """0.0–1.0 severity of this individual signal."""

    evidence: str = ""
    """Human-readable excerpt or description that triggered this signal."""

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectionResult:
    """Aggregated output of the full 3-layer CDE pipeline."""

    crisis_level: CrisisLevel
    composite_score: float
    """Weighted combination of all three layer scores (0.0–1.0)."""

    layer1_score: float = 0.0
    layer2_score: float = 0.0
    layer3_score: float = 0.0

    signals: list[CrisisSignal] = field(default_factory=list)
    dominant_distress_type: str = "unknown"
    confidence: float = 0.0
    recommended_personas: list[str] = field(default_factory=list)
    escalation_required: bool = False

    def top_signals(self, n: int = 5) -> list[CrisisSignal]:
        return sorted(self.signals, key=lambda s: s.score, reverse=True)[:n]
