"""
OTOI Coordinator - Orchestrated Terms of Interaction
RRT Advocate - Protective Layer of the Solidarity Framework

Coordinates which personas speak; ensures no single persona overrides
the user's explicit interaction contract.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from .toi_parser import TOIConfig, TonePreference

logger = logging.getLogger(__name__)

VALID_PERSONAS = {"ash", "sol", "echo", "kai", "myra"}


@dataclass
class PersonaPermission:
    """Permission for a persona to speak under OTOI"""
    persona: str
    weight: float
    allowed: bool
    reason: Optional[str] = None


class OTOICoordinator:
    """
    Orchestrates persona activation per user's TOI.
    Ensures persona blend respects allowed_personas and tone preferences.
    """

    # Tone → preferred personas (for soft guidance, not hard blocks)
    TONE_PERSONA_PREFERENCES = {
        TonePreference.SUPPORTIVE_DEFAULT: ["ash", "echo", "myra"],
        TonePreference.MINIMAL: ["sol", "kai"],
        TonePreference.DIRECTIVE: ["sol", "kai"],
        TonePreference.THERAPEUTIC_REFLECTIVE: ["ash", "echo"],
    }

    def __init__(self, toi_config: Optional[TOIConfig] = None):
        self.toi_config = toi_config

    def filter_persona_weights(
        self, persona_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Filter persona weights against TOI allowed_personas.
        Zero out any persona not in allowed list.
        """
        if not self.toi_config or not self.toi_config.allowed_personas:
            return persona_weights

        allowed = set(p.lower() for p in self.toi_config.allowed_personas)
        filtered = {k: v for k, v in persona_weights.items() if k.lower() in allowed}

        # Renormalize if we dropped personas
        total = sum(filtered.values())
        if total > 0 and total != 1.0:
            filtered = {k: v / total for k, v in filtered.items()}

        return filtered

    def get_persona_permissions(
        self, persona_weights: Dict[str, float]
    ) -> List[PersonaPermission]:
        """Get permission status for each persona under OTOI."""
        filtered = self.filter_persona_weights(persona_weights)
        result = []
        for persona, weight in filtered.items():
            if persona.lower() not in VALID_PERSONAS:
                result.append(PersonaPermission(persona, weight, False, "Unknown persona"))
            elif self.toi_config and self.toi_config.allowed_personas:
                allowed = persona.lower() in [p.lower() for p in self.toi_config.allowed_personas]
                result.append(
                    PersonaPermission(persona, weight, allowed, None if allowed else "Not in TOI allowed_personas")
                )
            else:
                result.append(PersonaPermission(persona, weight, True, None))
        return result

    def suggest_tone_for_personas(
        self, primary_personas: List[str]
    ) -> Optional[TonePreference]:
        """
        Suggest a tone profile based on which personas are primary.
        Used when tone isn't explicitly set in TOI.
        """
        if not primary_personas:
            return TonePreference.SUPPORTIVE_DEFAULT

        # Sol/Kai → Directive; Ash/Echo → Therapeutic; Myra → Supportive
        if any(p in ("sol", "kai") for p in primary_personas):
            return TonePreference.DIRECTIVE
        if any(p in ("ash", "echo") for p in primary_personas):
            return TonePreference.THERAPEUTIC_REFLECTIVE
        if "myra" in primary_personas:
            return TonePreference.SUPPORTIVE_DEFAULT

        return TonePreference.SUPPORTIVE_DEFAULT
