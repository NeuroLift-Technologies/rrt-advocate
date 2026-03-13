"""
Dialogue Tree — state machine that walks the user through Stages 0-5.

Key design principles:
  * Agency-first: the system MUST obtain consent (Stage 1) before proceeding.
  * No forced productivity: if the user declines or selects "Shut down",
    the system backs off or enters Silent Mode.
  * Low cognitive load: options are minimal; free-text is never required.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.models import (
    CrisisAssessment,
    DialogueStage,
    DistressInput,
    FusedResponse,
    PersonaWeights,
)
from src.dialogue.stages import StageDefinitions, StageSpec
from src.personas.fusion_engine import FusionEngine

logger = logging.getLogger(__name__)


class DialogueTree:
    """
    Manages the user's journey through the tiered activation stages.

    Usage
    -----
    tree = DialogueTree(fusion_engine)
    # CDE fires → advance from Stage 0 to Stage 1
    resp = tree.advance()                  # returns Stage 1 consent prompt
    resp = tree.respond("yes")             # user consents → Stage 2 options
    resp = tree.respond("Meltdown")        # Stage 2 → Stage 3 fused support
    resp = tree.advance()                  # Stage 3 → Stage 4 grounding
    resp = tree.advance()                  # Stage 4 → Stage 5 transition
    """

    def __init__(self, fusion_engine: FusionEngine):
        self._engine = fusion_engine
        self._stage = DialogueStage.STAGE_0_DETECTION
        self._consent_given = False
        self._distress: Optional[DistressInput] = None
        self._context: Dict[str, Any] = {}

    @property
    def current_stage(self) -> DialogueStage:
        return self._stage

    @property
    def consent_given(self) -> bool:
        return self._consent_given

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def trigger_from_cde(self, assessment: CrisisAssessment) -> Dict[str, Any]:
        """
        Called when the CDE detects elevated distress.
        Moves from Stage 0 → Stage 1 and returns the consent prompt.
        """
        self._context["assessment"] = {
            "level": assessment.crisis_level.value,
            "confidence": assessment.confidence_score,
        }
        self._stage = DialogueStage.STAGE_1_CONSENT
        spec = StageDefinitions.get(self._stage)
        return self._stage_payload(spec)

    def respond(self, user_input: str) -> Dict[str, Any]:
        """
        Process a user reply at the current stage and advance accordingly.
        """
        if self._stage == DialogueStage.STAGE_1_CONSENT:
            return self._handle_consent(user_input)
        if self._stage == DialogueStage.STAGE_2_ASSESSMENT:
            return self._handle_assessment(user_input)
        if self._stage == DialogueStage.STAGE_5_TRANSITION:
            return self._handle_transition(user_input)
        return self.advance()

    def advance(self) -> Dict[str, Any]:
        """Move to the next stage in sequence (where auto-advance is valid)."""
        next_val = self._stage.value + 1
        if next_val > DialogueStage.STAGE_5_TRANSITION.value:
            return self._end_session()
        self._stage = DialogueStage(next_val)
        spec = StageDefinitions.get(self._stage)
        if spec.requires_consent and not self._consent_given:
            return self._no_consent_exit()
        if self._stage == DialogueStage.STAGE_3_SUPPORT:
            return self._generate_support()
        return self._stage_payload(spec)

    def reset(self) -> None:
        """Reset the tree to its initial state."""
        self._stage = DialogueStage.STAGE_0_DETECTION
        self._consent_given = False
        self._distress = None
        self._context = {}

    # ------------------------------------------------------------------
    # Stage handlers
    # ------------------------------------------------------------------

    def _handle_consent(self, user_input: str) -> Dict[str, Any]:
        lower = user_input.strip().lower()
        affirmative = any(w in lower for w in ("yes", "okay", "ok", "sure", "support"))
        if affirmative:
            self._consent_given = True
            self._stage = DialogueStage.STAGE_2_ASSESSMENT
            spec = StageDefinitions.get(self._stage)
            return self._stage_payload(spec)
        return self._no_consent_exit()

    def _handle_assessment(self, user_input: str) -> Dict[str, Any]:
        self._distress = StageDefinitions.stage_2_distress(user_input)
        self._stage = DialogueStage.STAGE_3_SUPPORT
        return self._generate_support()

    def _handle_transition(self, user_input: str) -> Dict[str, Any]:
        lower = user_input.strip().lower()
        payload: Dict[str, Any] = {
            "stage": self._stage.value,
            "label": "Transition",
        }
        if "later" in lower or "check" in lower:
            payload["action"] = "schedule_followup"
            payload["message"] = (
                "I'll check back in a little while. You know where to find me."
            )
        elif "resource" in lower:
            payload["action"] = "show_resources"
            payload["message"] = (
                "Here are some resources that might help:\n"
                "• 988 Suicide & Crisis Lifeline (call or text 988)\n"
                "• Crisis Text Line (text HOME to 741741)\n"
                "• CHADD — chadd.org\n"
                "• ADDitude — additudemag.com"
            )
        else:
            payload["action"] = "user_initiated_exit"
            payload["message"] = (
                "You know where to find me whenever you need. Take care."
            )
        return payload

    def _generate_support(self) -> Dict[str, Any]:
        distress = self._distress or DistressInput.SHUTDOWN
        fused: FusedResponse = self._engine.generate(
            distress=distress,
            context=self._context,
        )
        return {
            "stage": self._stage.value,
            "label": "Active Support",
            "fused_response": fused,
            "message": fused.primary_message,
            "silent_mode": fused.silent_mode,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _stage_payload(spec: StageSpec) -> Dict[str, Any]:
        return {
            "stage": spec.stage.value,
            "label": spec.label,
            "prompts": spec.prompts,
            "options": spec.options,
        }

    @staticmethod
    def _no_consent_exit() -> Dict[str, Any]:
        return {
            "stage": DialogueStage.STAGE_1_CONSENT.value,
            "label": "Consent Declined",
            "message": (
                "That's completely okay. I'll be right here whenever "
                "you're ready — no pressure at all."
            ),
            "action": "consent_declined",
        }

    @staticmethod
    def _end_session() -> Dict[str, Any]:
        return {
            "stage": DialogueStage.STAGE_5_TRANSITION.value,
            "label": "Session Complete",
            "message": "Session complete. Remember — reaching out is strength.",
            "action": "session_end",
        }
