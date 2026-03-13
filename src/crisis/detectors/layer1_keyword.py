"""
Layer 1: Keyword & Semantic Field Analysis
Local-first analysis for negative self-talk, task avoidance, overwhelm.

Uses predefined lexicons—no cloud API calls. Designed for neurodivergent
distress patterns (shame-resistant naming).
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Set, Optional


@dataclass
class KeywordMatch:
    """Match from keyword/semantic field analysis."""
    field: str
    matched_terms: List[str]
    raw_count: int
    normalized_score: float  # 0.0–1.0


# Semantic fields aligned with NLT ethos (non-judgmental, shame-resistant)
NEGATIVE_SELF_TALK_FIELD = {
    "can't", "never", "always", "failure", "stupid", "broken", "worthless",
    "hate myself", "not good enough", "should have", "never going to", "give up",
    "can't do", "useless", "pathetic", "waste", "screw up", "mess", "ruined",
    "why bother", "what's the point", "nothing works", "not capable",
}

TASK_AVOIDANCE_FIELD = {
    "overwhelmed", "overwhelm", "too much", "can't start", "don't know where",
    "paralyzed", "stuck", "freeze", "freezing", "blank", "nothing done",
    "avoiding", "put off", "procrastinat", "basic tasks", "simple things",
    "can't do basic", "can't even", "one thing", "everything at once",
    "where to begin", "don't know how", "too hard", "impossible",
}

OVERWHELM_FIELD = {
    "everything hurts", "shut down", "shutting down", "meltdown", "melting down",
    "too loud", "too bright", "sensory", "overstimulated", "burnout", "burnt out",
    "exhausted", "drained", "empty", "numb", "dissociate", "don't know",
    "don't care anymore", "checked out", "crashing", "breaking down",
    "can't cope", "falling apart", "falling to pieces",
}

# Hyperfocus/loop indicators (for Kai mapping)
HYPERFOCUS_LOOP_FIELD = {
    "stuck in", "can't stop", "loop", "looping", "fixated", "fixation",
    "hyperfocus", "hyper focus", "obsessed", "can't get out", "trapped in",
    "same thing", "going in circles", "spiraling", "spiral",
}


class Layer1KeywordAnalyzer:
    """
    Local-first keyword and semantic field analyzer.
    No external APIs. Uses predefined lexicons for neurodivergent distress.
    """

    def __init__(
        self,
        custom_fields: Optional[Dict[str, Set[str]]] = None,
    ):
        self.fields: Dict[str, Set[str]] = {
            "negative_self_talk": NEGATIVE_SELF_TALK_FIELD,
            "task_avoidance": TASK_AVOIDANCE_FIELD,
            "overwhelm": OVERWHELM_FIELD,
            "hyperfocus_loop": HYPERFOCUS_LOOP_FIELD,
        }
        if custom_fields:
            for name, terms in custom_fields.items():
                self.fields[name] = set(terms) if not isinstance(terms, set) else terms

    def analyze(self, text: str) -> Dict[str, KeywordMatch]:
        """
        Analyze text against semantic fields.
        Returns normalized scores per field (0.0–1.0).
        """
        if not text or not isinstance(text, str):
            return {}

        text_lower = text.lower().strip()
        words = set(re.findall(r"\b\w+\b", text_lower))
        # Also check 2–3 word phrases
        bigrams = set(
            " ".join(t) for t in zip(
                text_lower.split(), text_lower.split()[1:]
            )
        )
        trigrams = set(
            " ".join(t) for t in zip(
                text_lower.split(), text_lower.split()[1:], text_lower.split()[2:]
            )
        ) if len(text_lower.split()) >= 3 else set()
        all_tokens = words | bigrams | trigrams

        results: Dict[str, KeywordMatch] = {}
        for field_name, terms in self.fields.items():
            matched = [t for t in terms if t in text_lower or t in all_tokens]
            raw_count = len(matched)
            # Normalize to 0–1 (cap at ~5 matches for saturation)
            max_for_field = max(len(terms) * 0.3, 5)
            normalized = min(1.0, raw_count / max_for_field) if max_for_field > 0 else 0.0
            results[field_name] = KeywordMatch(
                field=field_name,
                matched_terms=matched,
                raw_count=raw_count,
                normalized_score=round(normalized, 4),
            )
        return results

    def get_dominant_field(self, text: str) -> Optional[str]:
        """Return the semantic field with highest normalized score."""
        results = self.analyze(text)
        if not results:
            return None
        return max(results.keys(), key=lambda k: results[k].normalized_score)
