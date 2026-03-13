"""Local-first three-layer Crisis Detection Engine (CDE)."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CDELayerResult:
    score: float
    details: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class CDEAssessment:
    layer1: CDELayerResult
    layer2: CDELayerResult
    layer3: CDELayerResult
    overall_risk: float
    flags: List[str]
    local_first: bool


class CrisisDetectionEngine:
    """Analyzes distress with lexical, sentiment, and behavioral layers."""

    def __init__(self, config: Optional[Dict[str, object]] = None):
        config = config or {}
        cde = config.get("cde", {}) if isinstance(config, dict) else {}

        self.local_processing_only = bool(
            cde.get("local_processing_only", True)
        )

        self.layer1_cfg = cde.get("layer1", {})
        self.layer2_cfg = cde.get("layer2", {})
        self.layer3_cfg = cde.get("layer3", {})
        self.layer_weights = cde.get(
            "layer_weights",
            {"layer1": 0.4, "layer2": 0.3, "layer3": 0.3},
        )

    def analyze(
        self,
        message_history: List[str],
        response_latency_seconds: Optional[float] = None,
    ) -> CDEAssessment:
        if not message_history:
            empty = CDELayerResult(0.0, {})
            return CDEAssessment(
                layer1=empty,
                layer2=empty,
                layer3=empty,
                overall_risk=0.0,
                flags=[],
                local_first=self.local_processing_only,
            )

        layer1 = self._analyze_layer1(message_history)
        layer2 = self._analyze_layer2(message_history)
        layer3 = self._analyze_layer3(message_history, response_latency_seconds)

        weighted_average = (
            layer1.score * float(self.layer_weights.get("layer1", 0.4))
            + layer2.score * float(self.layer_weights.get("layer2", 0.3))
            + layer3.score * float(self.layer_weights.get("layer3", 0.3))
        )
        peak_signal = max(layer1.score, layer2.score, layer3.score)
        overall = max(0.0, min(weighted_average + 0.2 * peak_signal, 1.0))

        flags: List[str] = []
        if layer1.score >= 0.6:
            flags.append("semantic_distress_high")
        if layer2.score >= 0.6:
            flags.append("emotional_tone_drop")
        if layer3.score >= 0.6:
            flags.append("behavioral_pattern_alert")
        if overall >= 0.75:
            flags.append("high_risk")

        return CDEAssessment(
            layer1=layer1,
            layer2=layer2,
            layer3=layer3,
            overall_risk=overall,
            flags=flags,
            local_first=self.local_processing_only,
        )

    def _analyze_layer1(self, message_history: List[str]) -> CDELayerResult:
        text = " ".join(message_history).lower()
        libraries = self.layer1_cfg.get("keyword_libraries", {})
        category_weights = self.layer1_cfg.get("weights", {})

        category_scores: Dict[str, float] = {}
        weighted_total = 0.0
        weight_sum = 0.0
        for category, words in libraries.items():
            if not isinstance(words, list):
                continue
            word_hits = sum(1 for token in words if str(token).lower() in text)
            denominator = max(1, len(words))
            score = min(1.0, word_hits / denominator)
            category_scores[category] = score

            weight = float(category_weights.get(category, 1.0))
            weighted_total += score * weight
            weight_sum += weight

        layer_score = (weighted_total / weight_sum) if weight_sum else 0.0
        return CDELayerResult(score=max(0.0, min(layer_score, 1.0)), details=category_scores)

    def _analyze_layer2(self, message_history: List[str]) -> CDELayerResult:
        lexicon = self.layer2_cfg.get("lexicon", {})
        negative = [str(token).lower() for token in lexicon.get("negative", [])]
        positive = [str(token).lower() for token in lexicon.get("positive", [])]
        drop_threshold = float(self.layer2_cfg.get("polarity_drop_threshold", 0.25))

        latest = " ".join(message_history[-2:]).lower()
        recent = " ".join(message_history[-3:]).lower()

        latest_neg = sum(1 for token in negative if token in latest)
        latest_pos = sum(1 for token in positive if token in latest)
        latest_total = max(1, latest_neg + latest_pos)
        latest_polarity = (latest_pos - latest_neg) / latest_total

        recent_neg = sum(1 for token in negative if token in recent)
        recent_pos = sum(1 for token in positive if token in recent)
        recent_total = max(1, recent_neg + recent_pos)
        recent_polarity = (recent_pos - recent_neg) / recent_total

        drop = max(0.0, recent_polarity - latest_polarity)
        polarity_risk = max(0.0, -latest_polarity)
        negativity_density = latest_neg / latest_total
        drop_risk = min(1.0, drop / max(0.01, drop_threshold))
        score = min(1.0, 0.5 * polarity_risk + 0.3 * drop_risk + 0.2 * negativity_density)

        return CDELayerResult(
            score=score,
            details={
                "latest_polarity": latest_polarity,
                "recent_polarity": recent_polarity,
                "polarity_drop": drop,
                "negativity_density": negativity_density,
            },
        )

    def _analyze_layer3(
        self,
        message_history: List[str],
        response_latency_seconds: Optional[float],
    ) -> CDELayerResult:
        thresholds = self.layer3_cfg.get("thresholds", {})
        latency_threshold = float(thresholds.get("response_latency_seconds", 45.0))
        low_complexity_threshold = float(thresholds.get("min_avg_tokens", 4.0))
        looping_similarity_threshold = float(thresholds.get("looping_similarity", 0.75))

        latest_tokens = message_history[-1].split()
        avg_tokens = (
            sum(len(message.split()) for message in message_history[-3:])
            / max(1, len(message_history[-3:]))
        )

        latency = response_latency_seconds if response_latency_seconds is not None else 0.0
        latency_risk = min(1.0, latency / max(1.0, latency_threshold))

        complexity_gap = max(0.0, low_complexity_threshold - avg_tokens)
        complexity_risk = min(1.0, complexity_gap / max(1.0, low_complexity_threshold))

        loop_risk = 0.0
        if len(message_history) >= 2:
            previous_tokens = set(message_history[-2].lower().split())
            current_tokens = set(token.lower() for token in latest_tokens)
            union = previous_tokens | current_tokens
            overlap = previous_tokens & current_tokens
            similarity = (len(overlap) / len(union)) if union else 0.0
            if similarity >= looping_similarity_threshold:
                loop_risk = similarity

        score = min(1.0, (latency_risk + complexity_risk + loop_risk) / 3.0)
        return CDELayerResult(
            score=score,
            details={
                "latency_risk": latency_risk,
                "complexity_risk": complexity_risk,
                "looping_risk": loop_risk,
            },
        )
