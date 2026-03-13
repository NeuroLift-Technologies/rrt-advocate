"""
Tiered Activation Dialogue Tree — the user-facing interaction flow
that prioritises agency and explicit consent at every step.

Stages
------
0 — Passive Observation   (CDE running, no user-facing output)
1 — Entry Prompt          (consent request)
2 — Distress Assessment   (user selects flavour of distress)
3 — Persona Fusion        (system generates blended response)
4 — Ongoing Support       (iterative loop of 2→3 until user exits)
5 — Graceful Exit         (user disengages; system returns to Stage 0)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional

from ..personas.fusion_engine import FusionEngine, FusedResponse, PersonaWeights
from ..toi.toi_config import TOIConfig
from ..toi.toi_parser import TOIParser
from ..toi.otoi_coordinator import OTOICoordinator
from ..tones.tone_profiles import ToneManager
from .consent_manager import ConsentManager, ConsentState
from .stage_handlers import StageHandlers


class ActivationStage(IntEnum):
    PASSIVE_OBSERVATION = 0
    ENTRY_PROMPT = 1
    DISTRESS_ASSESSMENT = 2
    PERSONA_FUSION = 3
    ONGOING_SUPPORT = 4
    GRACEFUL_EXIT = 5


@dataclass
class StageInput:
    """Payload from the UI layer for a single dialogue turn."""
    user_text: str = ""
    selected_option: str = ""
    consent_response: Optional[bool] = None


@dataclass
class StageOutput:
    """Payload returned to the UI layer."""
    stage: ActivationStage
    text: str = ""
    options: List[str] = field(default_factory=list)
    fused_response: Optional[FusedResponse] = None
    silent_mode: bool = False
    visual_cues: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


STAGE2_OPTIONS = [
    "Everything hurts / Meltdown",
    "Can't do basic tasks",
    "Can't stop self-blame",
    "Stuck in hyperfocus/loop",
    "Don't know / Shut down",
]


class DialogueTree:
    """
    State machine that walks the user through the tiered activation
    flow.  Each call to ``advance()`` processes the current stage's
    input and transitions to the next stage.
    """

    def __init__(
        self,
        toi: TOIConfig,
        fusion_engine: Optional[FusionEngine] = None,
    ) -> None:
        self.toi = toi
        self.toi_parser = TOIParser(toi)
        self.otoi = OTOICoordinator(toi)
        self.consent = ConsentManager()
        self.handlers = StageHandlers()
        self.tone_manager = ToneManager()
        self.fusion = fusion_engine or FusionEngine()

        self._stage = ActivationStage.PASSIVE_OBSERVATION
        self._last_weights: Optional[PersonaWeights] = None

    @property
    def current_stage(self) -> ActivationStage:
        return self._stage

    def trigger_entry(self) -> StageOutput:
        """
        Called when the CDE (or the user) triggers the activation flow.
        Moves from Stage 0 → Stage 1 and returns the consent prompt.
        """
        self._stage = ActivationStage.ENTRY_PROMPT
        prompt = self.consent.request_consent()
        return StageOutput(
            stage=self._stage,
            text=prompt,
            options=["Yes, I'd like support", "Not right now"],
        )

    def advance(self, inp: StageInput) -> StageOutput:
        """
        Process the user's input for the current stage and return
        the next stage's output.
        """
        if self._stage == ActivationStage.ENTRY_PROMPT:
            return self._handle_consent(inp)

        if self._stage in (
            ActivationStage.DISTRESS_ASSESSMENT,
            ActivationStage.ONGOING_SUPPORT,
        ):
            return self._handle_distress_selection(inp)

        if self._stage == ActivationStage.PERSONA_FUSION:
            return self._present_fusion(inp)

        if self._stage == ActivationStage.GRACEFUL_EXIT:
            return self._handle_exit(inp)

        return StageOutput(stage=self._stage)

    def exit(self) -> StageOutput:
        """User-initiated exit at any point."""
        self._stage = ActivationStage.GRACEFUL_EXIT
        self.consent.withdraw()
        return StageOutput(
            stage=self._stage,
            text=(
                "Okay, stepping back. I'm still here if you need me — "
                "no pressure, no judgement."
            ),
        )

    # ------------------------------------------------------------------
    # Stage handlers
    # ------------------------------------------------------------------

    def _handle_consent(self, inp: StageInput) -> StageOutput:
        if inp.consent_response is True or "yes" in inp.selected_option.lower():
            self.consent.grant()
            self._stage = ActivationStage.DISTRESS_ASSESSMENT
            return StageOutput(
                stage=self._stage,
                text="What feels closest to where you are right now?",
                options=STAGE2_OPTIONS,
            )

        self.consent.decline()
        self._stage = ActivationStage.GRACEFUL_EXIT
        return StageOutput(
            stage=self._stage,
            text=(
                "That's completely okay. I'll be here whenever you're "
                "ready — no rush."
            ),
        )

    def _handle_distress_selection(self, inp: StageInput) -> StageOutput:
        selection = inp.selected_option or inp.user_text
        weights = self.handlers.get_weights(selection)
        context = self.handlers.get_distress_context(selection)

        otoi_caps = self.otoi.validate_fusion_output(weights.as_dict())

        tone_str = self.toi.tone.value
        fused = self.fusion.fuse(
            weights=weights,
            distress_context=context,
            tone=tone_str,
            otoi_caps=otoi_caps,
        )

        filtered = self.toi_parser.filter_response(fused.primary_text)

        self._last_weights = weights
        self._stage = ActivationStage.PERSONA_FUSION

        return StageOutput(
            stage=self._stage,
            text=filtered.filtered_text,
            fused_response=fused,
            silent_mode=fused.silent_mode,
            visual_cues=fused.visual_cues,
            options=["This helps", "Try something else", "I want to stop"],
            metadata={
                "weights": weights.as_dict(),
                "otoi_caps": otoi_caps,
                "toi_modifications": filtered.modifications,
            },
        )

    def _present_fusion(self, inp: StageInput) -> StageOutput:
        sel = (inp.selected_option or inp.user_text).lower()
        if "stop" in sel or "exit" in sel:
            return self.exit()

        if "else" in sel or "try" in sel:
            self._stage = ActivationStage.ONGOING_SUPPORT
            return StageOutput(
                stage=self._stage,
                text="No problem. What feels closest now?",
                options=STAGE2_OPTIONS,
            )

        self._stage = ActivationStage.ONGOING_SUPPORT
        return StageOutput(
            stage=self._stage,
            text="I'm glad. I'm still here. Let me know if anything shifts.",
            options=STAGE2_OPTIONS + ["I'm okay now"],
        )

    def _handle_exit(self, _inp: StageInput) -> StageOutput:
        self._stage = ActivationStage.PASSIVE_OBSERVATION
        self.consent.reset()
        return StageOutput(
            stage=self._stage,
            text="",
        )
