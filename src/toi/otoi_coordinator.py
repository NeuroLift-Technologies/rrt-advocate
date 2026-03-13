"""
OTOI Coordinator — Orchestrated Terms of Interaction.

Sits between the TOI layer and the Persona Fusion Engine.  Given a user's
TOI and the current distress context, it produces an OTOIDirective that
specifies exactly which personas may speak, in what order, and under what
constraints — ensuring no single persona overrides the user's interaction
contract.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .models import (
    InteractionContract,
    OTOIDirective,
    ToneProfile,
)

if TYPE_CHECKING:
    from ..personas.models import PersonaWeights

logger = logging.getLogger(__name__)


class OTOICoordinator:
    """
    The OTOI Coordinator enforces the user's interaction contract at runtime.

    It is called after persona weights have been computed by the Fusion Engine
    but *before* any response is assembled.  It may suppress, reorder, or
    tone-shift persona contributions based on the active TOI.
    """

    def produce_directive(
        self,
        contract: InteractionContract,
        persona_weights: "PersonaWeights",
        distress_type: str | None = None,
    ) -> OTOIDirective:
        """
        Generate an OTOIDirective from the current interaction state.

        Parameters
        ----------
        contract:
            The session's InteractionContract (wraps the user's TOI).
        persona_weights:
            The raw weights produced by the FusionEngine for this context.
        distress_type:
            Optional label describing the detected flavour of distress
            (e.g. 'shutdown', 'meltdown', 'hyperfocus').
        """
        toi = contract.toi

        ordered = persona_weights.ranked()
        permitted = [
            name for name in ordered if toi.is_persona_allowed(name)
        ]

        if not permitted:
            logger.warning(
                "All weighted personas are muted by the user's TOI.  "
                "Defaulting to MYRA for relational safety."
            )
            permitted = ["MYRA"]

        lead = permitted[0]

        silence_requested = (
            distress_type == "shutdown"
            and toi.safety_boundaries.silent_mode_eligible
        )

        tone_override: ToneProfile | None = None
        if toi.tone_profile == ToneProfile.MINIMAL:
            tone_override = ToneProfile.MINIMAL
        elif lead in ("ASH", "ECHO") and toi.tone_profile == ToneProfile.THERAPEUTIC_REFLECTIVE:
            tone_override = ToneProfile.THERAPEUTIC_REFLECTIVE
        elif lead in ("SOL", "KAI") and toi.tone_profile == ToneProfile.DIRECTIVE:
            tone_override = ToneProfile.DIRECTIVE

        max_personas = 1 if toi.tone_profile == ToneProfile.MINIMAL else 2

        consent_needed = (
            toi.safety_boundaries.require_explicit_consent
            and not contract.consent_granted
        )

        directive = OTOIDirective(
            permitted_personas=permitted[:max_personas],
            lead_persona=lead,
            max_personas_per_response=max_personas,
            tone_override=tone_override,
            scaffolding_override=toi.cognitive_scaffolding if toi.cognitive_scaffolding.chunking_enabled else None,
            silence_requested=silence_requested,
            consent_checkpoint_required=consent_needed,
        )

        logger.debug(
            "OTOIDirective produced | lead=%s | permitted=%s | tone=%s | consent_needed=%s",
            directive.lead_persona,
            directive.permitted_personas,
            directive.tone_override,
            directive.consent_checkpoint_required,
        )

        return directive

    def check_no_productivity_pressure(
        self,
        contract: InteractionContract,
        proposed_response: str,
    ) -> str:
        """
        Guard: if the user's TOI forbids productivity pressure and the
        proposed response contains pressure-laden language, strip it.
        Returns the (possibly cleaned) response string.
        """
        if not contract.toi.safety_boundaries.no_productivity_pressure:
            return proposed_response

        pressure_phrases = [
            "you should complete",
            "finish the task",
            "productivity goal",
            "get it done",
            "push through",
        ]
        cleaned = proposed_response
        for phrase in pressure_phrases:
            if phrase.lower() in cleaned.lower():
                logger.info("Removing productivity-pressure phrase: '%s'", phrase)
                cleaned = cleaned.replace(phrase, "")

        return cleaned.strip()
