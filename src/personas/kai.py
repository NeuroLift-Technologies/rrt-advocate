"""
KAI — Original Guide for hyperfocus redirection.

Redirects hyperfocus and fixation into constructive pathways.
"""

from __future__ import annotations

from typing import Any, Dict

from src.models import PersonaName, PersonaResponse, ToneProfile
from src.personas.base import BasePersona

_MESSAGES: Dict[ToneProfile, str] = {
    ToneProfile.SUPPORTIVE: (
        "I see you're locked in. That laser-focus is actually a super-power "
        "— it just needs a slight course correction. Let's gently redirect "
        "that energy somewhere it'll serve you."
    ),
    ToneProfile.MINIMAL: (
        "You're looping. Pause. Breathe. Choose one new direction."
    ),
    ToneProfile.DIRECTIVE: (
        "Stop the loop now. Stand up or change position. Write down what "
        "you were fixating on, then choose one constructive action."
    ),
    ToneProfile.THERAPEUTIC: (
        "Hyperfocus can feel like being pulled by a current. What would it "
        "feel like to step onto the bank for a moment and watch the stream "
        "instead of being in it?"
    ),
}


class KaiPersona(BasePersona):
    name = PersonaName.KAI

    def generate(
        self,
        context: Dict[str, Any],
        tone: ToneProfile,
        weight: float,
    ) -> PersonaResponse:
        msg = _MESSAGES.get(tone, _MESSAGES[ToneProfile.SUPPORTIVE])
        return self._make_response(msg, tone, weight, domain="hyperfocus_redirection")
