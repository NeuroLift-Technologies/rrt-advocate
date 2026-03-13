"""
Persona Fusion Engine — translates distress inputs into dynamic persona blends.

The engine takes a distress_type (from the Tiered Dialogue Tree's Stage 2
assessment) and an optional raw_text signal, then computes a PersonaWeights
object via a three-step process:

  1. Canonical distress-type mapping (the 5 Stage-2 inputs from the brief).
  2. Semantic signal boosting (keyword proximity across each persona's
     distress_signals vocabulary).
  3. TOI preference boosting (the user's preferred_personas get a small lift).

All weights are normalised before being returned.
"""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from .models import PERSONAS, Persona, PersonaBlend, PersonaWeights

if TYPE_CHECKING:
    from ..toi.models import TOIConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical distress-type → base weight mappings (Stage 2 dialogue tree)
# ---------------------------------------------------------------------------
_CANONICAL_WEIGHTS: dict[str, PersonaWeights] = {
    # "Everything hurts / Meltdown" → heavily ASH + MYRA
    "meltdown": PersonaWeights(ash=0.45, sol=0.05, echo=0.10, kai=0.05, myra=0.35),
    # "Can't do basic tasks" → heavily SOL
    "task_paralysis": PersonaWeights(ash=0.15, sol=0.55, echo=0.10, kai=0.10, myra=0.10),
    # "Can't stop self-blame" → heavily ECHO
    "self_blame": PersonaWeights(ash=0.20, sol=0.05, echo=0.55, kai=0.05, myra=0.15),
    # "Stuck in hyperfocus / loop" → heavily KAI
    "hyperfocus_loop": PersonaWeights(ash=0.10, sol=0.15, echo=0.10, kai=0.55, myra=0.10),
    # "Don't know / Shut down" → heavily MYRA, trigger Silent Mode
    "shutdown": PersonaWeights(ash=0.15, sol=0.05, echo=0.05, kai=0.05, myra=0.70),
    # Fallback / unrecognised
    "unknown": PersonaWeights(ash=0.20, sol=0.20, echo=0.20, kai=0.20, myra=0.20),
}

# Aliases that map raw user input phrases to canonical distress types
_INPUT_ALIASES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"everything hurts|meltdown|overwhelm", re.I), "meltdown"),
    (re.compile(r"can'?t do.*(task|basic|thing)|basic task", re.I), "task_paralysis"),
    (re.compile(r"can'?t stop.*(blame|blame)|self.?blame|it'?s my fault", re.I), "self_blame"),
    (re.compile(r"hyper.?focus|stuck.*(loop|thought)|can'?t stop thinking", re.I), "hyperfocus_loop"),
    (re.compile(r"shut.?down|don'?t know|freeze|can'?t speak|blank", re.I), "shutdown"),
]

# Small keyword-proximity boost weights per persona (applied on top of canonical)
_SEMANTIC_BOOSTS: dict[str, float] = {
    "burnout": 0.05,
    "shame": 0.05,
    "exhausted": 0.03,
    "paralysis": 0.04,
    "rumination": 0.04,
    "loop": 0.04,
    "intrusive": 0.03,
    "freeze": 0.04,
    "overwhelmed": 0.03,
}


