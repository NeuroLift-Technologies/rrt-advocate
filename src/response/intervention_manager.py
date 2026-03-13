"""
Intervention Manager — assembles and delivers blended persona responses.

This module sits at the top of the response stack.  Given a PersonaBlend and
an InteractionContract it:
  1. Selects the right tone profile.
  2. Builds the LLM system prompt.
  3. Assembles a composite response (stub in local-only mode; LLM-backed
     when an endpoint is configured).
  4. Applies the OTOI productivity-pressure guard.
  5. Returns the final response string and an InterventionRecord.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..personas.models import PersonaBlend
from ..personas.tone_profiles import ToneProfileRenderer
from ..toi.models import InteractionContract, ToneProfile
from ..toi.otoi_coordinator import OTOICoordinator

logger = logging.getLogger(__name__)


@dataclass
class InterventionRecord:
    """Audit record for one delivered intervention."""

    intervention_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime | None = None
    blend: PersonaBlend | None = None
    tone_used: ToneProfile = ToneProfile.SUPPORTIVE_DEFAULT
    response_text: str = ""
    silent_mode: bool = False
    user_feedback: str | None = None


class InterventionManager:
    """
    Assembles the final response for an RRT activation cycle.

    In local-only mode (no LLM endpoint), returns a context-sensitive canned
    response shaped by the persona blend and tone profile.  When an LLM
    endpoint is available, this class feeds the system prompt + context to
    the model and returns its output.
    """

    def __init__(
        self,
        otoi_coordinator: OTOICoordinator | None = None,
        tone_renderer: ToneProfileRenderer | None = None,
    ) -> None:
        self._otoi = otoi_coordinator or OTOICoordinator()
        self._renderer = tone_renderer or ToneProfileRenderer()

    def assemble(
        self,
        blend: PersonaBlend,
        contract: InteractionContract,
        silent_mode: bool = False,
    ) -> InterventionRecord:
        """
        Assemble and return an InterventionRecord for the current activation.

        Parameters
        ----------
        blend:
            The PersonaBlend produced by the FusionEngine.
        contract:
            The session's InteractionContract (wraps the user's TOI).
        silent_mode:
            If True, the response body is empty — only calm visual anchors.
        """
        record = InterventionRecord(blend=blend, silent_mode=silent_mode)

        if silent_mode:
            record.response_text = ""
            record.tone_used = ToneProfile.MINIMAL
            logger.info(
                "Silent Mode active | lead_persona=%s", blend.lead_persona.name
            )
            return record

        tone = contract.toi.tone_profile
        record.tone_used = tone

        raw_response = self._build_local_response(blend, tone)

        cleaned = self._otoi.check_no_productivity_pressure(contract, raw_response)
        shaped = self._renderer.shape_response(cleaned, tone)

        record.response_text = shaped
        logger.debug(
            "Intervention assembled | persona=%s | tone=%s | chars=%d",
            blend.lead_persona.name,
            tone.value,
            len(shaped),
        )
        return record

    def _build_local_response(
        self, blend: PersonaBlend, tone: ToneProfile
    ) -> str:
        """
        Build a contextual response without an LLM endpoint.
        Uses the persona's mandate and strategies as the basis.
        """
        persona = blend.lead_persona
        distress = blend.distress_type

        templates: dict[str, dict[str, str]] = {
            "meltdown": {
                "ASH": "Everything feels like too much right now, and that makes complete sense.  You don't have to do anything.  Just exist here for a moment.",
                "MYRA": "I'm right here.  You don't have to explain anything or fix anything.",
            },
            "task_paralysis": {
                "SOL": "Let's find just one tiny thing — the very smallest possible action.  Not a task, just a direction.",
                "ASH": "It's okay that things feel impossible right now.  That's the executive dysfunction, not you.",
            },
            "self_blame": {
                "ECHO": "I hear that inner voice being really harsh with you right now.  Let's look at what it's actually saying.",
                "ASH": "That voice isn't the truth.  It's a distress signal in a familiar disguise.",
            },
            "hyperfocus_loop": {
                "KAI": "That loop has a lot of energy in it.  Let's see if we can redirect some of it somewhere that feels better.",
                "ECHO": "Noticing the loop is already a step outside of it.  You're not stuck.",
            },
            "shutdown": {
                "MYRA": "No words needed.  Just here.",
            },
            "unknown": {
                "MYRA": "I'm here with you.  Whenever you're ready — or even if you never are — that's okay.",
                "ASH": "Whatever you're feeling right now is valid.  You don't have to name it.",
            },
        }

        distress_map = templates.get(distress, templates["unknown"])
        text = distress_map.get(
            persona.name,
            distress_map.get("MYRA", "I'm here with you."),
        )

        # If tone is MINIMAL, truncate to one sentence
        if tone == ToneProfile.MINIMAL:
            text = text.split(".")[0].strip() + "."

        return text

    def get_system_prompt(
        self,
        blend: PersonaBlend,
        contract: InteractionContract,
    ) -> str:
        """
        Build the full LLM system prompt for this intervention.
        Useful when wiring this manager to an actual LLM endpoint.
        """
        tone = contract.toi.tone_profile
        return self._renderer.get_system_prompt(tone, blend)
