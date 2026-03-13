from __future__ import annotations

from typing import Any

from .models import DistressInput, TOIConfig, ToneProfile


class ToneProfileRenderer:
    def __init__(self, config: dict[str, Any]):
        self.config = config.get("tone_profiles", {})

    def render_entry_prompt(self, toi: TOIConfig) -> str:
        prompts = {
            ToneProfile.SUPPORTIVE_DEFAULT: "I can step into RRT support if you want. Do you want gentle help right now?",
            ToneProfile.MINIMAL: "RRT is available. Want support now?",
            ToneProfile.DIRECTIVE: "I can activate RRT support. Reply yes to continue.",
            ToneProfile.THERAPEUTIC_REFLECTIVE: "I can stay with this carefully and respond in a grounded way if you want. Do you want me to step in now?",
        }
        return prompts[toi.tone]

    def render_support_message(
        self,
        *,
        toi: TOIConfig,
        distress_input: DistressInput,
        active_personas: list[str],
        recommended_actions: list[str],
        silent_mode: bool,
    ) -> str:
        primary = active_personas[0] if active_personas else "myra"
        action_text = " ".join(recommended_actions)

        if toi.tone == ToneProfile.MINIMAL:
            if silent_mode:
                return f"Silent mode on. {recommended_actions[0]} {recommended_actions[1]}"
            return f"{primary.title()} lead. {recommended_actions[0]} {recommended_actions[1]}"

        if toi.tone == ToneProfile.DIRECTIVE:
            prefix = "Silent mode is active. " if silent_mode else ""
            return f"{prefix}Start here: {recommended_actions[0]} Then {recommended_actions[1]}"

        if toi.tone == ToneProfile.THERAPEUTIC_REFLECTIVE:
            reflection = {
                DistressInput.EVERYTHING_HURTS_MELTDOWN: "It makes sense that your system is signaling overload.",
                DistressInput.CANT_DO_BASIC_TASKS: "This sounds less like laziness and more like friction plus fatigue.",
                DistressInput.CANT_STOP_SELF_BLAME: "The self-judgment is loud right now, and it does not get to define the facts.",
                DistressInput.STUCK_IN_HYPERFOCUS_LOOP: "Your attention seems locked onto one track and struggling to unhook.",
                DistressInput.DONT_KNOW_SHUT_DOWN: "Words may be offline right now, and that is enough information by itself.",
            }[distress_input]
            if silent_mode:
                return f"{reflection} Silent mode stays on. {action_text}"
            return f"{reflection} {action_text}"

        validation = {
            DistressInput.EVERYTHING_HURTS_MELTDOWN: "This sounds like overload, not failure.",
            DistressInput.CANT_DO_BASIC_TASKS: "A blocked task system is still a stressed system, not a moral problem.",
            DistressInput.CANT_STOP_SELF_BLAME: "Self-blame gets loud when the system is taxed.",
            DistressInput.STUCK_IN_HYPERFOCUS_LOOP: "Being stuck in a loop can feel impossible to interrupt.",
            DistressInput.DONT_KNOW_SHUT_DOWN: "Shutdown is real information, and you do not need to perform clarity.",
        }[distress_input]
        if silent_mode:
            return f"{validation} Silent mode is on. {action_text}"
        return f"{validation} {action_text}"
