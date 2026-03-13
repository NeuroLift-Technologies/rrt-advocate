"""
Tiered Activation Dialogue Tree - Backend Handlers
Maps Stage 2 distress assessment inputs to Persona Fusion Engine.

User-led, low-demand journey. Stage 1 asks for consent before full RRT activation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from persona.fusion_engine import PersonaFusionEngine
from governance.otoi_coordinator import OTOICoordinator, PersonaBlend
from governance.toi_parser import TOIConfig


class DialogueStage(int, Enum):
    """Stages 0-5 of the tiered activation dialogue tree."""
    STAGE_0_IDLE = 0
    STAGE_1_CONSENT = 1
    STAGE_2_ASSESSMENT = 2
    STAGE_3_FUSION = 3
    STAGE_4_RESPONSE = 4
    STAGE_5_FOLLOWUP = 5


# Stage 2 canonical inputs (from briefing)
STAGE_2_INPUTS = [
    "Everything hurts / Meltdown",
    "Can't do basic tasks",
    "Can't stop self-blame",
    "Stuck in hyperfocus/loop",
    "Don't know / Shut down",
]


@dataclass
class Stage2Result:
    """Result of Stage 2 handler: blend ready for Stage 3/4."""
    distress_key: str
    blend: PersonaBlend
    silent_mode: bool


class StageHandlers:
    """
    Backend handlers for the tiered activation dialogue tree.
    Stage 2 inputs map directly to Fusion Engine.
    """

    def __init__(
        self,
        fusion_engine: Optional[PersonaFusionEngine] = None,
        toi: Optional[TOIConfig] = None,
    ):
        self.fusion_engine = fusion_engine or PersonaFusionEngine()
        self._toi = toi
        self._otoi = OTOICoordinator(toi) if toi else None

    def set_toi(self, toi: TOIConfig) -> None:
        """Update TOI for OTOI coordination."""
        self._toi = toi
        self._otoi = OTOICoordinator(toi)

    def handle_stage_1_consent_prompt(self) -> str:
        """
        Stage 1 Entry Prompt: Agency-first.
        Pause and ask for consent before deploying full RRT Advocate.
        """
        return (
            "I notice you might need some support. Would you like me to help right now? "
            "You can say yes, not yet, or tell me what you're experiencing. No pressure."
        )

    def handle_stage_2_assessment(self, user_input: str) -> Stage2Result:
        """
        Map Stage 2 distress assessment input to Fusion Engine.
        Returns blend (possibly OTOI-adjusted) for response generation.
        """
        blend = self.fusion_engine.compute_blend(user_input)

        if self._otoi:
            blend = self._otoi.apply_toi_to_blend(blend, user_input)

        distress_key = self.fusion_engine._map_to_config_key(user_input)
        silent_mode = self._otoi.should_trigger_silent_mode(blend) if self._otoi else blend.silent_mode

        return Stage2Result(
            distress_key=distress_key,
            blend=blend,
            silent_mode=silent_mode,
        )

    def get_stage_2_options(self) -> list:
        """Return the 5 Stage 2 option strings for UI display."""
        return list(STAGE_2_INPUTS)
