"""
KAI — Original Guide: Hyperfocus Redirection.

Kai redirects hyperfocus and fixation into constructive pathways.
Kai never vilifies hyperfocus itself — it honours the energy while
gently steering it somewhere safer.
"""

from __future__ import annotations

from typing import Any, Dict

from .persona_base import Persona, PersonaResponse


class Kai(Persona):

    @property
    def persona_id(self) -> str:
        return "kai"

    @property
    def display_name(self) -> str:
        return "Kai"

    @property
    def core_role(self) -> str:
        return "Redirects hyperfocus and fixation into constructive pathways"

    RESPONSES = {
        "supportive": {
            "hyperfocus_loop": (
                "Your focus is powerful — let's point it somewhere that "
                "serves you right now instead of draining you. What's one "
                "thing that would feel good to redirect this energy toward?"
            ),
            "fixation": (
                "I can see you're locked in. That intensity is a strength, "
                "but right now it might be working against you. Let's "
                "channel it."
            ),
            "default": (
                "You've got a lot of mental energy right now. Let's find "
                "a good place for it."
            ),
        },
        "minimal": {
            "hyperfocus_loop": "Redirect the focus. Where does it help you most?",
            "fixation": "Locked in. Let's shift the target.",
            "default": "Channel the energy somewhere useful.",
        },
        "directive": {
            "hyperfocus_loop": (
                "Step back from the loop. Pick one constructive target for "
                "this energy. Set a 15-minute boundary."
            ),
            "fixation": (
                "Acknowledge the fixation. Choose an exit point. Move to a "
                "different context."
            ),
            "default": "Name what you're locked on. Decide where to redirect.",
        },
        "therapeutic": {
            "hyperfocus_loop": (
                "This loop has a lot of momentum. What do you think is "
                "keeping you inside it? What would it feel like to step "
                "outside, just for a moment?"
            ),
            "fixation": (
                "I wonder what need this fixation is trying to meet. "
                "Is there a gentler way to meet that need?"
            ),
            "default": (
                "What is this intensity telling you about what matters "
                "to you right now?"
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
            suggested_actions=["redirect", "boundary_set", "context_switch"],
        )
