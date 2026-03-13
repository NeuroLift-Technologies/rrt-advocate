"""
Persona Fusion Engine — dynamically blends the five Original Guides.

Instead of raw severity driving a single-track response, the Fusion Engine
uses modular weights (0.0–1.0) for each persona, determined by the specific
flavour of neurodivergent distress the user is experiencing.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from src.models import (
    DistressInput,
    FusedResponse,
    PersonaName,
    PersonaResponse,
    PersonaWeights,
    TOIConfig,
    ToneProfile,
)
from src.personas.ash import AshPersona
from src.personas.echo import EchoPersona
from src.personas.kai import KaiPersona
from src.personas.myra import MyraPersona
from src.personas.sol import SolPersona
from src.toi.governance import GovernanceMiddleware

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Distress → Persona weight mapping (Stage 2 of the Dialogue Tree)
# ---------------------------------------------------------------------------

DISTRESS_WEIGHT_MAP: Dict[DistressInput, PersonaWeights] = {
    DistressInput.MELTDOWN: PersonaWeights(
        ash=0.8, sol=0.05, echo=0.05, kai=0.0, myra=0.8
    ),
    DistressInput.TASK_PARALYSIS: PersonaWeights(
        ash=0.1, sol=0.85, echo=0.1, kai=0.1, myra=0.1
    ),
    DistressInput.SELF_BLAME: PersonaWeights(
        ash=0.15, sol=0.05, echo=0.85, kai=0.0, myra=0.15
    ),
    DistressInput.HYPERFOCUS_LOOP: PersonaWeights(
        ash=0.05, sol=0.1, echo=0.05, kai=0.85, myra=0.05
    ),
    DistressInput.SHUTDOWN: PersonaWeights(
        ash=0.1, sol=0.0, echo=0.0, kai=0.0, myra=1.0
    ),
}


class FusionEngine:
    """
    Generates blended persona responses driven by distress-type weights.

    The engine:
      1. Maps the distress input to a PersonaWeights vector.
      2. Asks each persona whose weight > 0 to generate a contribution.
      3. Passes everything through the GovernanceMiddleware for TOI compliance.
    """

    def __init__(self, governance: GovernanceMiddleware):
        self._governance = governance
        self._personas = {
            PersonaName.ASH: AshPersona(),
            PersonaName.SOL: SolPersona(),
            PersonaName.ECHO: EchoPersona(),
            PersonaName.KAI: KaiPersona(),
            PersonaName.MYRA: MyraPersona(),
        }

    def resolve_weights(self, distress: DistressInput) -> PersonaWeights:
        return DISTRESS_WEIGHT_MAP.get(
            distress,
            PersonaWeights(),
        )

    def generate(
        self,
        distress: DistressInput,
        context: Dict[str, Any] | None = None,
        weight_override: PersonaWeights | None = None,
    ) -> FusedResponse:
        """
        Produce a fully governed, blended response for the given distress.

        Parameters
        ----------
        distress : DistressInput
            The user's self-reported distress flavour (Stage 2 input).
        context : dict, optional
            Extra context forwarded to each persona's ``generate()``.
        weight_override : PersonaWeights, optional
            Bypass the default distress→weight mapping.
        """
        context = context or {}
        weights = weight_override if weight_override else self.resolve_weights(distress)
        tone = self._governance.toi.tone
        silent_mode = distress == DistressInput.SHUTDOWN

        if silent_mode:
            context["silent_mode"] = True

        contributions = self._collect_contributions(weights, context, tone)

        return self._governance.process(
            contributions=contributions,
            weights=weights,
            silent_mode=silent_mode,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _collect_contributions(
        self,
        weights: PersonaWeights,
        context: Dict[str, Any],
        tone: ToneProfile,
    ) -> List[PersonaResponse]:
        weight_map = weights.as_dict()
        results: List[PersonaResponse] = []
        for persona_name, persona in self._personas.items():
            w = weight_map.get(persona_name.value, 0.0)
            if w > 0.0:
                resp = persona.generate(context, tone, w)
                results.append(resp)
        return results
