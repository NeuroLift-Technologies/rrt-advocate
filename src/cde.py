"""
Local-first Crisis Detection Engine (CDE) with 3 analytical layers.
"""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Dict, Iterable, List

from .models import CDEAssessment, CDELayerResult


class LocalFirstCrisisDetectionEngine:
    """
    3-layer crisis detection pipeline:
      1) Keyword/semantic fields
      2) Sentiment and emotional tone shifts
      3) Behavioral patterns (latency, complexity, looping)
    """

    _lexicons: Dict[str, List[str]] = {
        "negative_self_talk": ["worthless", "broken", "failure", "hate myself", "my fault", "shame"],
        "task_avoidance": ["can't start", "cant start", "avoiding", "stuck", "frozen"],
        "overwhelm": ["overwhelmed", "too much", "everything hurts", "meltdown", "shutdown"],
    }

    _negative_words = {"bad", "awful", "hopeless", "stuck", "panic", "scared", "tired", "ashamed", "hate"}
    _positive_words = {"okay", "safe", "calm", "better", "good", "hope", "steady", "supported"}

    def __init__(self) -> None:
        self._last_polarity: float = 0.0

    def assess(
        self,
        *,
        message: str,
        recent_messages: Iterable[str] | None = None,
        response_latency_seconds: float | None = None,
    ) -> CDEAssessment:
        recent = list(recent_messages or [])
        keyword_layer = self._layer_1_keywords(message)
        sentiment_layer, polarity = self._layer_2_sentiment(message)
        behavior_layer = self._layer_3_behavior(
            message=message,
            recent_messages=recent,
            response_latency_seconds=response_latency_seconds,
        )

        combined = (
            0.42 * keyword_layer.score
            + 0.33 * sentiment_layer.score
            + 0.25 * behavior_layer.score
        )
        distress_tags = self._collect_distress_tags(
            keyword_signals=keyword_layer.signals,
            behavior_signals=behavior_layer.signals,
        )
        self._last_polarity = polarity

        return CDEAssessment(
            layer_1_keywords=keyword_layer,
            layer_2_sentiment=sentiment_layer,
            layer_3_behavior=behavior_layer,
            overall_risk_score=max(0.0, min(1.0, combined)),
            distress_tags=distress_tags,
            polarity=polarity,
        )

    def _layer_1_keywords(self, message: str) -> CDELayerResult:
        lowered = message.lower()
        signals: Dict[str, float] = {}
        for domain, tokens in self._lexicons.items():
            hits = sum(1 for token in tokens if token in lowered)
            signals[domain] = min(1.0, hits / 2.0)
        score = mean(signals.values()) if signals else 0.0
        return CDELayerResult(score=score, signals=signals)

    def _layer_2_sentiment(self, message: str) -> tuple[CDELayerResult, float]:
        words = [token.strip(".,!?;:").lower() for token in message.split()]
        counts = Counter(words)
        negative_hits = sum(counts[word] for word in self._negative_words if word in counts)
        positive_hits = sum(counts[word] for word in self._positive_words if word in counts)

        total = max(1, len(words))
        polarity = (positive_hits - negative_hits) / total  # [-1, 1] approx for short text
        drop = max(0.0, self._last_polarity - polarity)
        sentiment_stress = max(0.0, -polarity) + drop
        normalized = max(0.0, min(1.0, sentiment_stress))

        return (
            CDELayerResult(
                score=normalized,
                signals={
                    "polarity": polarity,
                    "polarity_drop": drop,
                    "negative_word_density": negative_hits / total,
                },
            ),
            polarity,
        )

    def _layer_3_behavior(
        self,
        *,
        message: str,
        recent_messages: List[str],
        response_latency_seconds: float | None,
    ) -> CDELayerResult:
        latency = 0.0
        if response_latency_seconds is not None:
            latency = max(0.0, min(1.0, response_latency_seconds / 60.0))

        complexity = self._message_complexity(message)
        looping = self._looping_score(message, recent_messages)

        score = max(0.0, min(1.0, 0.4 * latency + 0.25 * complexity + 0.35 * looping))
        return CDELayerResult(
            score=score,
            signals={
                "response_latency": latency,
                "message_complexity": complexity,
                "looping_behavior": looping,
            },
        )

    @staticmethod
    def _message_complexity(message: str) -> float:
        words = [w for w in message.split() if w]
        if not words:
            return 0.0
        unique_ratio = len(set(word.lower() for word in words)) / len(words)
        # Lower lexical variety plus short repetitive bursts may indicate collapse.
        return max(0.0, min(1.0, 1.0 - unique_ratio))

    @staticmethod
    def _looping_score(message: str, recent_messages: List[str]) -> float:
        lowered = message.lower()
        if not recent_messages:
            return 0.0
        same_count = sum(1 for msg in recent_messages if msg.lower().strip() == lowered.strip())
        return max(0.0, min(1.0, same_count / max(1, len(recent_messages))))

    @staticmethod
    def _collect_distress_tags(
        *,
        keyword_signals: Dict[str, float],
        behavior_signals: Dict[str, float],
    ) -> List[str]:
        tags: List[str] = []
        for key in ("negative_self_talk", "task_avoidance", "overwhelm"):
            if keyword_signals.get(key, 0.0) >= 0.4:
                tags.append(key)
        if behavior_signals.get("looping_behavior", 0.0) >= 0.4:
            tags.append("looping_behavior")
        return tags
