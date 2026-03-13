"""Tiered activation dialogue tree for agency-first intervention flow."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from persona_fusion import DistressSignal


class ActivationStage(Enum):
    STAGE_0_IDLE = 0
    STAGE_1_CONSENT = 1
    STAGE_2_DISTRESS = 2
    STAGE_3_SUPPORT = 3
    STAGE_4_SAFETY_CONFIRM = 4
    STAGE_5_ESCALATION = 5


@dataclass
class DialogueState:
    stage: ActivationStage = ActivationStage.STAGE_1_CONSENT
    consent_granted: bool = False
    distress_signal: Optional[DistressSignal] = None


class TieredActivationDialogueTree:
    """Low-demand dialogue flow that preserves user agency."""

    STAGE_2_OPTIONS = [
        DistressSignal.MELTDOWN.value,
        DistressSignal.BASIC_TASKS.value,
        DistressSignal.SELF_BLAME.value,
        DistressSignal.HYPERFOCUS_LOOP.value,
        DistressSignal.SHUTDOWN.value,
    ]

    KEYWORD_MAP: Dict[DistressSignal, List[str]] = {
        DistressSignal.MELTDOWN: ["meltdown", "everything hurts", "overwhelmed"],
        DistressSignal.BASIC_TASKS: ["can't do", "basic task", "task", "stuck starting"],
        DistressSignal.SELF_BLAME: ["self-blame", "my fault", "hate myself", "ashamed"],
        DistressSignal.HYPERFOCUS_LOOP: ["hyperfocus", "loop", "can't stop", "stuck on"],
        DistressSignal.SHUTDOWN: ["shut down", "don't know", "blank", "numb"],
    }

    @staticmethod
    def stage_1_entry_prompt() -> str:
        return (
            "I can activate RRT support now. Do you want me to start? "
            "Reply yes/no. You stay in control."
        )

    @classmethod
    def stage_2_prompt(cls) -> Dict[str, object]:
        return {
            "prompt": "Which one fits best right now?",
            "options": cls.STAGE_2_OPTIONS,
            "note": "You can pick one, or type your own words.",
        }

    @classmethod
    def resolve_distress_signal(cls, user_text: str) -> DistressSignal:
        normalized = user_text.strip().lower()
        for signal in DistressSignal:
            if normalized == signal.value:
                return signal

        for signal, keywords in cls.KEYWORD_MAP.items():
            if any(keyword in normalized for keyword in keywords):
                return signal

        return DistressSignal.SHUTDOWN