class FusionEngine:
    """
    Blends the five NLT personas into a weighted PersonaBlend.

    Usage
    -----
    engine = FusionEngine()
    blend  = engine.compute(
        distress_input="Can't stop self-blame",
        raw_text="I keep telling myself I'm worthless",
        toi_config=user_toi,
    )
    """

    def __init__(self, preferred_persona_boost: float = 0.08) -> None:
        self._preferred_boost = preferred_persona_boost

    def compute(
        self,
        distress_input: str,
        raw_text: str = "",
        toi_config: "TOIConfig | None" = None,
    ) -> PersonaBlend:
        """
        Compute a PersonaBlend for the given distress context.

        Parameters
        ----------
        distress_input:
            The user's Stage-2 selection or a free-text phrase describing
            their current experience.
        raw_text:
            Optional additional context (e.g. the raw user message) used
            for semantic boosting.
        toi_config:
            The user's TOI; used to apply preference boosts and muting.
        """
        distress_type = self._classify(distress_input)
        base = _CANONICAL_WEIGHTS.get(distress_type, _CANONICAL_WEIGHTS["unknown"])

        weights = PersonaWeights(
            ash=base.ash,
            sol=base.sol,
            echo=base.echo,
            kai=base.kai,
            myra=base.myra,
        )

        # Semantic boosting from raw text
        if raw_text:
            weights = self._apply_semantic_boosts(weights, distress_type, raw_text)

        # TOI preference boosting
        if toi_config:
            weights = self._apply_toi_boosts(weights, toi_config)

        normalised = weights.normalised()
        ranked = normalised.ranked()

        lead_name = ranked[0]
        lead_persona = PERSONAS[lead_name]
        contributors = [PERSONAS[n] for n in ranked[:2] if n in PERSONAS]

        rationale = self._build_rationale(distress_type, normalised, lead_persona)

        logger.debug(
            "FusionEngine | distress_type=%s | weights=%s | lead=%s",
            distress_type,
            normalised.as_dict(),
            lead_name,
        )

        return PersonaBlend(
            weights=normalised,
            lead_persona=lead_persona,
            contributing_personas=contributors,
            distress_type=distress_type,
            rationale=rationale,
        )

    def _classify(self, distress_input: str) -> str:
        """Map a raw distress input phrase to a canonical distress type."""
        # Accept canonical keys directly (e.g. when coming from the dialogue tree)
        if distress_input in _CANONICAL_WEIGHTS:
            return distress_input
        for pattern, canonical in _INPUT_ALIASES:
            if pattern.search(distress_input):
                return canonical
        return "unknown"

    def _apply_semantic_boosts(
        self,
        weights: PersonaWeights,
        distress_type: str,
        text: str,
    ) -> PersonaWeights:
        """
        Scan the combined distress_input + raw_text for keyword proximity and
        add small boosts to the most relevant personas.
        """
        text_lower = text.lower()
        ash_boost = sol_boost = echo_boost = kai_boost = myra_boost = 0.0

        for keyword, boost in _SEMANTIC_BOOSTS.items():
            if keyword in text_lower:
                persona = self._keyword_to_persona(keyword, distress_type)
                if persona == "ASH":
                    ash_boost += boost
                elif persona == "SOL":
                    sol_boost += boost
                elif persona == "ECHO":
                    echo_boost += boost
                elif persona == "KAI":
                    kai_boost += boost
                elif persona == "MYRA":
                    myra_boost += boost

        return PersonaWeights(
            ash=weights.ash + ash_boost,
            sol=weights.sol + sol_boost,
            echo=weights.echo + echo_boost,
            kai=weights.kai + kai_boost,
            myra=weights.myra + myra_boost,
        )

    def _keyword_to_persona(self, keyword: str, distress_type: str) -> str:
        """Route a keyword to its primary persona, informed by the distress type."""
        mapping: dict[str, str] = {
            "burnout": "ASH",
            "shame": "ASH",
            "exhausted": "ASH",
            "paralysis": "SOL",
            "rumination": "ECHO",
            "loop": "KAI",
            "intrusive": "ECHO",
            "freeze": "MYRA",
            "overwhelmed": "MYRA",
        }
        return mapping.get(keyword, "ASH")

    def _apply_toi_boosts(
        self,
        weights: PersonaWeights,
        toi_config: "TOIConfig",
    ) -> PersonaWeights:
        """Apply a small lift to user-preferred personas and zero-out muted ones."""
        boost = self._preferred_boost
        preferred = {p.upper() for p in toi_config.preferred_personas}
        muted = {p.upper() for p in toi_config.persona_mute_list}

        return PersonaWeights(
            ash=(weights.ash + boost if "ASH" in preferred else weights.ash) * (0.0 if "ASH" in muted else 1.0),
            sol=(weights.sol + boost if "SOL" in preferred else weights.sol) * (0.0 if "SOL" in muted else 1.0),
            echo=(weights.echo + boost if "ECHO" in preferred else weights.echo) * (0.0 if "ECHO" in muted else 1.0),
            kai=(weights.kai + boost if "KAI" in preferred else weights.kai) * (0.0 if "KAI" in muted else 1.0),
            myra=(weights.myra + boost if "MYRA" in preferred else weights.myra) * (0.0 if "MYRA" in muted else 1.0),
        )

    def _build_rationale(
        self,
        distress_type: str,
        weights: PersonaWeights,
        lead: Persona,
    ) -> str:
        ranked = weights.ranked()
        top_two = " + ".join(ranked[:2]) if len(ranked) >= 2 else ranked[0]
        return (
            f"Distress type '{distress_type}' → lead persona {lead.name} "
            f"(blend: {top_two}).  {lead.mandate}"
        )
