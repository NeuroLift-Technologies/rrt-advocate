"""
Stage Handlers — backend mapping from Stage 2 distress-assessment
inputs to Persona Fusion Engine weights.

Each handler corresponds to a specific user-selected distress flavour
and returns the pre-computed persona weight profile.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from ..personas.fusion_engine import PersonaWeights


STAGE2_WEIGHT_MAP: Dict[str, PersonaWeights] = {
    "meltdown": PersonaWeights(ash=0.9, sol=0.1, echo=0.2, kai=0.0, myra=0.8),

    "cant_do_tasks": PersonaWeights(ash=0.2, sol=0.9, echo=0.1, kai=0.2, myra=0.1),

    "self_blame": PersonaWeights(ash=0.3, sol=0.1, echo=0.9, kai=0.0, myra=0.2),

    "hyperfocus_loop": PersonaWeights(ash=0.1, sol=0.2, echo=0.1, kai=0.9, myra=0.1),

    "shutdown": PersonaWeights(ash=0.2, sol=0.0, echo=0.0, kai=0.0, myra=1.0),
}

INPUT_ALIASES: Dict[str, str] = {
    "everything hurts": "meltdown",
    "everything hurts / meltdown": "meltdown",
    "meltdown": "meltdown",

    "can't do basic tasks": "cant_do_tasks",
    "cant do basic tasks": "cant_do_tasks",
    "cant_do_tasks": "cant_do_tasks",

    "can't stop self-blame": "self_blame",
    "cant stop self-blame": "self_blame",
    "self_blame": "self_blame",
    "self-blame": "self_blame",

    "stuck in hyperfocus/loop": "hyperfocus_loop",
    "stuck in hyperfocus": "hyperfocus_loop",
    "hyperfocus_loop": "hyperfocus_loop",
    "hyperfocus": "hyperfocus_loop",

    "don't know / shut down": "shutdown",
    "dont know / shut down": "shutdown",
    "don't know": "shutdown",
    "shut down": "shutdown",
    "shutdown": "shutdown",
}


class StageHandlers:
    """
    Resolves a user's distress-selection string into a canonical
    distress type and the corresponding persona weights.
    """

    def __init__(self) -> None:
        self.weight_map = dict(STAGE2_WEIGHT_MAP)
        self.aliases = dict(INPUT_ALIASES)

    def resolve_input(self, raw_input: str) -> str:
        """Normalise free-form user input to a canonical distress key."""
        normalised = raw_input.strip().lower()
        return self.aliases.get(normalised, "meltdown")

    def get_weights(self, raw_input: str) -> PersonaWeights:
        key = self.resolve_input(raw_input)
        return PersonaWeights.from_dict(
            self.weight_map.get(key, STAGE2_WEIGHT_MAP["meltdown"]).as_dict()
        )

    def get_distress_context(self, raw_input: str) -> Dict[str, Any]:
        """Build a distress_context dict suitable for the Fusion Engine."""
        key = self.resolve_input(raw_input)
        return {
            "distress_type": key,
            "raw_input": raw_input,
            "silent_mode": key == "shutdown",
        }
