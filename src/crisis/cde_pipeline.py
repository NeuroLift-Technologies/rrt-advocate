"""
Crisis Detection Engine (CDE) - 3-Layer Pipeline
Local-first orchestration of Layer 1 (Keyword), Layer 2 (Sentiment), Layer 3 (Behavioral).

All processing is local. No user data is sent to cloud by default.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from .detectors.layer1_keyword import Layer1KeywordAnalyzer, KeywordMatch
from .detectors.layer2_sentiment import Layer2SentimentAnalyzer, SentimentResult
from .detectors.layer3_behavioral import Layer3BehavioralAnalyzer, BehavioralResult


@dataclass
class CDEOutput:
    """Aggregated output from the 3-layer CDE pipeline."""
    timestamp: datetime
    layer1_keyword: Dict[str, Any]
    layer2_sentiment: Dict[str, Any]
    layer3_behavioral: Dict[str, Any]
    combined_risk_score: float  # 0.0–1.0
    dominant_semantic_field: Optional[str]
    polarity_drop_detected: bool
    looping_detected: bool


class CDEPipeline:
    """
    Orchestrates the 3-layer local-first Crisis Detection Engine.
    """

    def __init__(
        self,
        layer1_weight: float = 0.4,
        layer2_weight: float = 0.35,
        layer3_weight: float = 0.25,
    ):
        self.layer1 = Layer1KeywordAnalyzer()
        self.layer2 = Layer2SentimentAnalyzer()
        self.layer3 = Layer3BehavioralAnalyzer()
        self.layer1_weight = layer1_weight
        self.layer2_weight = layer2_weight
        self.layer3_weight = layer3_weight
        self._last_polarity: Optional[float] = None

    def add_interaction(self, text: str, timestamp: Optional[datetime] = None) -> None:
        """Feed user message into behavioral layer for pattern tracking."""
        self.layer3.add_interaction(text, timestamp)

    def run(
        self,
        text: str,
        timestamp: Optional[datetime] = None,
    ) -> CDEOutput:
        """
        Run full 3-layer analysis on input text.
        All processing is local.
        """
        ts = timestamp or datetime.now()

        # Layer 1: Keyword / Semantic
        l1_results = self.layer1.analyze(text)
        l1_max = max((r.normalized_score for r in l1_results.values()), default=0.0)
        dominant_field = self.layer1.get_dominant_field(text)
        l1_dict = {
            k: {
                "matched": v.matched_terms,
                "score": v.normalized_score,
            }
            for k, v in l1_results.items()
        }

        # Layer 2: Sentiment
        l2_result = self.layer2.analyze(text, self._last_polarity)
        self._last_polarity = l2_result.polarity
        # Risk from negative polarity: map [-1,1] to [1,0] for risk
        l2_risk = (1.0 - l2_result.polarity) / 2.0 if l2_result.polarity is not None else 0.5
        if l2_result.polarity_drop_detected:
            l2_risk = min(1.0, l2_risk + 0.2)
        l2_dict = {
            "polarity": l2_result.polarity,
            "negative_intensity": l2_result.negative_intensity,
            "polarity_drop_detected": l2_result.polarity_drop_detected,
        }

        # Layer 3: Behavioral
        l3_result = self.layer3.analyze(ts)
        l3_risk = 0.0
        if l3_result.looping_detected:
            l3_risk = 0.8
        elif l3_result.message_complexity_trend == "decreasing":
            l3_risk = 0.4
        l3_dict = {
            "avg_latency_seconds": l3_result.avg_response_latency_seconds,
            "complexity_trend": l3_result.message_complexity_trend,
            "looping_detected": l3_result.looping_detected,
        }

        # Combined risk (weighted)
        combined = (
            self.layer1_weight * l1_max
            + self.layer2_weight * l2_risk
            + self.layer3_weight * l3_risk
        )
        combined = min(1.0, max(0.0, combined))

        return CDEOutput(
            timestamp=ts,
            layer1_keyword=l1_dict,
            layer2_sentiment=l2_dict,
            layer3_behavioral=l3_dict,
            combined_risk_score=round(combined, 4),
            dominant_semantic_field=dominant_field,
            polarity_drop_detected=l2_result.polarity_drop_detected,
            looping_detected=l3_result.looping_detected,
        )
