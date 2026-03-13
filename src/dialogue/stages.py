"""
Stage definitions for the Tiered Activation Dialogue Tree.

Stage 0  —  Detection    (passive CDE monitoring, no user interaction)
Stage 1  —  Consent      (entry prompt; user must opt-in before any response)
Stage 2  —  Assessment   (low-demand distress self-report → 5 options)
Stage 3  —  Support      (persona-blended active support)
Stage 4  —  Grounding    (de-escalation / grounding exercises)
Stage 5  —  Transition   (gentle exit, follow-up scheduling, resource links)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from src.models import DialogueStage, DistressInput


@dataclass(frozen=True)
class StageSpec:
    stage: DialogueStage
    label: str
    description: str
    requires_consent: bool
    prompts: List[str] = field(default_factory=list)
    options: List[str] = field(default_factory=list)


STAGE_2_OPTION_MAP: Dict[str, DistressInput] = {
    "Everything hurts / Meltdown": DistressInput.MELTDOWN,
    "Can't do basic tasks": DistressInput.TASK_PARALYSIS,
    "Can't stop self-blame": DistressInput.SELF_BLAME,
    "Stuck in hyperfocus/loop": DistressInput.HYPERFOCUS_LOOP,
    "Don't know / Shut down": DistressInput.SHUTDOWN,
}


class StageDefinitions:
    """Canonical stage specs for the dialogue tree."""

    STAGES: Dict[DialogueStage, StageSpec] = {
        DialogueStage.STAGE_0_DETECTION: StageSpec(
            stage=DialogueStage.STAGE_0_DETECTION,
            label="Detection",
            description="Passive CDE monitoring. No user-facing interaction.",
            requires_consent=False,
        ),
        DialogueStage.STAGE_1_CONSENT: StageSpec(
            stage=DialogueStage.STAGE_1_CONSENT,
            label="Consent",
            description="Entry prompt — the system pauses and asks permission.",
            requires_consent=True,
            prompts=[
                "Hey — I noticed things might be getting heavy right now. "
                "Would it be okay if I checked in with you?",
            ],
            options=["Yes, I could use some support", "Not right now"],
        ),
        DialogueStage.STAGE_2_ASSESSMENT: StageSpec(
            stage=DialogueStage.STAGE_2_ASSESSMENT,
            label="Assessment",
            description="Low-demand distress self-report.",
            requires_consent=True,
            prompts=[
                "No pressure to explain everything. "
                "Which of these feels closest to where you are right now?",
            ],
            options=list(STAGE_2_OPTION_MAP.keys()),
        ),
        DialogueStage.STAGE_3_SUPPORT: StageSpec(
            stage=DialogueStage.STAGE_3_SUPPORT,
            label="Active Support",
            description="Persona-blended response based on assessment.",
            requires_consent=True,
        ),
        DialogueStage.STAGE_4_GROUNDING: StageSpec(
            stage=DialogueStage.STAGE_4_GROUNDING,
            label="Grounding",
            description="De-escalation exercises and anchoring techniques.",
            requires_consent=True,
            prompts=[
                "Let's try a quick grounding exercise. "
                "Can you name five things you can see right now?",
            ],
        ),
        DialogueStage.STAGE_5_TRANSITION: StageSpec(
            stage=DialogueStage.STAGE_5_TRANSITION,
            label="Transition",
            description="Gentle exit, follow-up offer, resource links.",
            requires_consent=False,
            prompts=[
                "You handled that. I'm proud of you. "
                "Would you like me to check in again later, "
                "or would you prefer to reach out when you're ready?",
            ],
            options=[
                "Check in later",
                "I'll reach out when I'm ready",
                "Show me some resources",
            ],
        ),
    }

    @classmethod
    def get(cls, stage: DialogueStage) -> StageSpec:
        return cls.STAGES[stage]

    @classmethod
    def stage_2_distress(cls, user_choice: str) -> DistressInput:
        """Map a Stage-2 user selection to a DistressInput enum."""
        normalised = user_choice.strip()
        if normalised in STAGE_2_OPTION_MAP:
            return STAGE_2_OPTION_MAP[normalised]
        lower = normalised.lower()
        for label, distress in STAGE_2_OPTION_MAP.items():
            if lower in label.lower():
                return distress
        return DistressInput.SHUTDOWN
