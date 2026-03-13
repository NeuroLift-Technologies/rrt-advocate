"""
RRT AIdvocAIte — Protective Layer of the Solidarity Framework.

Main orchestrator that wires together:
  • TOI-OTOI Governance Wrapper
  • Persona Fusion Engine (5 OG personas)
  • Crisis Detection Engine (3-layer CDE)
  • Tiered Activation Dialogue Tree
  • Configurable Tone Profiles

Every interaction flows through the TOI middleware before the user
sees it.  The CDE runs locally and never transmits user data.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .toi.toi_config import TOIConfig, TonePreference
from .toi.toi_parser import TOIParser, TOIFilterResult
from .toi.otoi_coordinator import OTOICoordinator

from .personas.fusion_engine import FusionEngine, FusedResponse, PersonaWeights

from .detection.cde_pipeline import CDEPipeline, CDEResult

from .dialogue.dialogue_tree import (
    DialogueTree,
    ActivationStage,
    StageInput,
    StageOutput,
)
from .dialogue.consent_manager import ConsentState

from .tones.tone_profiles import ToneManager, ToneType


class CrisisLevel(Enum):
    """Severity tier derived from the CDE aggregate distress score."""
    GREEN = "stable"
    YELLOW = "elevated"
    ORANGE = "high"
    RED = "critical"
    BLACK = "emergency"


class ResponseStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUCCESSFUL = "successful"
    ESCALATED = "escalated"
    COMPLETED = "completed"


@dataclass
class SessionState:
    """Mutable per-session state for a single user."""
    user_id: str
    toi: TOIConfig
    crisis_level: CrisisLevel = CrisisLevel.GREEN
    consent: ConsentState = ConsentState.NOT_ASKED
    is_monitoring: bool = False
    interaction_count: int = 0
    cde_history: List[CDEResult] = field(default_factory=list)
    response_history: List[StageOutput] = field(default_factory=list)
    started_at: Optional[datetime] = None


# Thresholds for mapping CDE aggregate → CrisisLevel
_LEVEL_THRESHOLDS = [
    (0.0, 0.15, CrisisLevel.GREEN),
    (0.15, 0.35, CrisisLevel.YELLOW),
    (0.35, 0.60, CrisisLevel.ORANGE),
    (0.60, 0.85, CrisisLevel.RED),
    (0.85, 1.01, CrisisLevel.BLACK),
]


def _score_to_level(score: float) -> CrisisLevel:
    for lo, hi, level in _LEVEL_THRESHOLDS:
        if lo <= score < hi:
            return level
    return CrisisLevel.BLACK


class RRTAdvocate:
    """
    The top-level RRT AIdvocAIte engine.

    Typical lifecycle::

        advocate = RRTAdvocate("user_123")
        advocate.update_toi({...})

        # User sends a message
        result = advocate.process_message("I can't do anything right")

        # CDE analyses the message, dialogue tree manages flow,
        # fusion engine blends personas, TOI filters the output.
    """

    CDE_ACTIVATION_THRESHOLD = 0.20

    def __init__(
        self,
        user_id: str,
        toi_dict: Optional[Dict[str, Any]] = None,
    ) -> None:
        toi = TOIConfig.from_dict(toi_dict) if toi_dict else TOIConfig()

        self.session = SessionState(user_id=user_id, toi=toi)
        self.cde = CDEPipeline()
        self.fusion = FusionEngine()
        self.toi_parser = TOIParser(toi)
        self.otoi = OTOICoordinator(toi)
        self.tone_manager = ToneManager()
        self.dialogue = DialogueTree(toi, self.fusion)

        self.logger = logging.getLogger(f"RRTAdvocate-{user_id}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_toi(self, toi_dict: Dict[str, Any]) -> None:
        """Hot-swap the TOI config mid-session."""
        toi = TOIConfig.from_dict(toi_dict)
        self.session.toi = toi
        self.toi_parser = TOIParser(toi)
        self.otoi = OTOICoordinator(toi)
        self.dialogue = DialogueTree(toi, self.fusion)

    def process_message(self, text: str) -> Dict[str, Any]:
        """
        Main entry point.  Processes a user message through the full
        CDE → Dialogue → Fusion → TOI pipeline.

        Returns a dictionary suitable for serialisation to a UI layer.
        """
        self.session.interaction_count += 1

        cde_result = self.cde.analyse(text)
        self.session.cde_history.append(cde_result)

        level = _score_to_level(cde_result.aggregate_distress)
        self.session.crisis_level = level

        stage = self.dialogue.current_stage

        if stage == ActivationStage.PASSIVE_OBSERVATION:
            if cde_result.aggregate_distress >= self.CDE_ACTIVATION_THRESHOLD:
                output = self.dialogue.trigger_entry()
                return self._build_response(output, cde_result)
            return self._passive_response(cde_result)

        if stage == ActivationStage.ENTRY_PROMPT:
            consent_yes = self._interpret_consent(text)
            inp = StageInput(
                user_text=text,
                selected_option=text,
                consent_response=consent_yes,
            )
            output = self.dialogue.advance(inp)
            return self._build_response(output, cde_result)

        inp = StageInput(user_text=text, selected_option=text)
        output = self.dialogue.advance(inp)
        return self._build_response(output, cde_result)

    def process_selection(self, option: str) -> Dict[str, Any]:
        """
        Process a UI button/option selection (as opposed to free text).
        """
        self.session.interaction_count += 1
        stage = self.dialogue.current_stage

        if stage == ActivationStage.ENTRY_PROMPT:
            consent_yes = "yes" in option.lower()
            inp = StageInput(
                selected_option=option,
                consent_response=consent_yes,
            )
        else:
            inp = StageInput(selected_option=option)

        exit_phrases = {"i want to stop", "i'm okay now", "okay now"}
        if option.lower().strip() in exit_phrases:
            output = self.dialogue.exit()
        else:
            output = self.dialogue.advance(inp)

        return self._build_response(output, None)

    def exit_session(self) -> Dict[str, Any]:
        output = self.dialogue.exit()
        return self._build_response(output, None)

    def get_status(self) -> Dict[str, Any]:
        return {
            "user_id": self.session.user_id,
            "crisis_level": self.session.crisis_level.value,
            "stage": self.dialogue.current_stage.name,
            "consent": self.dialogue.consent.state.value,
            "interaction_count": self.session.interaction_count,
            "toi": self.session.toi.to_dict(),
            "cde_history_length": len(self.session.cde_history),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _interpret_consent(text: str) -> bool:
        positive = {"yes", "yeah", "yep", "sure", "ok", "okay", "please", "help"}
        tokens = set(text.lower().strip().split())
        return bool(tokens & positive)

    def _passive_response(self, cde: CDEResult) -> Dict[str, Any]:
        return {
            "stage": "passive_observation",
            "crisis_level": self.session.crisis_level.value,
            "text": "",
            "silent_mode": False,
            "options": [],
            "cde_summary": {
                "aggregate_distress": cde.aggregate_distress,
                "distress_type": cde.distress_type,
                "flags": cde.flags,
            },
        }

    def _build_response(
        self,
        output: StageOutput,
        cde: Optional[CDEResult],
    ) -> Dict[str, Any]:
        self.session.response_history.append(output)
        result: Dict[str, Any] = {
            "stage": output.stage.name,
            "crisis_level": self.session.crisis_level.value,
            "text": output.text,
            "silent_mode": output.silent_mode,
            "visual_cues": output.visual_cues,
            "options": output.options,
            "metadata": output.metadata,
        }
        if cde:
            result["cde_summary"] = {
                "aggregate_distress": cde.aggregate_distress,
                "distress_type": cde.distress_type,
                "flags": cde.flags,
            }
        return result
