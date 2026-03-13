"""
ASH — Original Guide for burnout validation.

Validates burnout, diffuses shame, prioritises "being" over "doing".
"""

from __future__ import annotations

from typing import Any, Dict

from src.models import PersonaName, PersonaResponse, ToneProfile
from src.personas.base import BasePersona

_MESSAGES: Dict[ToneProfile, str] = {
    ToneProfile.SUPPORTIVE: (
        "You're allowed to feel exhausted. Burnout isn't a character flaw — "
        "it's your nervous system telling you it needs rest. You don't have "
        "to earn the right to pause."
    ),
    ToneProfile.MINIMAL: "Rest is valid. You're allowed to stop.",
    ToneProfile.DIRECTIVE: (
        "Step back from the task list. Right now, the only goal is to exist "
        "without judgment. Nothing needs doing this moment."
    ),
    ToneProfile.THERAPEUTIC: (
        "I notice how heavy things feel right now. That heaviness isn't "
        "weakness — it's information. What would it feel like to set the "
        "weight down, even for a moment?"
    ),
}


class AshPersona(BasePersona):
    name = PersonaName.ASH

    def generate(
        self,
        context: Dict[str, Any],
        tone: ToneProfile,
        weight: float,
    ) -> PersonaResponse:
        msg = _MESSAGES.get(tone, _MESSAGES[ToneProfile.SUPPORTIVE])
        return self._make_response(msg, tone, weight, domain="burnout_validation")
