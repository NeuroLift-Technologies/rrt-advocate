"""
CDE Layer 1: Keyword/Semantic Field Analysis
Local-first — pure Python pattern matching, no external API.

Maintains libraries of semantically related phrases organized into
neurodivergent-specific distress categories. Detects the presence
of these semantic fields in user messages with confidence scoring.
"""

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Set

logger = logging.getLogger(__name__)


class KeywordSemanticField(Enum):
    """
    Semantic fields representing distinct flavors of neurodivergent distress.

    Each field maps to a set of keyword patterns. Multiple field activations
    compound the overall crisis confidence score.
    """
    NEGATIVE_SELF_TALK = "negative_self_talk"
    TASK_AVOIDANCE = "task_avoidance"
    OVERWHELM = "overwhelm"
    MELTDOWN = "meltdown"
    SHUTDOWN = "shutdown"
    HYPERFOCUS_LOOP = "hyperfocus_loop"
    SELF_HARM_RISK = "self_harm_risk"  # High-priority escalation trigger


# ============================================================================
# Semantic Field Libraries
# Anti-Gaslight design: patterns are chosen to detect distress signals
# without pathologizing normal human language.
# ============================================================================

_FIELD_PATTERNS: Dict[KeywordSemanticField, List[str]] = {
    KeywordSemanticField.NEGATIVE_SELF_TALK: [
        r"i hate myself",
        r"i('m| am) (so |really )?(worthless|useless|stupid|pathetic|awful|terrible|broken)",
        r"i('m| am) a failure",
        r"i always (mess|screw|f+uck) (up|everything)",
        r"i('m| am) the worst",
        r"i ruin everything",
        r"(nobody|no one) cares (about me|anymore)?",
        r"i (can't|cannot) do anything right",
        r"why am i (so |like this|like that)",
        r"i don't deserve",
        r"i('m| am) so (dumb|stupid|bad)",
        r"everything('s| is) my fault",
        r"i('m| am) not good enough",
        r"i('ve| have) ruined (it|everything|this)",
    ],
    KeywordSemanticField.TASK_AVOIDANCE: [
        r"(can'?t|cannot) start",
        r"(can'?t|cannot) (do|finish|begin|complete|get started)",
        r"don'?t know (how to |where to )?begin",
        r"(can'?t|cannot) make myself",
        r"(i'?ve? been|been) (procrastin|putting it off|avoiding)",
        r"(too hard|too difficult|too much)",
        r"(giving up|give up|gave up)",
        r"what'?s the point",
        r"can'?t (be|get) (motivated|started|going)",
        r"(paralyzed|paralysed)",
        r"(stuck|frozen) (on|with|at)",
    ],
    KeywordSemanticField.OVERWHELM: [
        r"too much (going on|happening|at once)",
        r"(can'?t|cannot) cope",
        r"(can'?t|cannot) handle (this|it|everything|anymore)",
        r"(drowning|overwhelm(ed|ing))",
        r"everything (is |feels )?(too much|overwhelming|impossible)",
        r"(spinning|spiraling|spiral(l)?ing)",
        r"(can'?t|cannot) breathe",
        r"(shutting down|shutdown|shut(ting)? down)",
        r"brain (is |feels )?(fried|overloaded|full|done)",
        r"(so many|too many) (things|tasks|thoughts)",
        r"(can'?t|cannot) think (straight|clearly)",
    ],
    KeywordSemanticField.MELTDOWN: [
        r"(melt(ing|ed|down)|meltdown)",
        r"(fall(ing|en) apart|falling to pieces)",
        r"(break(ing|down)|breakdown)",
        r"(can'?t|cannot) stop (crying|shaking|panicking)",
        r"(losing|lost) (it|control|my mind)",
        r"(freaking|flipping|losing) out",
        r"everything'?s (falling|crumbling|coming) apart",
        r"(complete|total|full) (meltdown|breakdown|collapse)",
    ],
    KeywordSemanticField.SHUTDOWN: [
        r"(shut(ting)? down|shutdown)",
        r"(completely |totally )?(blank|empty|numb|gone|void)",
        r"(can'?t|cannot) (feel|think|move|respond)",
        r"(dissociat(ing|ed)|dissociation)",
        r"(frozen|froze(n)?|freezing)",
        r"(checked out|checked off|not (here|present|real))",
        r"(going |feel(ing)? )(numb|blank|empty)",
        r"(words|thoughts) (won'?t|don'?t) come",
        r"(can'?t|cannot) find (words|the words)",
        r"(just|totally|completely) (done|gone|empty|blank)",
    ],
    KeywordSemanticField.HYPERFOCUS_LOOP: [
        r"(can'?t|cannot) stop (thinking|going back|focusing)",
        r"(stuck|looping) (in|on) (a loop|it|this)",
        r"(keep|keep on|keeps) (thinking|going back|looping|fixating)",
        r"(hyperfocus(ing|ed)?|hyperfixat(ing|ion|ed))",
        r"(rabbit hole|down a rabbit)",
        r"(obsess(ing|ed|ion)|obsessive)",
        r"(can'?t|cannot) (let it go|move on|stop|switch off)",
        r"(loop(ing|ed)?|spiral(l)?ing) (back|on|about)",
        r"(intrusive|unwanted) (thought|loop|fixation)",
    ],
    KeywordSemanticField.SELF_HARM_RISK: [
        r"(want to |going to |going to )(hurt|harm) (myself|me)",
        r"(self[- ]?harm|self[- ]?hurt|self[- ]?injur)",
        r"don'?t want to (be here|live|exist|continue)",
        r"(better off|world (is|would be) better) (without me|if i (was|were) gone)",
        r"(thinking about|thought about) (ending|stopping) (it|everything|my life)",
        r"(suicid(e|al|ity)|want to die)",
        r"(kill|end) myself",
    ],
}

