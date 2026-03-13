"""
OTOI (Orchestrated TOI) Coordinator
Ensures no single persona overrides the user's explicit interaction contract.

Coordinates which personas speak and how they blend, per TOI.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from .toi_parser import TOIConfig, TOIParser, ToneProfile


@dataclass
class PersonaBlend:
    """Result of fusion: which personas speak and at what weights."""
    weights: Dict[str, float]  # ash, sol, echo, kai, myra
    primary_persona: str
    secondary_personas: List[str]
    silent_mode: bool  # True when Myra-dominant and nonverbal preferred


class OTOICoordinator:
    """
    Orchestrates persona selection against TOI.
    Receives PersonaBlend from Fusion Engine and applies TOI overrides.
    """

    def __init__(self, toi: TOIConfig):
        self.toi = toi

    def apply_toi_to_blend(
        self,
        base_blend: PersonaBlend,
        distress_input: Optional[str] = None,
    ) -> PersonaBlend:
        """
        Apply TOI persona_overrides to base blend from Fusion Engine.
        Ensures no persona exceeds user's explicit preferences.
        """
        weights = dict(base_blend.weights)
        overrides = self.toi.persona_overrides or {}

        for persona, override_val in overrides.items():
            if override_val is not None and persona in weights:
                # User has explicit preference: blend toward it
                weights[persona] = weights[persona] * 0.5 + override_val * 0.5

        # Normalize to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        # Respect silent_mode_available
        silent_mode = base_blend.silent_mode and self.toi.silent_mode_available

        # Recompute primary/secondary from adjusted weights
        sorted_personas = sorted(
            weights.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        primary = sorted_personas[0][0] if sorted_personas else "myra"
        secondary = [p for p, _ in sorted_personas[1:3]]

        return PersonaBlend(
            weights=weights,
            primary_persona=primary,
            secondary_personas=secondary,
            silent_mode=silent_mode,
        )

    def get_tone_profile(self) -> ToneProfile:
        """Return tone profile from TOI for prompt construction."""
        return self.toi.tone_profile

    def should_trigger_silent_mode(self, blend: PersonaBlend) -> bool:
        """Check if Silent Mode (calm visuals, no timers) should activate."""
        return (
            blend.silent_mode
            and self.toi.silent_mode_available
            and blend.weights.get("myra", 0) >= 0.5
        )
