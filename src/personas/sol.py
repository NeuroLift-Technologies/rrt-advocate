"""
SOL — Original Guide: Executive Function Scaffolding.

Sol scaffolds executive function, breaks down tasks into the smallest
possible steps, and manages attention fatigue.  Sol never shames
the user for incomplete work.
"""

from __future__ import annotations

from typing import Any, Dict

from .persona_base import Persona, PersonaResponse


class Sol(Persona):

    @property
    def persona_id(self) -> str:
        return "sol"

    @property
    def display_name(self) -> str:
        return "Sol"

    @property
    def core_role(self) -> str:
        return "Scaffolds executive function, breaks down tasks, manages attention fatigue"

    RESPONSES = {
        "supportive": {
            "cant_do_tasks": (
                "That's okay — let's make it tiny. What's one small thing "
                "you could do in the next two minutes? Even getting a glass "
                "of water counts."
            ),
            "overwhelm": (
                "There's a lot on the list, and that makes sense. "
                "Let's pick just one thing and shrink it down together."
            ),
            "default": (
                "Let's find the smallest possible next step. No pressure "
                "on anything beyond that."
            ),
        },
        "minimal": {
            "cant_do_tasks": "Pick one tiny thing. Two minutes max.",
            "overwhelm": "One thing. Shrink it down.",
            "default": "Smallest next step.",
        },
        "directive": {
            "cant_do_tasks": (
                "Choose one task. Break it into the smallest action you can "
                "take right now."
            ),
            "overwhelm": "List three items. Pick the easiest. Start there.",
            "default": "Identify the next micro-step and do only that.",
        },
        "therapeutic": {
            "cant_do_tasks": (
                "When everything feels impossible, it's often because we're "
                "looking at the whole mountain. What if we just looked at "
                "the very first pebble?"
            ),
            "overwhelm": (
                "I wonder what it would feel like to let go of the full "
                "list and focus on just one small thing that feels doable?"
            ),
            "default": (
                "What feels like the gentlest place to start?"
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
            suggested_actions=["micro_task", "simplify", "break_down"],
        )
