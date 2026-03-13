"""
Layer 1 — Keyword / Semantic Field Analysis.

Entirely local; no external API calls.  Uses curated semantic fields for:
  - Negative self-talk
  - Task avoidance
  - Overwhelm
  - Burnout
  - Shutdown / dissociation
  - Shame / rejection sensitivity

Each field has a weight and triggers a CrisisSignal when matched.
"""
from __future__ import annotations

import re

from .models import CrisisSignal

# ---------------------------------------------------------------------------
# Semantic field definitions
# Each entry: (field_name, signal_type, base_score, keyword_patterns)
# ---------------------------------------------------------------------------
SEMANTIC_FIELDS: list[tuple[str, str, float, list[str]]] = [
    (
        "negative_self_talk",
        "negative_self_talk",
        0.65,
        [
            r"\bi('?m| am)\s+\w*\s*(worthless|useless|stupid|broken|a failure|a burden)\b",
            r"\b(worthless|useless|hopeless|pathetic)\b",
            r"\bcan'?t do anything right\b",
            r"\beveryone (hates|is better than) me\b",
            r"\bi hate myself\b",
            r"\bi'?m so (dumb|pathetic|terrible)\b",
            r"\bwhat'?s wrong with me\b",
            r"\bi'?m (always|never) (good|enough|able)\b",
        ],
    ),
    (
        "task_avoidance",
        "task_avoidance",
        0.45,
        [
            r"\bcan'?t (start|begin|do|focus|concentrate)\b",
            r"\bkeep (putting|pushing) (it|things) off\b",
            r"\beven (basic|simple) tasks\b",
            r"\bparalys(ed|ed|is)\b",
            r"\bexecutive (dysfunction|function(ing)?)\b",
            r"\bcan'?t make (a|any) decision\b",
            r"\bstuck\b",
        ],
    ),
    (
        "overwhelm",
        "overwhelm",
        0.55,
        [
            r"\beverything is (too much|overwhelming)\b",
            r"\bcan'?t cope\b",
            r"\btoo much (going on|to handle|at once)\b",
            r"\bsensory overload\b",
            r"\bmeltdown\b",
            r"\bbreaking (down|point)\b",
            r"\boverwhel(med|ming)\b",
        ],
    ),
    (
        "burnout",
        "burnout",
        0.50,
        [
            r"\bcompletely (drained|exhausted|burnt out)\b",
            r"\bnoth(ing|ing left) in (me|the tank)\b",
            r"\bsurvivor mode\b",
            r"\bburnout\b",
            r"\bno (energy|motivation|capacity)\b",
            r"\bjust (surviving|getting through)\b",
        ],
    ),
    (
        "shutdown_dissociation",
        "shutdown",
        0.70,
        [
            r"\bshut(ting)? down\b",
            r"\bcan'?t (feel|think|speak|talk)\b",
            r"\bgone blank\b",
            r"\bdissociat(ing|ion|ed)\b",
            r"\bnumb\b",
            r"\bfrozen\b",
        ],
    ),
    (
        "shame_rejection_sensitivity",
        "shame",
        0.55,
        [
            r"\bso ashamed\b",
            r"\bi'?m embarrass(ed|ing)\b",
            r"\brejection.{0,30}(hurts|fear|sensitivity)\b",
            r"\bRSD\b",
            r"\bcan'?t handle (criticism|feedback)\b",
            r"\bfeel like a (failure|fraud|impostor)\b",
            r"\bit'?s (all )?my fault\b",
            r"\bblaming myself\b",
            r"\bcan'?t stop blaming\b",
        ],
    ),
    (
        "hyperfocus_loop",
        "hyperfocus_loop",
        0.45,
        [
            r"\bcan'?t stop (thinking|doing)\b",
            r"\bstuck (in a loop|on this)\b",
            r"\bhyper.?focus(ing|ed)?\b",
            r"\bkeep (going back|thinking about)\b",
            r"\bobsess(ing|ed)\b",
        ],
    ),
]

_SELF_HARM_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.I)
    for p in [
        r"\bwant(ing)?\s+to\s+(hurt|harm|kill)\s+(myself|me)\b",
        r"\b(thinking about|going to|gonna)\s+(hurt|harm|kill)\s+(myself|me)\b",
        r"\b(suicid(al|e)|self[- ]?harm|self[- ]?injur)\b",
        r"\bdon'?t want to (be here|exist|live)\b",
        r"\bending it\b",
        r"\b(hurt|harm|kill)\s+(myself|me)\b",
    ]
]


def analyse(text: str) -> tuple[float, list[CrisisSignal]]:
    """
    Run Layer 1 analysis on a text string.

    Returns
    -------
    (layer_score, signals)
      layer_score: 0.0–1.0 weighted aggregate of matched fields.
      signals: individual CrisisSignal objects for each matched field.
    """
    signals: list[CrisisSignal] = []
    scores: list[float] = []

    # Check for self-harm language first — always maximum severity
    for pattern in _SELF_HARM_PATTERNS:
        if pattern.search(text):
            signals.append(
                CrisisSignal(
                    source_layer=1,
                    signal_type="self_harm_language",
                    score=1.0,
                    evidence=pattern.pattern,
                )
            )
            scores.append(1.0)

    for field_name, signal_type, base_score, patterns in SEMANTIC_FIELDS:
        matched_excerpts: list[str] = []
        for raw_pat in patterns:
            pat = re.compile(raw_pat, re.I)
            for match in pat.finditer(text):
                matched_excerpts.append(match.group(0))

        if matched_excerpts:
            intensity = min(1.0, base_score + 0.05 * (len(matched_excerpts) - 1))
            signals.append(
                CrisisSignal(
                    source_layer=1,
                    signal_type=signal_type,
                    score=intensity,
                    evidence="; ".join(matched_excerpts[:3]),
                )
            )
            scores.append(intensity)

    if not scores:
        return 0.0, []

    layer_score = min(1.0, sum(scores) / max(1, len(scores)) + 0.1 * len(scores))
    return layer_score, signals
