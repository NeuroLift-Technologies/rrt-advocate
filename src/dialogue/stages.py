"""
Activation Stage Definitions — Tiered Activation Dialogue Tree
Stages 0–5 of the RRT AIdvocAIte user journey.

Agency First: Every stage is designed to pause and check in before advancing.
No forced progression. The user controls the pace.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class ActivationStage(Enum):
    """
    The six stages of the RRT AIdvocAIte activation sequence.

    Designed to minimize cognitive load at each transition. The user
    can stay in any stage indefinitely or exit at any point.
    """
    STAGE_0_PASSIVE = 0        # Passive monitoring; silent presence available
    STAGE_1_ENTRY = 1          # Entry prompt: consent check (Agency First)
    STAGE_2_ASSESSMENT = 2     # Distress type assessment (maps to FusionEngine)
    STAGE_3_INTERVENTION = 3   # Persona-blended intervention delivery
    STAGE_4_FOLLOWUP = 4       # Follow-up / de-escalation check
    STAGE_5_CLOSURE = 5        # Closure / handoff / wind-down


@dataclass
class StageOption:
    """A single selectable option presented to the user at a stage."""
    key: str
    display_text: str
    next_stage: Optional[ActivationStage]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageConfig:
    """
    Configuration for a single dialogue stage.

    Defines the prompt, options, and transition rules for the stage.
    """
    stage: ActivationStage
    name: str
    prompt: str
    options: List[StageOption] = field(default_factory=list)
    requires_consent: bool = False
    allow_silent_mode: bool = False
    auto_advance: bool = False  # If True, advances without waiting for user input
    description: str = ""


# ============================================================================
# Stage Configurations
# These define the complete user journey through the RRT AIdvocAIte.
# ============================================================================

STAGE_CONFIGS: Dict[ActivationStage, StageConfig] = {

    ActivationStage.STAGE_0_PASSIVE: StageConfig(
        stage=ActivationStage.STAGE_0_PASSIVE,
        name="Passive Presence",
        description="Silent background monitoring. The Advocate is present but not intrusive.",
        prompt="",  # No visible prompt in passive stage
        options=[
            StageOption(
                key="check_in",
                display_text="I'd like to check in",
                next_stage=ActivationStage.STAGE_1_ENTRY,
            ),
        ],
        requires_consent=False,
        allow_silent_mode=True,
        auto_advance=False,
    ),

    ActivationStage.STAGE_1_ENTRY: StageConfig(
        stage=ActivationStage.STAGE_1_ENTRY,
        name="Entry & Consent",
        description="Agency First: The Advocate pauses and asks for consent before proceeding.",
        prompt=(
            "Hey. I noticed something feels heavy right now.\n"
            "I'm here — no pressure, no timers, just presence.\n"
            "Can I check in with you for a moment?"
        ),
        options=[
            StageOption(
                key="yes",
                display_text="Yes, I'd like support",
                next_stage=ActivationStage.STAGE_2_ASSESSMENT,
                metadata={"grants_consent": True},
            ),
            StageOption(
                key="not_now",
                display_text="Not right now",
                next_stage=ActivationStage.STAGE_0_PASSIVE,
                metadata={"grants_consent": False},
            ),
            StageOption(
                key="silent",
                display_text="Just be here with me (Silent Mode)",
                next_stage=ActivationStage.STAGE_3_INTERVENTION,
                metadata={"grants_consent": True, "activate_silent_mode": True},
            ),
        ],
        requires_consent=False,  # This stage IS the consent check
        allow_silent_mode=True,
        auto_advance=False,
    ),

    ActivationStage.STAGE_2_ASSESSMENT: StageConfig(
        stage=ActivationStage.STAGE_2_ASSESSMENT,
        name="Distress Assessment",
        description=(
            "Low-demand assessment of the specific flavor of distress. "
            "Maps directly to FusionEngine persona weights."
        ),
        prompt=(
            "I'm with you. Can you tell me a little about what's happening?\n"
            "You can pick the one that feels closest — or skip if nothing fits."
        ),
        options=[
            StageOption(
                key="meltdown",
                display_text="Everything hurts / I'm in meltdown",
                next_stage=ActivationStage.STAGE_3_INTERVENTION,
                metadata={"distress_input": "everything_hurts_meltdown"},
            ),
            StageOption(
                key="cant_task",
                display_text="I can't do basic tasks",
                next_stage=ActivationStage.STAGE_3_INTERVENTION,
                metadata={"distress_input": "cant_do_basic_tasks"},
            ),
            StageOption(
                key="self_blame",
                display_text="I can't stop blaming myself",
                next_stage=ActivationStage.STAGE_3_INTERVENTION,
                metadata={"distress_input": "cant_stop_self_blame"},
            ),
            StageOption(
                key="hyperfocus",
                display_text="I'm stuck in a loop / can't stop fixating",
                next_stage=ActivationStage.STAGE_3_INTERVENTION,
                metadata={"distress_input": "stuck_in_hyperfocus_loop"},
            ),
            StageOption(
                key="shutdown",
                display_text="I don't know / I've shut down",
                next_stage=ActivationStage.STAGE_3_INTERVENTION,
                metadata={"distress_input": "dont_know_shut_down", "activate_silent_mode": True},
            ),
            StageOption(
                key="skip",
                display_text="Skip / Just be here",
                next_stage=ActivationStage.STAGE_3_INTERVENTION,
                metadata={"distress_input": None},
            ),
        ],
        requires_consent=True,
        allow_silent_mode=True,
        auto_advance=False,
    ),

    ActivationStage.STAGE_3_INTERVENTION: StageConfig(
        stage=ActivationStage.STAGE_3_INTERVENTION,
        name="Persona-Blended Intervention",
        description="The FusionEngine delivers the blended persona response.",
        prompt="",  # Populated dynamically by FusionEngine output
        options=[
            StageOption(
                key="helped",
                display_text="That helped, thank you",
                next_stage=ActivationStage.STAGE_4_FOLLOWUP,
            ),
            StageOption(
                key="more",
                display_text="I need more support",
                next_stage=ActivationStage.STAGE_2_ASSESSMENT,
            ),
            StageOption(
                key="stay",
                display_text="Just stay here with me",
                next_stage=ActivationStage.STAGE_3_INTERVENTION,
                metadata={"loop_intervention": True},
            ),
            StageOption(
                key="done",
                display_text="I'm okay now",
                next_stage=ActivationStage.STAGE_5_CLOSURE,
            ),
        ],
        requires_consent=True,
        allow_silent_mode=True,
        auto_advance=False,
    ),

    ActivationStage.STAGE_4_FOLLOWUP: StageConfig(
        stage=ActivationStage.STAGE_4_FOLLOWUP,
        name="Follow-up & De-escalation Check",
        description="Checks in after the intervention to assess de-escalation.",
        prompt=(
            "How are you feeling now? No pressure to be 'better' —\n"
            "just checking in."
        ),
        options=[
            StageOption(
                key="better",
                display_text="A bit better",
                next_stage=ActivationStage.STAGE_5_CLOSURE,
            ),
            StageOption(
                key="same",
                display_text="About the same",
                next_stage=ActivationStage.STAGE_3_INTERVENTION,
            ),
            StageOption(
                key="worse",
                display_text="Worse / I need more help",
                next_stage=ActivationStage.STAGE_2_ASSESSMENT,
                metadata={"escalate": True},
            ),
        ],
        requires_consent=True,
        allow_silent_mode=False,
        auto_advance=False,
    ),

    ActivationStage.STAGE_5_CLOSURE: StageConfig(
        stage=ActivationStage.STAGE_5_CLOSURE,
        name="Closure & Wind-down",
        description="Gentle closure. Offers handoff or continued presence.",
        prompt=(
            "I'm really glad I got to be here with you.\n"
            "Take care of yourself. I'll be here if you need me again."
        ),
        options=[
            StageOption(
                key="goodbye",
                display_text="Thank you, goodbye",
                next_stage=ActivationStage.STAGE_0_PASSIVE,
            ),
            StageOption(
                key="stay",
                display_text="Stay with me a bit longer",
                next_stage=ActivationStage.STAGE_3_INTERVENTION,
                metadata={"loop_intervention": True},
            ),
        ],
        requires_consent=False,
        allow_silent_mode=True,
        auto_advance=False,
    ),
}
