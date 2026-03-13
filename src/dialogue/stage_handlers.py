"""
Stage Handlers - Tiered Activation Dialogue Tree (Stages 0-5)

Coordinates the user-led, low-demand intervention flow.
Stage 2 distress inputs are mapped to Persona Fusion Engine weights.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .stage1_entry import Stage1EntryHandler, Stage1EntryResult
from .distress_options import DISTRESS_OPTIONS, get_option_by_id
from ..personas.fusion_engine import PersonaFusionEngine
from ..personas.distress_mapper import get_persona_weights_for_distress


class DialogueStage(Enum):
    """Dialogue tree stages 0-5"""
    STAGE_0 = 0   # Pre-activation / dormant
    STAGE_1 = 1   # Entry / consent request
    STAGE_2 = 2   # Distress assessment (user selects)
    STAGE_3 = 3   # Persona-weighted response generation
    STAGE_4 = 4   # Follow-up / stabilization
    STAGE_5 = 5   # Exit / handoff


@dataclass
class StageContext:
    """Context passed between dialogue stages"""
    stage: DialogueStage
    consent_granted: bool = False
    distress_option_id: Optional[str] = None
    persona_weights: Optional[Dict[str, float]] = None
    silent_mode_active: bool = False
    session_metadata: Optional[Dict[str, Any]] = None


class StageHandlers:
    """
    Handles transitions and logic for the Tiered Activation Dialogue Tree.
    Integrates Stage 1 consent, Stage 2 distress selection, and Persona Fusion.
    """

    def __init__(self, fusion_engine: Optional[PersonaFusionEngine] = None):
        self.stage1 = Stage1EntryHandler()
        self.fusion_engine = fusion_engine or PersonaFusionEngine()

    def process_stage1_response(self, user_response: str) -> Stage1EntryResult:
        """Process Stage 1 user response; returns consent result."""
        return self.stage1.parse_consent(user_response)

    def process_stage2_selection(self, distress_option_id: str) -> StageContext:
        """
        Process Stage 2 distress selection.
        Maps to persona weights and determines if Silent Mode is active.
        """
        option = get_option_by_id(distress_option_id)
        if not option:
            return StageContext(
                stage=DialogueStage.STAGE_2,
                distress_option_id=distress_option_id,
                persona_weights=self.fusion_engine.get_default_weights(),
                silent_mode_active=False,
            )

        persona_weights = get_persona_weights_for_distress(distress_option_id)
        return StageContext(
            stage=DialogueStage.STAGE_3,
            consent_granted=True,
            distress_option_id=distress_option_id,
            persona_weights=persona_weights,
            silent_mode_active=option.triggers_silent_mode,
        )

    def get_stage1_prompt(self, tone_variant: str = "default") -> str:
        """Get Stage 1 entry prompt for the given tone."""
        self.stage1.tone_variant = tone_variant
        return self.stage1.get_entry_prompt()
