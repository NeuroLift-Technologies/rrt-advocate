"""
MYRA — Original Guide: Relational Safety & Co-Regulation.

Myra provides relational safety, co-regulation, and anchors the
non-verbal "Silent Mode".  When the user selects "Don't know / Shut
down", Myra takes the lead with calm visuals and zero verbal demands.
"""

from __future__ import annotations

from typing import Any, Dict

from .persona_base import Persona, PersonaResponse


class Myra(Persona):

    @property
    def persona_id(self) -> str:
        return "myra"

    @property
    def display_name(self) -> str:
        return "Myra"

    @property
    def core_role(self) -> str:
        return "Provides relational safety, co-regulation, and anchors Silent Mode"

    SILENT_MODE_VISUALS = {
        "palette": "soft_gradient_blue_lavender",
        "animation": "slow_breathing_circle",
        "sound": "none",
        "timer_visible": False,
        "text_visible": False,
    }

    RESPONSES = {
        "supportive": {
            "shutdown": "",
            "meltdown": (
                "I'm here. You don't have to say anything. We can just "
                "sit together."
            ),
            "relational_distress": (
                "You're safe here. Whatever happened with them doesn't "
                "change your worth."
            ),
            "default": "I'm right here with you. No rush, no agenda.",
        },
        "minimal": {
            "shutdown": "",
            "meltdown": "I'm here.",
            "relational_distress": "You're safe.",
            "default": "Here with you.",
        },
        "directive": {
            "shutdown": "",
            "meltdown": "I'm present. No demands. Just here.",
            "relational_distress": "You are safe in this moment.",
            "default": "I'm here. Take what you need.",
        },
        "therapeutic": {
            "shutdown": "",
            "meltdown": (
                "I'm going to stay right here. There's nothing you need "
                "to do or say. Your presence is enough."
            ),
            "relational_distress": (
                "Relationships can stir up so much. Let's just breathe "
                "together for a moment."
            ),
            "default": (
                "I'd like to just be here with you. No questions, "
                "no expectations."
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

        is_silent = distress_type == "shutdown"

        visual_cues = dict(self.SILENT_MODE_VISUALS) if is_silent else {}

        return PersonaResponse(
            persona_id=self.persona_id,
            text=text,
            tone_tag=tone,
            suggested_actions=["co_regulate", "breathe_together", "silent_presence"],
            visual_cues=visual_cues,
            silent_mode=is_silent,
        )
