"""
SOL — Original Guide for executive function scaffolding.

Scaffolds executive function, breaks down tasks, manages attention fatigue.
"""

from __future__ import annotations

from typing import Any, Dict

from src.models import PersonaName, PersonaResponse, ToneProfile
from src.personas.base import BasePersona

_MESSAGES: Dict[ToneProfile, str] = {
    ToneProfile.SUPPORTIVE: (
        "Let's shrink this down to something manageable. You don't need to "
        "see the whole staircase — just the next step. What's one tiny thing "
        "you could do in the next two minutes?"
    ),
    ToneProfile.MINIMAL: "One small step. That's all. What's the tiniest move?",
    ToneProfile.DIRECTIVE: (
        "Pick the single easiest task. Set a two-minute timer. Start there. "
        "Everything else can wait."
    ),
    ToneProfile.THERAPEUTIC: (
        "When everything feels equally urgent, nothing moves. Let's gently "
        "untangle this together — which thread feels the lightest to pull?"
    ),
}


class SolPersona(BasePersona):
    name = PersonaName.SOL

    def generate(
        self,
        context: Dict[str, Any],
        tone: ToneProfile,
        weight: float,
    ) -> PersonaResponse:
        msg = _MESSAGES.get(tone, _MESSAGES[ToneProfile.SUPPORTIVE])
        return self._make_response(msg, tone, weight, domain="executive_function")
