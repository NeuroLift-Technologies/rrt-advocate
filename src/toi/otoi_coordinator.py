"""
OTOI Coordinator — Orchestrated Terms of Interaction.

Ensures that the Persona Fusion Engine respects the TOI contract when
deciding *which* personas speak, in *what order*, and with *what weight*.
No single persona may override the user's explicit interaction contract.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .toi_config import TOIConfig, TonePreference, SafetyBoundary

logger = logging.getLogger(__name__)


@dataclass
class PersonaDirective:
    """Instructions the OTOI sends to the Fusion Engine for one persona."""
    persona_id: str
    permitted: bool
    weight_cap: float = 1.0
    tone_override: Optional[TonePreference] = None
    notes: List[str] = field(default_factory=list)


class OTOICoordinator:
    """
    Sits between the TOI config and the Fusion Engine.  For every
    interaction cycle it produces a set of PersonaDirectives that the
    Fusion Engine must honour.
    """

    TONE_PERSONA_AFFINITY: Dict[TonePreference, Dict[str, float]] = {
        TonePreference.SUPPORTIVE: {
            "ash": 1.0, "sol": 0.7, "echo": 0.9, "kai": 0.6, "myra": 1.0,
        },
        TonePreference.MINIMAL: {
            "ash": 0.5, "sol": 0.9, "echo": 0.4, "kai": 0.8, "myra": 0.6,
        },
        TonePreference.DIRECTIVE: {
            "ash": 0.4, "sol": 1.0, "echo": 0.5, "kai": 1.0, "myra": 0.3,
        },
        TonePreference.THERAPEUTIC: {
            "ash": 1.0, "sol": 0.5, "echo": 1.0, "kai": 0.4, "myra": 0.8,
        },
    }

    def __init__(self, toi: TOIConfig) -> None:
        self.toi = toi

    def generate_directives(
        self,
        requested_weights: Dict[str, float],
    ) -> List[PersonaDirective]:
        """
        Produce a list of OTOI-approved directives for the Fusion Engine.

        ``requested_weights`` are the raw weights the dialogue-tree or
        CDE has calculated.  The coordinator clips them against the TOI.
        """
        directives: List[PersonaDirective] = []
        affinity = self.TONE_PERSONA_AFFINITY.get(
            self.toi.tone, self.TONE_PERSONA_AFFINITY[TonePreference.SUPPORTIVE]
        )

        for persona_id, raw_weight in requested_weights.items():
            pid = persona_id.lower()
            permitted = self.toi.persona_allowed(pid)

            if not permitted:
                directives.append(
                    PersonaDirective(
                        persona_id=pid,
                        permitted=False,
                        weight_cap=0.0,
                        notes=[f"Blocked by TOI allowed_personas"],
                    )
                )
                continue

            tone_cap = affinity.get(pid, 0.5)
            effective_cap = min(raw_weight, tone_cap)

            if self.toi.boundary_active(SafetyBoundary.NO_PRODUCTIVITY_FRAMING):
                if pid == "sol":
                    effective_cap = min(effective_cap, 0.5)

            if self.toi.boundary_active(SafetyBoundary.SILENT_MODE_ONLY):
                if pid != "myra":
                    effective_cap = 0.0

            directives.append(
                PersonaDirective(
                    persona_id=pid,
                    permitted=True,
                    weight_cap=round(effective_cap, 3),
                    tone_override=self.toi.tone,
                )
            )

        return directives

    def validate_fusion_output(
        self,
        persona_contributions: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Post-fusion validation.  Clips any persona contribution that
        would exceed the OTOI-approved cap.  Returns adjusted weights.
        """
        directives = self.generate_directives(persona_contributions)
        validated: Dict[str, float] = {}
        for d in directives:
            if not d.permitted:
                validated[d.persona_id] = 0.0
            else:
                validated[d.persona_id] = min(
                    persona_contributions.get(d.persona_id, 0.0),
                    d.weight_cap,
                )
        return validated
