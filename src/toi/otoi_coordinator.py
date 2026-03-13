"""
OTOI Coordinator — Orchestrated Terms of Interaction.

Ensures that persona contributions honour the user's TOI contract:
  * No single persona may exceed its allocated weight ceiling.
  * Silent Mode overrides all verbal personas in favour of Myra's non-verbal anchoring.
  * Tone consistency is enforced across every persona contribution.
"""

from __future__ import annotations

import logging
from typing import List

from src.models import (
    FusedResponse,
    PersonaName,
    PersonaResponse,
    PersonaWeights,
    TOIConfig,
    ToneProfile,
)

logger = logging.getLogger(__name__)

_WEIGHT_CEILING = 0.85


class OTOICoordinator:
    """Coordinate persona contributions under the user's TOI contract."""

    def __init__(self, toi: TOIConfig):
        self.toi = toi

    def enforce(
        self,
        contributions: List[PersonaResponse],
        weights: PersonaWeights,
        silent_mode: bool = False,
    ) -> FusedResponse:
        """
        Build a FusedResponse from raw persona contributions, applying
        TOI constraints and OTOI coordination rules.
        """
        if self.toi.persona_overrides is not None:
            weights = self.toi.persona_overrides

        weights = self._clamp_weights(weights)

        if silent_mode:
            return self._build_silent_response(contributions, weights)

        filtered = self._apply_tone_filter(contributions)
        ordered = self._order_by_weight(filtered, weights)
        primary_message = self._compose_primary_message(ordered, weights)

        return FusedResponse(
            tone=self.toi.tone,
            primary_message=primary_message,
            persona_contributions=ordered,
            weights_used=weights,
            silent_mode=False,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clamp_weights(weights: PersonaWeights) -> PersonaWeights:
        """Prevent any single persona from dominating the response."""
        clamped = PersonaWeights(
            ash=min(weights.ash, _WEIGHT_CEILING),
            sol=min(weights.sol, _WEIGHT_CEILING),
            echo=min(weights.echo, _WEIGHT_CEILING),
            kai=min(weights.kai, _WEIGHT_CEILING),
            myra=min(weights.myra, _WEIGHT_CEILING),
        )
        return clamped

    def _apply_tone_filter(
        self, contributions: List[PersonaResponse]
    ) -> List[PersonaResponse]:
        """Override each contribution's tone to match the user's TOI."""
        return [
            PersonaResponse(
                persona=c.persona,
                weight=c.weight,
                message=c.message,
                tone=self.toi.tone,
                metadata=c.metadata,
            )
            for c in contributions
        ]

    @staticmethod
    def _order_by_weight(
        contributions: List[PersonaResponse], weights: PersonaWeights
    ) -> List[PersonaResponse]:
        weight_map = weights.as_dict()
        return sorted(
            contributions,
            key=lambda c: weight_map.get(c.persona.value, 0.0),
            reverse=True,
        )

    @staticmethod
    def _compose_primary_message(
        ordered: List[PersonaResponse], weights: PersonaWeights
    ) -> str:
        """Weight-blend the ordered contributions into a single message."""
        weight_map = weights.as_dict()
        parts: list[str] = []
        for c in ordered:
            w = weight_map.get(c.persona.value, 0.0)
            if w > 0.0 and c.message:
                parts.append(c.message)
        return "\n\n".join(parts) if parts else ""

    def _build_silent_response(
        self,
        contributions: List[PersonaResponse],
        weights: PersonaWeights,
    ) -> FusedResponse:
        """
        Silent Mode: only Myra speaks (non-verbal anchoring).
        No timers, no task prompts — calm visuals only.
        """
        myra_msg = ""
        for c in contributions:
            if c.persona == PersonaName.MYRA:
                myra_msg = c.message
                break

        if not myra_msg:
            myra_msg = "I'm here. No words needed. Take all the time you need."

        return FusedResponse(
            tone=self.toi.tone,
            primary_message=myra_msg,
            persona_contributions=[
                PersonaResponse(
                    persona=PersonaName.MYRA,
                    weight=1.0,
                    message=myra_msg,
                    tone=self.toi.tone,
                )
            ],
            weights_used=PersonaWeights(ash=0, sol=0, echo=0, kai=0, myra=1.0),
            silent_mode=True,
            metadata={"no_timers": True, "visuals": "calm"},
        )
