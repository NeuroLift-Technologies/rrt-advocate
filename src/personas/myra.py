"""
MYRA — Original Guide for relational safety.

Provides relational safety, co-regulation, and anchors the non-verbal
"Silent Mode" (calm visuals, no timers, no task prompts).
"""

from __future__ import annotations

from typing import Any, Dict

from src.models import PersonaName, PersonaResponse, ToneProfile
from src.personas.base import BasePersona

_MESSAGES: Dict[ToneProfile, str] = {
    ToneProfile.SUPPORTIVE: (
        "I'm right here with you. You don't need to explain anything or "
        "perform for anyone. Just breathe. I'm not going anywhere."
    ),
    ToneProfile.MINIMAL: "I'm here. No words needed.",
    ToneProfile.DIRECTIVE: (
        "Ground yourself: feel your feet on the floor. I'm here, steady "
        "and present. You're safe."
    ),
    ToneProfile.THERAPEUTIC: (
        "Sometimes the bravest thing is to let someone sit with you in "
        "the quiet. I'm here for that. What does your body need right now?"
    ),
}

_SILENT_MODE_MESSAGE = (
    "I'm here. No words needed. Take all the time you need."
)


class MyraPersona(BasePersona):
    name = PersonaName.MYRA

    def generate(
        self,
        context: Dict[str, Any],
        tone: ToneProfile,
        weight: float,
    ) -> PersonaResponse:
        silent = context.get("silent_mode", False)
        if silent:
            return self._make_response(
                _SILENT_MODE_MESSAGE, tone, weight,
                domain="relational_safety", silent_mode=True,
                no_timers=True, visuals="calm",
            )
        msg = _MESSAGES.get(tone, _MESSAGES[ToneProfile.SUPPORTIVE])
        return self._make_response(msg, tone, weight, domain="relational_safety")
