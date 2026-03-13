"""
CDE Pipeline — 3-layer, local-first Crisis Detection Engine.

Orchestrates the three analytical layers and produces a unified
``CDEResult`` with an aggregate distress score and recommended
persona weights.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .keyword_analyzer import KeywordAnalyzer, KeywordResult
from .sentiment_analyzer import SentimentAnalyzer, SentimentResult
from .behavioral_analyzer import BehavioralAnalyzer, BehavioralResult


DISTRESS_FIELD_TO_PERSONA: Dict[str, Dict[str, float]] = {
    "overwhelm": {"ash": 0.8, "myra": 0.7, "echo": 0.3, "sol": 0.1, "kai": 0.1},
    "negative_self_talk": {"echo": 0.9, "ash": 0.5, "myra": 0.3, "sol": 0.1, "kai": 0.1},
    "task_avoidance": {"sol": 0.9, "ash": 0.3, "echo": 0.2, "kai": 0.2, "myra": 0.1},
    "hyperfocus_loop": {"kai": 0.9, "sol": 0.3, "echo": 0.2, "ash": 0.1, "myra": 0.1},
    "relational_distress": {"myra": 0.9, "ash": 0.4, "echo": 0.4, "sol": 0.1, "kai": 0.1},
}


@dataclass
class CDEResult:
    """Unified output from the 3-layer CDE pipeline."""
    keyword_result: KeywordResult
    sentiment_result: SentimentResult
    behavioral_result: BehavioralResult
    aggregate_distress: float
    recommended_weights: Dict[str, float]
    distress_type: str
    flags: List[str] = field(default_factory=list)


class CDEPipeline:
    """
    Runs text through all three analysis layers and produces a unified
    crisis-detection result with recommended persona weights.

    Layer weights in the aggregate:
        Layer 1 (Keyword):    0.40
        Layer 2 (Sentiment):  0.30
        Layer 3 (Behavioral): 0.30
    """

    LAYER_WEIGHTS = (0.40, 0.30, 0.30)

    def __init__(self) -> None:
        self.keyword_analyzer = KeywordAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.behavioral_analyzer = BehavioralAnalyzer()

    def analyse(
        self,
        text: str,
        timestamp: Optional[float] = None,
    ) -> CDEResult:
        kw = self.keyword_analyzer.analyse(text)

        sent = self.sentiment_analyzer.analyse(text)

        behav = self.behavioral_analyzer.record_message(text, timestamp)

        sent_distress = max(0.0, -sent.polarity) * 0.5 + sent.polarity_drop * 0.5
        sent_distress = min(sent_distress, 1.0)

        aggregate = (
            self.LAYER_WEIGHTS[0] * kw.overall_score
            + self.LAYER_WEIGHTS[1] * sent_distress
            + self.LAYER_WEIGHTS[2] * behav.overall_score
        )
        aggregate = round(min(aggregate, 1.0), 4)

        distress_type = self._resolve_distress_type(kw, sent, behav)
        weights = self._compute_persona_weights(kw, sent_distress, behav, distress_type)

        all_flags = list(behav.flags)
        if sent.polarity_drop > 0.4:
            all_flags.append("polarity_drop_significant")
        if sent.emotional_volatility > 0.5:
            all_flags.append("emotional_volatility_high")
        if kw.overall_score > 0.6:
            all_flags.append("keyword_distress_high")

        return CDEResult(
            keyword_result=kw,
            sentiment_result=sent,
            behavioral_result=behav,
            aggregate_distress=aggregate,
            recommended_weights=weights,
            distress_type=distress_type,
            flags=all_flags,
        )

    def reset(self) -> None:
        self.sentiment_analyzer.reset()
        self.behavioral_analyzer.reset()

    def _resolve_distress_type(
        self, kw: KeywordResult, sent: SentimentResult, behav: BehavioralResult
    ) -> str:
        if kw.overall_score > 0.1:
            return kw.dominant_field

        if "possible_shutdown" in behav.flags:
            return "overwhelm"
        if "conversational_looping_detected" in behav.flags:
            return "hyperfocus_loop"
        if sent.dominant_emotion == "distressed":
            return "negative_self_talk"

        return "overwhelm"

    @staticmethod
    def _compute_persona_weights(
        kw: KeywordResult,
        sent_distress: float,
        behav: BehavioralResult,
        distress_type: str,
    ) -> Dict[str, float]:
        base = DISTRESS_FIELD_TO_PERSONA.get(
            distress_type,
            {"ash": 0.3, "sol": 0.2, "echo": 0.2, "kai": 0.1, "myra": 0.2},
        )
        weights = dict(base)

        severity_boost = (kw.overall_score + sent_distress + behav.overall_score) / 3.0
        for pid in weights:
            weights[pid] = min(weights[pid] + severity_boost * 0.2, 1.0)

        if "possible_shutdown" in behav.flags:
            weights["myra"] = min(weights["myra"] + 0.3, 1.0)
        if "conversational_looping_detected" in behav.flags:
            weights["kai"] = min(weights["kai"] + 0.2, 1.0)
        if "message_complexity_dropping" in behav.flags:
            weights["ash"] = min(weights["ash"] + 0.1, 1.0)

        return {k: round(v, 4) for k, v in weights.items()}
