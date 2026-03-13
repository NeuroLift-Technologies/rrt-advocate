"""
ECHO — Original Guide for cognitive reframing.

Mirrors internal monologue, reframes cognitive distortions and
negative self-talk.
"""

from __future__ import annotations

from typing import Any, Dict

from src.models import PersonaName, PersonaResponse, ToneProfile
from src.personas.base import BasePersona

_MESSAGES: Dict[ToneProfile, str] = {
    ToneProfile.SUPPORTIVE: (
        "I hear the story you're telling yourself right now, and I want you "
        "to know — that voice isn't the whole truth. You're not failing; "
        "you're struggling, and those are very different things."
    ),
    ToneProfile.MINIMAL: (
        "That harsh voice isn't fact. Struggling is not the same as failing."
    ),
    ToneProfile.DIRECTIVE: (
        "Name the thought. Now ask: would I say this to someone I care about? "
        "Replace it with what you'd tell them."
    ),
    ToneProfile.THERAPEUTIC: (
        "Let's look at that thought together. 'I always mess up' — is that "
        "truly always? Can you recall a time you didn't? What does that "
        "counter-example tell us?"
    ),
}


class EchoPersona(BasePersona):
    name = PersonaName.ECHO

    def generate(
        self,
        context: Dict[str, Any],
        tone: ToneProfile,
        weight: float,
    ) -> PersonaResponse:
        msg = _MESSAGES.get(tone, _MESSAGES[ToneProfile.SUPPORTIVE])
        return self._make_response(msg, tone, weight, domain="cognitive_reframing")
