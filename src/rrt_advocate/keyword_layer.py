"""CDE Layer 1: Keyword / Semantic Field Analysis.

Local-first - pure pattern matching, no external API.

Faithful Python port of ``src/keywordLayer.ts`` in
``@neurolift-technologies/rrt-advocate``. Maintains libraries of semantically
related phrases organized into neurodivergent-specific distress categories, and
detects the presence of these semantic fields in user messages with confidence
scoring.

Design notes (preserved from the source):
- Patterns use case-insensitive regex.
- The SELF_HARM_RISK field always forces maximum confidence (1.0).
- Multiple field activations compound the confidence score (capped at 1.0).
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from .types import KeywordAnalysisResult, KeywordMatch, KeywordSemanticField

# ============================================================================
# Semantic Field Libraries
# Anti-Gaslight design: patterns detect distress signals without
# pathologizing normal human language. Patterns and ordering are preserved
# verbatim from the source.
# ============================================================================

FIELD_PATTERNS: List[Tuple[KeywordSemanticField, List[str]]] = [
    (
        KeywordSemanticField.NEGATIVE_SELF_TALK,
        [
            "i hate myself",
            "i('m| am) (so |really )?(worthless|useless|stupid|pathetic|awful|terrible|broken)",
            "i('m| am) a failure",
            "i always (mess|screw|f+uck) (up|everything)",
            "i('m| am) the worst",
            "i ruin everything",
            "(nobody|no one) cares (about me|anymore)?",
            "i (can't|cannot) do anything right",
            "why am i (so |like this|like that)",
            "i don't deserve",
            "i('m| am) so (dumb|stupid|bad)",
            "everything('s| is) my fault",
            "i('m| am) not good enough",
            "i('ve| have) ruined (it|everything|this)",
        ],
    ),
    (
        KeywordSemanticField.TASK_AVOIDANCE,
        [
            "(can'?t|cannot) start",
            "(can'?t|cannot) (do|finish|begin|complete|get started)",
            "don'?t know (how to |where to )?begin",
            "(can'?t|cannot) make myself",
            "(i'?ve? been|been) (procrastin|putting it off|avoiding)",
            "(too hard|too difficult|too much)",
            "(giving up|give up|gave up)",
            "what'?s the point",
            "can'?t (be|get) (motivated|started|going)",
            "(paralyzed|paralysed)",
            "(stuck|frozen) (on|with|at)",
        ],
    ),
    (
        KeywordSemanticField.OVERWHELM,
        [
            "too much (going on|happening|at once)",
            "(can'?t|cannot) cope",
            "(can'?t|cannot) handle (this|it|everything|anymore)",
            "(drowning|overwhelm(ed|ing))",
            "everything (is |feels )?(too much|overwhelming|impossible)",
            "(spinning|spiraling|spiral(l)?ing)",
            "(can'?t|cannot) breathe",
            "(shutting down|shutdown|shut(ting)? down)",
            "brain (is |feels )?(fried|overloaded|full|done)",
            "(so many|too many) (things|tasks|thoughts)",
            "(can'?t|cannot) think (straight|clearly)",
        ],
    ),
    (
        KeywordSemanticField.MELTDOWN,
        [
            "(melt(ing|ed|down)|meltdown)",
            "(fall(ing|en) apart|falling to pieces)",
            "(break(ing|down)|breakdown)",
            "(can'?t|cannot) stop (crying|shaking|panicking)",
            "(losing|lost) (it|control|my mind)",
            "(freaking|flipping|losing) out",
            "everything'?s (falling|crumbling|coming) apart",
            "(complete|total|full) (meltdown|breakdown|collapse)",
        ],
    ),
    (
        KeywordSemanticField.SHUTDOWN,
        [
            "(shut(ting)? down|shutdown)",
            "(completely |totally )?(blank|empty|numb|gone|void)",
            "(can'?t|cannot) (feel|think|move|respond)",
            "(dissociat(ing|ed)|dissociation)",
            "(frozen|froze(n)?|freezing)",
            "(checked out|checked off|not (here|present|real))",
            "(going |feel(ing)? )(numb|blank|empty)",
            "(words|thoughts) (won'?t|don'?t) come",
            "(can'?t|cannot) find (words|the words)",
            "(just|totally|completely) (done|gone|empty|blank)",
        ],
    ),
    (
        KeywordSemanticField.HYPERFOCUS_LOOP,
        [
            "(can'?t|cannot) stop (thinking|going back|focusing)",
            "(stuck|looping) (in|on) (a loop|it|this)",
            "(keep|keep on|keeps) (thinking|going back|looping|fixating)",
            "(hyperfocus(ing|ed)?|hyperfixat(ing|ion|ed))",
            "(rabbit hole|down a rabbit)",
            "(obsess(ing|ed|ion)|obsessive)",
            "(can'?t|cannot) (let it go|move on|stop|switch off)",
            "(loop(ing|ed)?|spiral(l)?ing) (back|on|about)",
            "(intrusive|unwanted) (thought|loop|fixation)",
        ],
    ),
    (
        KeywordSemanticField.SELF_HARM_RISK,
        [
            "(want to |going to |going to )(hurt|harm) (myself|me)",
            "(self[- ]?harm|self[- ]?hurt|self[- ]?injur)",
            "don'?t want to (be here|live|exist|continue)",
            "(better off|world (is|would be) better) (without me|if i (was|were) gone)",
            "(thinking about|thought about) (ending|stopping) (it|everything|my life)",
            "(suicid(e|al|ity)|want to die)",
            "(kill|end) myself",
        ],
    ),
]

# ============================================================================
# INTENTIONAL DIVERGENCE FROM THE PYTHON SOURCE - apostrophe fail-open.
# ----------------------------------------------------------------------------
# The canonical Python patterns require literal apostrophes in places (e.g.
# ``i (can't|cannot)``, ``i('m| am)``, ``i don't deserve``, ``everything('s| is)``).
# Voice-dictated / smart-quote text ("cant", "dont", "wont", "im", "youre",
# "everythings") would silently MISS those patterns. Because this is the
# 0.45-weighted Layer 1, a miss here is the worst case for the whole CDE.
#
# So - unlike every other formula/threshold/weight in this port, which is a
# faithful 1:1 - the matcher here is deliberately made apostrophe-insensitive:
# apostrophes are stripped from BOTH the input text and the compiled patterns,
# so "can't" and "cant" match identically. This is the same fail-open behaviour
# adopted in nlt-sdl. See KNOWN_LIMITATIONS.md.
# ============================================================================

#: ASCII apostrophe, right single quote (U+2019), modifier letter apostrophe (U+02BC).
_APOSTROPHES = re.compile("['’ʼ]")
#: Optional-apostrophe token ``'?`` in pattern sources.
_OPTIONAL_APOSTROPHE = re.compile("'\\?")
_LITERAL_APOSTROPHE = re.compile("'")


def _strip_apostrophes(text: str) -> str:
    """Strip apostrophes from input text so dictation/smart-quote forms match."""
    return _APOSTROPHES.sub("", text)


def _normalize_pattern(source: str) -> str:
    """Make a pattern source apostrophe-insensitive to match ``_strip_apostrophes``.

    Removes the optional-apostrophe token ``'?`` first (so ``can'?t`` -> ``cant``,
    not the broken ``can?t``), then any remaining literal apostrophes (so
    ``i('m| am)`` -> ``i(m| am)``).
    """
    return _LITERAL_APOSTROPHE.sub("", _OPTIONAL_APOSTROPHE.sub("", source))


#: Confidence weights for each semantic field.
FIELD_CONFIDENCE_WEIGHTS: Dict[KeywordSemanticField, float] = {
    KeywordSemanticField.NEGATIVE_SELF_TALK: 0.15,
    KeywordSemanticField.TASK_AVOIDANCE: 0.1,
    KeywordSemanticField.OVERWHELM: 0.15,
    KeywordSemanticField.MELTDOWN: 0.25,
    KeywordSemanticField.SHUTDOWN: 0.2,
    KeywordSemanticField.HYPERFOCUS_LOOP: 0.1,
    KeywordSemanticField.SELF_HARM_RISK: 1.0,  # Always escalates to maximum
}


class _CompiledField:
    __slots__ = ("field", "patterns", "sources")

    def __init__(
        self,
        field: KeywordSemanticField,
        patterns: List["re.Pattern[str]"],
        sources: List[str],
    ) -> None:
        self.field = field
        self.patterns = patterns
        self.sources = sources


class KeywordLayer:
    def __init__(self) -> None:
        self._compiled: List[_CompiledField] = [
            _CompiledField(
                field=fld,
                # Compile apostrophe-insensitive (see divergence note above)...
                patterns=[re.compile(_normalize_pattern(p), re.IGNORECASE) for p in patterns],
                # ...but keep the original source string for human-readable reporting.
                sources=list(patterns),
            )
            for fld, patterns in FIELD_PATTERNS
        ]

    def analyze(self, text: str) -> KeywordAnalysisResult:
        """Analyze text for semantic field matches.

        :param text: User message text to analyze.
        :returns: Detected fields, matches, and a compounded confidence score.
        """
        if not text or not text.strip():
            return KeywordAnalysisResult(
                detected_fields=[],
                matches=[],
                confidence_score=0.0,
                self_harm_detected=False,
                primary_field=None,
            )

        # Match against the apostrophe-stripped form (see divergence note above).
        # `matched_text`/`position` therefore index into the normalized haystack.
        haystack = _strip_apostrophes(text)

        detected_fields: List[KeywordSemanticField] = []
        all_matches: List[KeywordMatch] = []
        field_match_counts: Dict[KeywordSemanticField, int] = {}

        for compiled in self._compiled:
            matches_for_field: List[KeywordMatch] = []
            for i, pattern in enumerate(compiled.patterns):
                match = pattern.search(haystack)
                if match:
                    matches_for_field.append(
                        KeywordMatch(
                            field=compiled.field,
                            pattern=compiled.sources[i],
                            matched_text=match.group(0),
                            position=match.start(),
                        )
                    )
            if matches_for_field:
                detected_fields.append(compiled.field)
                field_match_counts[compiled.field] = len(matches_for_field)
                all_matches.extend(matches_for_field)

        confidence = self._compute_confidence(detected_fields, field_match_counts)
        self_harm = KeywordSemanticField.SELF_HARM_RISK in detected_fields

        # Primary field = highest (weight * match count).
        primary: Optional[KeywordSemanticField] = None
        if detected_fields:
            primary = detected_fields[0]
            best_score = FIELD_CONFIDENCE_WEIGHTS.get(primary, 0.0) * field_match_counts.get(
                primary, 1
            )
            for f in detected_fields:
                score = FIELD_CONFIDENCE_WEIGHTS.get(f, 0.0) * field_match_counts.get(f, 1)
                if score > best_score:
                    primary = f
                    best_score = score

        return KeywordAnalysisResult(
            detected_fields=detected_fields,
            matches=all_matches,
            confidence_score=confidence,
            self_harm_detected=self_harm,
            primary_field=primary,
        )

    def _compute_confidence(
        self,
        detected_fields: List[KeywordSemanticField],
        field_match_counts: Dict[KeywordSemanticField, int],
    ) -> float:
        """Compute overall confidence from detected fields.

        Self-harm detection always returns 1.0. Otherwise, compounds field
        weights with a small diminishing bonus for repeated matches.
        """
        if KeywordSemanticField.SELF_HARM_RISK in detected_fields:
            return 1.0
        if not detected_fields:
            return 0.0

        total = 0.0
        for f in detected_fields:
            weight = FIELD_CONFIDENCE_WEIGHTS.get(f, 0.1)
            count_bonus = min(0.05 * (field_match_counts.get(f, 1) - 1), 0.1)
            total += weight + count_bonus
        return min(1.0, total)
