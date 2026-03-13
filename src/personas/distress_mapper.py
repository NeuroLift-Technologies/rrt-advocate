"""
Distress Mapper - Stage 2 Input → Persona Weights

Maps user-led tiered dialogue inputs to Persona Fusion Engine weights.
Reflects NLT Agency First: user describes their experience, system responds.
"""

from typing import Dict
from dataclasses import dataclass

# PersonaID/PERSONAE not used directly; kept for optional future use


@dataclass
class PersonaWeights:
    """Weights for each persona (0.0 to 1.0). Sum typically ~1.0."""
    ash: float = 0.0
    sol: float = 0.0
    echo: float = 0.0
    kai: float = 0.0
    myra: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "ash": self.ash,
            "sol": self.sol,
            "echo": self.echo,
            "kai": self.kai,
            "myra": self.myra,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> "PersonaWeights":
        return cls(
            ash=float(d.get("ash", 0)),
            sol=float(d.get("sol", 0)),
            echo=float(d.get("echo", 0)),
            kai=float(d.get("kai", 0)),
            myra=float(d.get("myra", 0)),
        )


# Stage 2 distress options → primary persona weights (from handoff spec)
STAGE2_DISTRESS_MAPPING = {
    # "Everything hurts / Meltdown" → Ash + Myra
    "everything_hurts": PersonaWeights(ash=0.45, sol=0.05, echo=0.1, kai=0.05, myra=0.35),
    "meltdown": PersonaWeights(ash=0.45, sol=0.05, echo=0.1, kai=0.05, myra=0.35),
    # "Can't do basic tasks" → Sol
    "cant_do_tasks": PersonaWeights(ash=0.1, sol=0.65, echo=0.1, kai=0.05, myra=0.1),
    "basic_tasks": PersonaWeights(ash=0.1, sol=0.65, echo=0.1, kai=0.05, myra=0.1),
    # "Can't stop self-blame" → Echo
    "self_blame": PersonaWeights(ash=0.15, sol=0.05, echo=0.65, kai=0.05, myra=0.1),
    "cant_stop_blame": PersonaWeights(ash=0.15, sol=0.05, echo=0.65, kai=0.05, myra=0.1),
    # "Stuck in hyperfocus/loop" → Kai
    "hyperfocus": PersonaWeights(ash=0.05, sol=0.1, echo=0.1, kai=0.65, myra=0.1),
    "stuck_loop": PersonaWeights(ash=0.05, sol=0.1, echo=0.1, kai=0.65, myra=0.1),
    # "Don't know / Shut down" → Myra (Silent Mode)
    "dont_know": PersonaWeights(ash=0.1, sol=0.05, echo=0.05, kai=0.05, myra=0.75),
    "shut_down": PersonaWeights(ash=0.1, sol=0.05, echo=0.05, kai=0.05, myra=0.75),
    "silent_mode": PersonaWeights(ash=0.05, sol=0.0, echo=0.0, kai=0.0, myra=0.95),
}

# Distress option IDs (from dialogue/distress_options) → PersonaWeights
OPTION_ID_TO_WEIGHTS: Dict[str, PersonaWeights] = {
    "everything_hurts_meltdown": PersonaWeights(ash=0.45, sol=0.05, echo=0.1, kai=0.05, myra=0.35),
    "cant_do_basic_tasks": PersonaWeights(ash=0.1, sol=0.65, echo=0.1, kai=0.05, myra=0.1),
    "cant_stop_self_blame": PersonaWeights(ash=0.15, sol=0.05, echo=0.65, kai=0.05, myra=0.1),
    "stuck_hyperfocus_loop": PersonaWeights(ash=0.05, sol=0.1, echo=0.1, kai=0.65, myra=0.1),
    "dont_know_shut_down": PersonaWeights(ash=0.1, sol=0.05, echo=0.05, kai=0.05, myra=0.75),
}


def get_persona_weights_for_distress(option_id: str) -> Dict[str, float]:
    """
    Map Stage 2 distress option ID to persona weights dict.
    Used by StageHandlers when user selects a distress option.
    """
    weights = OPTION_ID_TO_WEIGHTS.get(
        (option_id or "").strip().lower(),
        PersonaWeights(ash=0.2, sol=0.2, echo=0.2, kai=0.2, myra=0.2),
    )
    return weights.to_dict()


class DistressMapper:
    """
    Maps Stage 2 distress assessment inputs to persona weights.
    Uses normalized string matching for flexibility.
    """

    def __init__(self, custom_mapping: Dict[str, PersonaWeights] = None):
        self._mapping = dict(STAGE2_DISTRESS_MAPPING)
        if custom_mapping:
            self._mapping.update(custom_mapping)

    def map_input(self, user_input: str) -> PersonaWeights:
        """
        Map user distress description to persona weights.
        Input is normalized (lowercase, strip) and matched to known keys.
        """
        normalized = user_input.lower().strip()
        # Direct key match
        if normalized in self._mapping:
            return self._mapping[normalized]

        # Keyword substring matching
        for key, weights in self._mapping.items():
            if key.replace("_", " ") in normalized or key in normalized.replace(" ", "_"):
                return weights

        # Semantic heuristics for common phrasings
        if any(w in normalized for w in ["hurt", "meltdown", "overwhelm", "everything"]):
            return STAGE2_DISTRESS_MAPPING["everything_hurts"]
        if any(w in normalized for w in ["cant do", "can't do", "basic task", "executive"]):
            return STAGE2_DISTRESS_MAPPING["cant_do_tasks"]
        if any(w in normalized for w in ["self-blame", "blame", "guilty", "wrong"]):
            return STAGE2_DISTRESS_MAPPING["self_blame"]
        if any(w in normalized for w in ["hyperfocus", "loop", "stuck", "fixat"]):
            return STAGE2_DISTRESS_MAPPING["hyperfocus"]
        if any(w in normalized for w in ["don't know", "dont know", "shut down", "blank", "numb"]):
            return STAGE2_DISTRESS_MAPPING["dont_know"]

        # Default: balanced, slightly Myra-led (safest for unknown states)
        return PersonaWeights(ash=0.2, sol=0.2, echo=0.2, kai=0.2, myra=0.2)

    def get_silent_mode_weights(self) -> PersonaWeights:
        """Explicit Silent Mode: calm visuals, no timers, Myra-heavy."""
        return STAGE2_DISTRESS_MAPPING["silent_mode"]