# Confidence weights for each semantic field
_FIELD_CONFIDENCE_WEIGHTS: Dict[KeywordSemanticField, float] = {
    KeywordSemanticField.NEGATIVE_SELF_TALK: 0.15,
    KeywordSemanticField.TASK_AVOIDANCE: 0.10,
    KeywordSemanticField.OVERWHELM: 0.15,
    KeywordSemanticField.MELTDOWN: 0.25,
    KeywordSemanticField.SHUTDOWN: 0.20,
    KeywordSemanticField.HYPERFOCUS_LOOP: 0.10,
    KeywordSemanticField.SELF_HARM_RISK: 1.00,  # Always escalates to maximum
}


@dataclass
class KeywordMatch:
    """A single keyword pattern match within a semantic field."""
    field: KeywordSemanticField
    pattern: str
    matched_text: str
    position: int


@dataclass
class KeywordAnalysisResult:
    """Result of Layer 1 keyword/semantic field analysis."""
    detected_fields: List[KeywordSemanticField] = field(default_factory=list)
    matches: List[KeywordMatch] = field(default_factory=list)
    confidence_score: float = 0.0
    self_harm_detected: bool = False
    primary_field: KeywordSemanticField = None

    def has_field(self, semantic_field: KeywordSemanticField) -> bool:
        return semantic_field in self.detected_fields


class KeywordLayer:
    """
    CDE Layer 1: Keyword/Semantic Field Analysis.

    Scans user messages against curated semantic field libraries.
    Runs entirely locally with no external dependencies beyond Python stdlib.

    Design notes:
    - Patterns use case-insensitive regex for robustness.
    - The SELF_HARM_RISK field always forces maximum confidence.
    - Multiple field activations compound the confidence score (capped at 1.0).
    """

    def __init__(self):
        self._compiled_patterns: Dict[KeywordSemanticField, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance."""
        for field_type, patterns in _FIELD_PATTERNS.items():
            self._compiled_patterns[field_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

    def analyze(self, text: str) -> KeywordAnalysisResult:
        """
        Analyze text for semantic field matches.

        Args:
            text: User message text to analyze.

        Returns:
            KeywordAnalysisResult with detected fields and confidence score.
        """
        if not text or not text.strip():
            return KeywordAnalysisResult()

        detected_fields: List[KeywordSemanticField] = []
        all_matches: List[KeywordMatch] = []
        field_match_counts: Dict[KeywordSemanticField, int] = {}

        for field_type, patterns in self._compiled_patterns.items():
            matches_for_field = []
            for i, pattern in enumerate(patterns):
                match = pattern.search(text)
                if match:
                    matches_for_field.append(
                        KeywordMatch(
                            field=field_type,
                            pattern=_FIELD_PATTERNS[field_type][i],
                            matched_text=match.group(0),
                            position=match.start(),
                        )
                    )

            if matches_for_field:
                detected_fields.append(field_type)
                field_match_counts[field_type] = len(matches_for_field)
                all_matches.extend(matches_for_field)

        # Compute confidence score
        confidence = self._compute_confidence(detected_fields, field_match_counts)
        self_harm = KeywordSemanticField.SELF_HARM_RISK in detected_fields

        # Determine primary field (highest weight * match count)
        primary = None
        if detected_fields:
            primary = max(
                detected_fields,
                key=lambda f: _FIELD_CONFIDENCE_WEIGHTS.get(f, 0.0) * field_match_counts.get(f, 1),
            )

        result = KeywordAnalysisResult(
            detected_fields=detected_fields,
            matches=all_matches,
            confidence_score=confidence,
            self_harm_detected=self_harm,
            primary_field=primary,
        )

        if self_harm:
            logger.warning("SELF_HARM_RISK field detected in keyword analysis")

        logger.debug(
            "Keyword analysis: fields=%s, confidence=%.3f",
            [f.value for f in detected_fields],
            confidence,
        )

        return result

    def _compute_confidence(
        self,
        detected_fields: List[KeywordSemanticField],
        field_match_counts: Dict[KeywordSemanticField, int],
    ) -> float:
        """
        Compute overall confidence score from detected fields.

        Self-harm detection always returns 1.0.
        Otherwise, compounds field weights with diminishing returns.
        """
        if KeywordSemanticField.SELF_HARM_RISK in detected_fields:
            return 1.0

        if not detected_fields:
            return 0.0

        total = 0.0
        for f in detected_fields:
            weight = _FIELD_CONFIDENCE_WEIGHTS.get(f, 0.10)
            # Multiple matches in same field add a small bonus
            count_bonus = min(0.05 * (field_match_counts.get(f, 1) - 1), 0.10)
            total += weight + count_bonus

        return min(1.0, total)
