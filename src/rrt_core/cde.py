from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from .models import CDELayerResult, CrisisAssessment, DistressInput, InteractionContext


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class CrisisDetectionEngine:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.lexicons = config.get("cde", {}).get("layer_1", {}).get("lexicons", {})
        self.sentiment_config = config.get("cde", {}).get("layer_2", {})
        self.behavior_config = config.get("cde", {}).get("layer_3", {})
        self.layer_weights = config.get(
            "cde", {}
        ).get("layer_weights", {"semantic": 0.45, "sentiment": 0.30, "behavioral": 0.25})
        self.risk_thresholds = config.get("risk_thresholds", {})

    def analyze(self, context: InteractionContext) -> CrisisAssessment:
        semantic = self._semantic_layer(context)
        sentiment = self._sentiment_layer(context)
        behavioral = self._behavioral_layer(context)

        severity = _clamp(
            semantic.score * float(self.layer_weights.get("semantic", 0.45))
            + sentiment.score * float(self.layer_weights.get("sentiment", 0.30))
            + behavioral.score * float(self.layer_weights.get("behavioral", 0.25))
        )
        confidence = _clamp((semantic.score + sentiment.score + behavioral.score) / 3)
        risk_level = self._risk_level_for(severity)
        semantic_hits = [name for name, score in semantic.details.items() if score >= 0.18]
        behavioral_flags = [name for name, score in behavioral.details.items() if score >= 0.30]
        silent_mode = context.distress_input == DistressInput.DONT_KNOW_SHUT_DOWN or "shutdown" in semantic_hits

        return CrisisAssessment(
            timestamp=datetime.now(UTC),
            distress_input=context.distress_input,
            severity_score=severity,
            confidence_score=confidence,
            risk_level=risk_level,
            layer_results=[semantic, sentiment, behavioral],
            semantic_hits=semantic_hits,
            behavioral_flags=behavioral_flags,
            silent_mode=silent_mode,
        )

    def _semantic_layer(self, context: InteractionContext) -> CDELayerResult:
        corpus = " ".join([*context.recent_user_messages, context.user_message]).lower()
        details: dict[str, float] = {}
        matched_labels = []
        for label, phrases in self.lexicons.items():
            hits = sum(corpus.count(phrase.lower()) for phrase in phrases)
            score = _clamp(hits / max(1, len(phrases) / 2))
            details[label] = score
            if score > 0:
                matched_labels.append(label.replace("_", " "))
        overall = _clamp(sum(details.values()) / max(1, len(details)))
        summary = "Semantic fields active: " + (", ".join(matched_labels) if matched_labels else "none")
        return CDELayerResult(name="semantic", score=overall, summary=summary, details=details)

    def _sentiment_layer(self, context: InteractionContext) -> CDELayerResult:
        current_tokens = context.user_message.lower().split()
        history_tokens = " ".join(context.recent_user_messages).lower().split()
        negative_terms = set(self.sentiment_config.get("negative_terms", []))
        positive_terms = set(self.sentiment_config.get("positive_terms", []))
        intense_terms = set(self.sentiment_config.get("intense_terms", []))

        negative_ratio = _clamp(sum(token in negative_terms for token in current_tokens) / max(1, len(current_tokens)))
        positive_ratio = _clamp(sum(token in positive_terms for token in current_tokens) / max(1, len(current_tokens)))
        intensity_ratio = _clamp(sum(token in intense_terms for token in current_tokens) / max(1, len(current_tokens)))
        history_negative = _clamp(sum(token in negative_terms for token in history_tokens) / max(1, len(history_tokens)))
        polarity_drop = _clamp(max(0.0, negative_ratio - history_negative + positive_ratio * -1))
        score = _clamp(negative_ratio * 0.5 + intensity_ratio * 0.3 + polarity_drop * 0.2)
        summary = "Negative tone tracked locally without cloud inference."
        return CDELayerResult(
            name="sentiment",
            score=score,
            summary=summary,
            details={
                "negative_ratio": negative_ratio,
                "positive_ratio": positive_ratio,
                "intensity_ratio": intensity_ratio,
                "polarity_drop": polarity_drop,
            },
        )

    def _behavioral_layer(self, context: InteractionContext) -> CDELayerResult:
        latency_thresholds = self.behavior_config.get("latency_threshold_seconds", {})
        latency = float(context.response_latency_seconds or 0.0)
        if latency >= float(latency_thresholds.get("critical", 900)):
            latency_score = 1.0
        elif latency >= float(latency_thresholds.get("high", 300)):
            latency_score = 0.7
        elif latency >= float(latency_thresholds.get("elevated", 60)):
            latency_score = 0.4
        else:
            latency_score = 0.0

        word_count = len(context.user_message.split())
        low_complexity = int(word_count <= int(self.behavior_config.get("low_complexity_word_count", 5)))
        complexity_score = 0.7 if low_complexity else 0.0

        window = int(self.behavior_config.get("repetition_window", 3))
        recent = [message.strip().lower() for message in context.recent_user_messages[-window:] if message.strip()]
        current = context.user_message.strip().lower()
        loop_counter = Counter(recent + ([current] if current else []))
        looping_score = 1.0 if loop_counter and loop_counter.most_common(1)[0][1] >= max(2, window) else 0.0

        score = _clamp(latency_score * 0.45 + complexity_score * 0.25 + looping_score * 0.30)
        summary = "Behavioral pattern layer uses latency, complexity, and looping only from local session state."
        return CDELayerResult(
            name="behavioral",
            score=score,
            summary=summary,
            details={
                "latency_score": latency_score,
                "complexity_score": complexity_score,
                "looping_score": looping_score,
            },
        )

    def _risk_level_for(self, severity: float) -> str:
        for label, bounds in self.risk_thresholds.items():
            lower, upper = bounds
            if lower <= severity < upper or (label == "acute" and severity <= upper):
                return label
        return "steady"
