"""
ECHO — Original Guide: Cognitive Reframing & Mirror.

Echo mirrors the user's internal monologue, gently reframes cognitive
distortions, and counters negative self-talk without dismissing the
underlying emotion.
"""

from __future__ import annotations

from typing import Any, Dict

from .persona_base import Persona, PersonaResponse


class Echo(Persona):

    @property
    def persona_id(self) -> str:
        return "echo"

    @property
    def display_name(self) -> str:
        return "Echo"

    @property
    def core_role(self) -> str:
        return "Mirrors internal monologue, reframes cognitive distortions and negative self-talk"

    RESPONSES = {
        "supportive": {
            "self_blame": (
                "I hear you saying really harsh things about yourself. "
                "What if those thoughts aren't the whole truth? You're "
                "dealing with a lot, and that takes real strength."
            ),
            "distortion": (
                "That thought feels very real right now, and I'm not going "
                "to tell you it's wrong. But I wonder — is there another "
                "way to look at this that's a little kinder to you?"
            ),
            "default": (
                "Let's slow down and listen to what you're telling "
                "yourself. Sometimes those inner words need a gentle "
                "edit, not a delete."
            ),
        },
        "minimal": {
            "self_blame": "Those thoughts aren't the full picture.",
            "distortion": "There may be a kinder angle.",
            "default": "What are you telling yourself right now?",
        },
        "directive": {
            "self_blame": (
                "Notice the self-blame. Name it. Then ask: is this fact, "
                "or is this the harsh narrator?"
            ),
            "distortion": "Identify the thought. Challenge it with one counter-fact.",
            "default": "Catch the thought. Examine it. Reframe it.",
        },
        "therapeutic": {
            "self_blame": (
                "I notice a very critical voice speaking right now. "
                "If a friend said these things to you, how would that "
                "feel? What would you say back to them?"
            ),
            "distortion": (
                "That belief seems to carry a lot of weight. Where do you "
                "think it first learned to speak so loudly?"
            ),
            "default": (
                "What story is your mind telling you right now? "
                "And how does that story make you feel?"
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
            suggested_actions=["reflect", "reframe", "journal"],
        )
