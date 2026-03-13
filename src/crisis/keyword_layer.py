"""
CDE Layer 1 — Keyword / Semantic Field Analysis.

Local-only lexical scan for negative self-talk, task avoidance, and overwhelm
markers.  No cloud API is used; all matching is performed with static
dictionaries on-device.
"""

from __future__ import annotations

import re
from typing import Dict, List, Set

from src.models import CDESignal

# ---------------------------------------------------------------------------
# Semantic field libraries (extend as needed)
# ---------------------------------------------------------------------------

NEGATIVE_SELF_TALK: Set[str] = {
    "i'm worthless", "i'm a failure", "i can't do anything right",
    "i'm so stupid", "everyone hates me", "i ruin everything",
    "i'm broken", "what's wrong with me", "i always mess up",
    "i'm useless", "nobody cares", "i'm a burden",
    "i'll never be enough", "i hate myself", "i'm pathetic",
    "i can't do this", "i'm the worst",
}

TASK_AVOIDANCE: Set[str] = {
    "i can't start", "i don't know where to begin", "too many things",
    "can't focus", "nothing makes sense", "i'll do it later",
    "i keep putting it off", "everything is piling up",
    "i'm paralyzed", "i froze", "can't make a decision",
    "what's the point", "i give up", "it's too much",
}

OVERWHELM: Set[str] = {
    "everything is too much", "i can't breathe", "i'm drowning",
    "i'm going to explode", "make it stop", "i can't cope",
    "i'm falling apart", "i need it to stop", "shutting down",
    "i can't take it", "i'm overwhelmed", "i feel trapped",
    "walls are closing in", "i'm losing it",
}

_ALL_FIELDS: Dict[str, Set[str]] = {
    "negative_self_talk": NEGATIVE_SELF_TALK,
    "task_avoidance": TASK_AVOIDANCE,
    "overwhelm": OVERWHELM,
}

_WORD_RE = re.compile(r"[^a-z0-9' ]+")


def _normalise(text: str) -> str:
    return _WORD_RE.sub(" ", text.lower()).strip()


class KeywordLayer:
    """Layer 1 of the CDE — keyword / semantic field matching."""

    def analyse(self, text: str) -> CDESignal:
        norm = _normalise(text)
        hits: List[str] = []
        field_scores: Dict[str, float] = {}

        for field_name, phrases in _ALL_FIELDS.items():
            count = sum(1 for p in phrases if p in norm)
            if count:
                ratio = min(count / max(len(phrases) * 0.2, 1), 1.0)
                field_scores[field_name] = ratio
                hits.append(field_name)

        score = min(sum(field_scores.values()) / len(field_scores), 1.0) if field_scores else 0.0

        return CDESignal(
            layer="keyword",
            score=score,
            indicators=hits,
            metadata={"field_scores": field_scores},
        )
