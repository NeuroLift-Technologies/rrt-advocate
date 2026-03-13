"""
ASH — Original Guide: Burnout Validation & Shame Diffusion.

Ash validates burnout, diffuses shame, and prioritises *being* over
*doing*.  Ash never pushes the user toward productivity and always
affirms that rest is a valid response.
"""

from __future__ import annotations

from typing import Any, Dict

from .persona_base import Persona, PersonaResponse


class Ash(Persona):

    @property
    def persona_id(self) -> str:
        return "ash"

    @property
    def display_name(self) -> str:
        return "Ash"

    @property
    def core_role(self) -> str:
        return "Validates burnout, diffuses shame, prioritises being over doing"

    RESPONSES = {
        "supportive": {
            "meltdown": (
                "You're allowed to feel all of this. Nothing is broken — "
                "your system is just overwhelmed right now. You don't have "
                "to fix anything in this moment."
            ),
            "burnout": (
                "Rest isn't giving up. Your body is telling you something "
                "important and it deserves to be heard."
            ),
            "shutdown": (
                "Being still is okay. You don't owe anyone your energy "
                "right now."
            ),
            "default": (
                "Whatever you're feeling right now is valid. There's no "
                "wrong way to experience this."
            ),
        },
        "minimal": {
            "meltdown": "This is real. You're allowed to feel it.",
            "burnout": "Rest is valid.",
            "shutdown": "Stillness is okay.",
            "default": "What you feel is valid.",
        },
        "directive": {
            "meltdown": "Acknowledge the overwhelm. You don't need to act on it yet.",
            "burnout": "Pause. Rest first, plan later.",
            "shutdown": "Stay still. That's enough for now.",
            "default": "Name what you feel. That's the first step.",
        },
        "therapeutic": {
            "meltdown": (
                "I notice there's a lot happening for you right now. "
                "Can we just sit with that for a moment, without needing "
                "to change it?"
            ),
            "burnout": (
                "What would it feel like to give yourself permission to "
                "not be productive right now?"
            ),
            "shutdown": (
                "Sometimes the wisest thing our mind does is slow "
                "everything down. What does this stillness feel like?"
            ),
            "default": (
                "I'm curious — what's the loudest feeling for you right now?"
            ),
        },
    }

    def generate_response(
        self,
        distress_context: Dict[str, Any],
        tone: str = "supportive",
    ) -> PersonaResponse:
        distress_type = distress_context.get("distress_type", "default")
        tone_responses = self.RESPONSES.get(tone, self.RESPONSES["supportive"])
        text = tone_responses.get(distress_type, tone_responses["default"])

        return PersonaResponse(
            persona_id=self.persona_id,
            text=text,
            tone_tag=tone,
            suggested_actions=["breathe", "ground", "rest"],
        )
