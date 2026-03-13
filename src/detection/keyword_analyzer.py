"""
Layer 1 — Keyword / Semantic Field Analysis.

Local-first keyword matching against curated lexicons for negative
self-talk, task avoidance, overwhelm, and other neurodivergent
distress signals.  No cloud API calls — all processing is in-memory.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Set


@dataclass
class KeywordResult:
    """Output of Layer 1 analysis."""
    matched_fields: Dict[str, List[str]]
    field_scores: Dict[str, float]
    overall_score: float
    dominant_field: str


NEGATIVE_SELF_TALK: FrozenSet[str] = frozenset({
    "i'm worthless", "i'm a failure", "i can't do anything right",
    "i'm broken", "what's wrong with me", "i'm so stupid",
    "i'm useless", "i hate myself", "i'm pathetic", "i'm a burden",
    "everyone would be better off", "i ruin everything",
    "i can never", "i always mess up", "nothing i do matters",
    "i'm not good enough", "i don't deserve",
})

TASK_AVOIDANCE: FrozenSet[str] = frozenset({
    "i can't start", "can't do this", "too much", "can't focus",
    "i'll do it later", "what's the point", "i give up",
    "can't make myself", "can't get started", "paralysed",
    "don't know where to begin", "overwhelmed by the list",
    "everything is piling up", "falling behind",
    "i'm drowning in tasks",
})

OVERWHELM_EXPRESSIONS: FrozenSet[str] = frozenset({
    "everything hurts", "i can't breathe", "too much",
    "make it stop", "i can't take this", "i'm going to explode",
    "shut down", "shutting down", "can't cope", "can't handle",
    "losing it", "falling apart", "spiralling", "drowning",
    "meltdown", "having a meltdown", "breaking down",
    "i'm done", "i can't anymore",
})

HYPERFOCUS_LOOP: FrozenSet[str] = frozenset({
    "can't stop", "stuck in a loop", "can't let go",
    "obsessing", "fixated", "can't move on", "hours have passed",
    "lost track of time", "hyperfocus", "tunnel vision",
    "can't pull away", "one more thing", "just one more",
})

RELATIONAL_DISTRESS: FrozenSet[str] = frozenset({
    "they hate me", "nobody cares", "i'm alone", "rejected",
    "they're better off without me", "abandoned", "left out",
    "nobody understands", "all alone", "no one gets it",
    "pushed away", "invisible",
})

SEMANTIC_FIELDS: Dict[str, FrozenSet[str]] = {
    "negative_self_talk": NEGATIVE_SELF_TALK,
    "task_avoidance": TASK_AVOIDANCE,
    "overwhelm": OVERWHELM_EXPRESSIONS,
    "hyperfocus_loop": HYPERFOCUS_LOOP,
    "relational_distress": RELATIONAL_DISTRESS,
}

FIELD_WEIGHTS: Dict[str, float] = {
    "negative_self_talk": 0.25,
    "task_avoidance": 0.20,
    "overwhelm": 0.25,
    "hyperfocus_loop": 0.15,
    "relational_distress": 0.15,
}


class KeywordAnalyzer:
    """
    Layer 1 of the CDE.  Scans input text against semantic-field
    lexicons and returns field-level and aggregate distress scores.
    """

    def __init__(
        self,
        fields: Dict[str, FrozenSet[str]] | None = None,
        weights: Dict[str, float] | None = None,
    ) -> None:
        self.fields = fields or SEMANTIC_FIELDS
        self.weights = weights or FIELD_WEIGHTS

    def analyse(self, text: str) -> KeywordResult:
        normalised = text.lower().strip()

        matched_fields: Dict[str, List[str]] = {}
        field_scores: Dict[str, float] = {}

        for field_name, lexicon in self.fields.items():
            matches: List[str] = []
            for phrase in lexicon:
                if phrase in normalised:
                    matches.append(phrase)
            matched_fields[field_name] = matches
            if lexicon:
                field_scores[field_name] = min(len(matches) / 3.0, 1.0)
            else:
                field_scores[field_name] = 0.0

        weighted_sum = sum(
            field_scores.get(f, 0.0) * self.weights.get(f, 0.0)
            for f in self.fields
        )
        weight_total = sum(self.weights.get(f, 0.0) for f in self.fields)
        overall = weighted_sum / weight_total if weight_total else 0.0

        dominant = max(field_scores, key=lambda k: field_scores[k]) if field_scores else "overwhelm"

        return KeywordResult(
            matched_fields=matched_fields,
            field_scores=field_scores,
            overall_score=round(min(overall, 1.0), 4),
            dominant_field=dominant,
        )
