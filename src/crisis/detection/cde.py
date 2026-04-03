"""
Crisis Detection Engine (CDE)
Strict 3-layer, local-first pipeline. No cloud processing for CDE.

Layer 1: Keyword/Semantic Field Analysis (negative self-talk, task avoidance, overwhelm)
Layer 2: Sentiment & Emotional Tone Analysis (polarity drops)
Layer 3: Behavioral Pattern Analysis (response latency, message complexity, looping)

Local-first: All processing runs locally. No external API calls.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import re


@dataclass
class CDEResult:
    """Aggregated result from 3-layer CDE pipeline."""
    timestamp: datetime
    layer1_score: float  # 0.0-1.0
    layer2_score: float  # 0.0-1.0
    layer3_score: float  # 0.0-1.0
    composite_score: float  # 0.0-1.0 weighted combination
    detected_fields: List[str] = field(default_factory=list)
    suggested_distress_key: Optional[str] = None  # For Fusion Engine input
    metadata: Dict[str, Any] = field(default_factory=dict)


# Layer 1: Semantic fields (local keyword/phrase matching)
SEMANTIC_FIELDS = {
    "negative_self_talk": [
        r"\b(i('m| am) )?(so |really |such )?(stupid|dumb|worthless|failure|useless|pathetic|broken)\b",
        r"\b(can't|cannot) (do anything|get anything right)\b",
        r"\b(hate|loathe) (myself|my life)\b",
        r"\b(no one|nobody) (cares|understands)\b",
        r"\b(always|never) (fail|mess up)\b",
        r"\bwhy (am i|do i) (even )?try\b",
        r"\b(self[- ]?blame|blame myself)\b",
    ],
    "task_avoidance": [
        r"\b(can't|cannot) (do|start|finish) (basic )?(tasks?|things)\b",
        r"\b(overwhelm|overwhelmed)\b",
        r"\b(stuck|paralyzed|frozen)\b",
        r"\b(avoid|avoiding) (everything|all of it)\b",
        r"\b(executive function|can't think)\b",
        r"\b(too many|too much) (to do|going on)\b",
    ],
    "overwhelm": [
        r"\b(everything )?hurts?\b",
        r"\b(meltdown|melting down)\b",
        r"\b(shut down|shutdown)\b",
        r"\b(don't|do not) know\b",
        r"\b(overwhelm|overwhelmed|overwhelming)\b",
        r"\b(can't|cannot) cope\b",
        r"\b(hyperfocus|stuck in (a )?loop)\b",
    ],
}

# Polarity indicators for Layer 2 (simple local sentiment)
NEGATIVE_WORDS = [
    "bad", "terrible", "awful", "horrible", "worst", "hate", "can't", "cannot",
    "fail", "failed", "failure", "stupid", "worthless", "stuck", "overwhelm",
    "hurt", "hurts", "pain", "exhausted", "drained", "empty",
]
POSITIVE_WORDS = [
    "ok", "okay", "fine", "good", "great", "better", "manage", "cope", "hope",
]


class CrisisDetectionEngine:
    """
    3-layer local-first CDE.
    No external APIs. All processing in-process.
    """

    def __init__(
        self,
        layer1_weight: float = 0.4,
        layer2_weight: float = 0.35,
        layer3_weight: float = 0.25,
    ):
        self.layer1_weight = layer1_weight
        self.layer2_weight = layer2_weight
        self.layer3_weight = layer3_weight

        # Behavioral state (in-memory, local)
        self._message_history: List[Dict[str, Any]] = []
        self._max_history = 50

    def _layer1_keyword_semantic(self, text: str) -> tuple:
        """
        Layer 1: Keyword/Semantic Field Analysis.
        Returns (score 0-1, list of matched field names).
        """
        if not text or not text.strip():
            return 0.0, []

        text_lower = text.lower().strip()
        detected: List[str] = []
        total_matches = 0

        for field_name, patterns in SEMANTIC_FIELDS.items():
            for pat in patterns:
                if re.search(pat, text_lower, re.IGNORECASE):
                    if field_name not in detected:
                        detected.append(field_name)
                    total_matches += 1
                    break

        # Score: more fields = higher. Cap at 1.0.
        score = min(1.0, len(detected) * 0.35 + total_matches * 0.15)
        return score, detected

    def _layer2_sentiment(self, text: str) -> float:
        """
        Layer 2: Sentiment & Emotional Tone Analysis.
        Simple local polarity. No cloud NLP.
        """
        if not text or not text.strip():
            return 0.0

        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return 0.0

        neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
        pos_count = sum(1 for w in words if w in POSITIVE_WORDS)

        # Polarity drop: more negative than positive
        delta = neg_count - pos_count
        # Map to 0-1 (higher = more distress)
        score = min(1.0, max(0.0, 0.5 + delta * 0.15))
        return score

    def _layer3_behavioral(
        self,
        text: str,
        latency_seconds: Optional[float] = None,
        is_loop: bool = False,
    ) -> float:
        """
        Layer 3: Behavioral Pattern Analysis.
        Tracks response latency, message complexity, looping.
        """
        score = 0.0

        # Message complexity drop: very short repeated messages can indicate overwhelm
        if text:
            word_count = len(text.split())
            if word_count <= 3 and len(self._message_history) >= 2:
                # User sending very short messages repeatedly
                score += 0.3
            if word_count >= 50 and "overwhelm" in text.lower():
                score += 0.2

        # Latency: long delays can indicate avoidance or freeze
        if latency_seconds is not None:
            if latency_seconds > 300:  # 5+ min delay
                score += 0.4
            elif latency_seconds > 60:
                score += 0.2

        # Looping: same/similar message repeated
        if is_loop and self._message_history:
            score += 0.4

        return min(1.0, score)

    def record_message(self, text: str, latency_seconds: Optional[float] = None) -> None:
        """Record user message for behavioral analysis. Local storage only."""
        self._message_history.append({
            "text": text,
            "latency": latency_seconds,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)

    def detect(
        self,
        text: str,
        latency_seconds: Optional[float] = None,
        is_loop: Optional[bool] = None,
    ) -> CDEResult:
        """
        Run full 3-layer CDE pipeline on input text.
        All processing local. No cloud calls.
        """
        timestamp = datetime.now()

        l1_score, detected_fields = self._layer1_keyword_semantic(text)
        l2_score = self._layer2_sentiment(text)

        if is_loop is None and self._message_history:
            last = self._message_history[-1].get("text", "")
            is_loop = text.strip().lower() == last.strip().lower()
        is_loop = is_loop or False

        l3_score = self._layer3_behavioral(text, latency_seconds, is_loop)

        composite = (
            l1_score * self.layer1_weight
            + l2_score * self.layer2_weight
            + l3_score * self.layer3_weight
        )

        # Suggest distress key for Fusion Engine
        suggested = None
        if "overwhelm" in detected_fields and ("shut" in text.lower() or "don't know" in text.lower()):
            suggested = "shutdown"
        elif "meltdown" in str(detected_fields).lower() or "overwhelm" in detected_fields:
            suggested = "meltdown"
        elif "task_avoidance" in detected_fields or "negative_self_talk" in detected_fields:
            if "negative_self_talk" in detected_fields and "self" in text.lower():
                suggested = "negative_self_talk"
            else:
                suggested = "executive_dysfunction"
        elif "hyperfocus" in str(detected_fields).lower() or "loop" in text.lower():
            suggested = "hyperfocus_stuck"

        if not suggested and detected_fields:
            suggested = detected_fields[0]

        return CDEResult(
            timestamp=timestamp,
            layer1_score=l1_score,
            layer2_score=l2_score,
            layer3_score=l3_score,
            composite_score=composite,
            detected_fields=detected_fields,
            suggested_distress_key=suggested,
            metadata={
                "is_loop": is_loop,
                "latency_seconds": latency_seconds,
            },
        )
