"""
Layer 2: Sentiment & Emotional Tone Analysis
Tracks polarity drops using local lexicons—no cloud APIs.

Designed for local-first, privacy-preserving emotional tone detection.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import re


@dataclass
class SentimentResult:
    """Result of sentiment/emotional tone analysis."""
    polarity: float  # -1.0 (negative) to 1.0 (positive)
    negative_intensity: float
    positive_intensity: float
    dominant_emotion: Optional[str]
    polarity_drop_detected: bool


# Local sentiment lexicons (simplified; expandable without cloud)
NEGATIVE_EMOTIONAL_TERMS = {
    "terrible", "awful", "horrible", "miserable", "hopeless", "desperate",
    "anxious", "panic", "dread", "fear", "scared", "worried", "stressed",
    "sad", "depressed", "empty", "numb", "lonely", "isolated",
    "angry", "frustrated", "irritated", "overwhelmed", "exhausted",
    "ashamed", "guilty", "worthless", "rejected", "abandoned",
    "confused", "lost", "stuck", "trapped", "helpless", "powerless",
}

POSITIVE_EMOTIONAL_TERMS = {
    "okay", "ok", "fine", "good", "better", "calm", "relieved", "hopeful",
    "grateful", "proud", "content", "peaceful", "safe", "supported",
}


class Layer2SentimentAnalyzer:
    """
    Local-first sentiment and emotional tone analyzer.
    Tracks polarity and detects significant drops without cloud processing.
    """

    def __init__(
        self,
        polarity_drop_threshold: float = -0.3,
        custom_negative: Optional[set] = None,
        custom_positive: Optional[set] = None,
    ):
        self.polarity_drop_threshold = polarity_drop_threshold
        self.negative_terms = NEGATIVE_EMOTIONAL_TERMS | (custom_negative or set())
        self.positive_terms = POSITIVE_EMOTIONAL_TERMS | (custom_positive or set())

    def analyze(
        self,
        text: str,
        previous_polarity: Optional[float] = None,
    ) -> SentimentResult:
        """
        Analyze emotional tone. If previous_polarity is provided,
        detects whether a significant polarity drop occurred.
        """
        if not text or not isinstance(text, str):
            return SentimentResult(
                polarity=0.0,
                negative_intensity=0.0,
                positive_intensity=0.0,
                dominant_emotion=None,
                polarity_drop_detected=False,
            )

        text_lower = text.lower()
        words = re.findall(r"\b\w+\b", text_lower)

        neg_count = sum(1 for w in words if w in self.negative_terms)
        pos_count = sum(1 for w in words if w in self.positive_terms)

        total = len(words) or 1
        neg_intensity = min(1.0, neg_count / (total * 0.5))
        pos_intensity = min(1.0, pos_count / (total * 0.5))

        # Polarity: positive minus negative, normalized to [-1, 1]
        raw = pos_intensity - neg_intensity
        polarity = max(-1.0, min(1.0, raw))

        dominant = None
        if neg_intensity > pos_intensity and neg_intensity > 0.1:
            dominant = "negative"
        elif pos_intensity > neg_intensity and pos_intensity > 0.1:
            dominant = "positive"

        drop_detected = False
        if previous_polarity is not None:
            drop = polarity - previous_polarity
            if drop <= self.polarity_drop_threshold:
                drop_detected = True

        return SentimentResult(
            polarity=round(polarity, 4),
            negative_intensity=round(neg_intensity, 4),
            positive_intensity=round(pos_intensity, 4),
            dominant_emotion=dominant,
            polarity_drop_detected=drop_detected,
        )
