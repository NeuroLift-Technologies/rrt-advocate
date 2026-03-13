"""
RRT AIdvocAIte — Protective Layer of the Solidarity Framework.

This module is the top-level orchestrator that wires together:
  * The TOI-OTOI Governance Wrapper (Constitutional bridge)
  * The Persona Fusion Engine (5 Original Guides)
  * The Crisis Detection Engine (3-layer local-first pipeline)
  * The Tiered Activation Dialogue Tree (Stages 0–5)
  * Configurable Tone Profiles

All processing is local-first.  User data sovereignty is the foundation.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.crisis.engine import CrisisDetectionEngine
from src.dialogue.dialogue_tree import DialogueTree
from src.models import (
    CrisisAssessment,
    CrisisLevel,
    DialogueStage,
    DistressInput,
    FusedResponse,
    InterventionResponse,
    PersonaWeights,
    ResponseStatus,
    UserMessage,
)
from src.personas.fusion_engine import FusionEngine
from src.toi.governance import GovernanceMiddleware
from src.tone.profiles import ToneProfileManager


class RRTAdvocate:
    """
    Rapid Response Team AIdvocAIte — multi-persona crisis orchestration engine.

    Lifecycle:
        1. Construct with a user-id and optional TOI / config overrides.
        2. Feed user messages via ``process_message()``.
        3. The CDE runs automatically; the Dialogue Tree manages consent and staging.
        4. Call ``get_status_report()`` at any time for telemetry.
        5. ``shutdown()`` for graceful teardown.
    """

    def __init__(
        self,
        user_id: str,
        toi_data: Optional[Dict[str, Any]] = None,
        config_path: str = "config/crisis_thresholds.yaml",
    ):
        self.user_id = user_id

        self._governance = GovernanceMiddleware(toi_data)
        self._cde = CrisisDetectionEngine(config_path)
        self._fusion = FusionEngine(self._governance)
        self._dialogue = DialogueTree(self._fusion)
        self._tone_mgr = ToneProfileManager()

        self._is_monitoring = False
        self._current_assessment: Optional[CrisisAssessment] = None
        self._crisis_history: List[CrisisAssessment] = []
        self._response_history: List[FusedResponse] = []
        self._message_history: List[UserMessage] = []

        self.logger = logging.getLogger(f"RRTAdvocate-{user_id}")
        self._setup_logging()
        self.logger.info("RRT AIdvocAIte initialised for user %s", user_id)

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _setup_logging(self) -> None:
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            fmt = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(fmt)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    # ------------------------------------------------------------------
    # Public API — message processing
    # ------------------------------------------------------------------

    def process_message(self, text: str) -> Dict[str, Any]:
        """
        Primary entry-point: ingest a user message, run the CDE,
        and advance the dialogue tree as appropriate.

        Returns a dict describing the system's response for the caller
        to render.
        """
        msg = UserMessage(text=text)
        self._message_history.append(msg)

        assessment = self._cde.analyse(text, msg.timestamp)
        self._current_assessment = assessment
        self._crisis_history.append(assessment)

        stage = self._dialogue.current_stage

        if stage == DialogueStage.STAGE_0_DETECTION:
            if assessment.crisis_level != CrisisLevel.GREEN:
                payload = self._dialogue.trigger_from_cde(assessment)
                return self._wrap(payload, assessment)
            return self._wrap({
                "stage": 0,
                "label": "Monitoring",
                "message": None,
            }, assessment)

        payload = self._dialogue.respond(text)
        if "fused_response" in payload:
            self._response_history.append(payload["fused_response"])
        return self._wrap(payload, assessment)

    def update_toi(self, toi_data: Dict[str, Any]) -> None:
        """Hot-reload the user's Terms of Interaction."""
        self._governance.update_toi(toi_data)
        self.logger.info("TOI updated at runtime")

    # ------------------------------------------------------------------
    # Public API — monitoring
    # ------------------------------------------------------------------

    async def start_monitoring(self) -> bool:
        if self._is_monitoring:
            return True
        self._is_monitoring = True
        self.logger.info("Monitoring started")
        return True

    async def stop_monitoring(self) -> bool:
        self._is_monitoring = False
        self.logger.info("Monitoring stopped")
        return True

    # ------------------------------------------------------------------
    # Public API — status / telemetry
    # ------------------------------------------------------------------

    def get_status_report(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "monitoring_active": self._is_monitoring,
            "dialogue_stage": self._dialogue.current_stage.value,
            "consent_given": self._dialogue.consent_given,
            "current_crisis": {
                "level": (
                    self._current_assessment.crisis_level.value
                    if self._current_assessment
                    else "none"
                ),
                "confidence": (
                    self._current_assessment.confidence_score
                    if self._current_assessment
                    else 0.0
                ),
            },
            "tone": self._governance.toi.tone.value,
            "total_messages": len(self._message_history),
            "total_crises": len(self._crisis_history),
            "total_responses": len(self._response_history),
        }

    def reset(self) -> None:
        """Reset the dialogue tree and assessment state."""
        self._dialogue.reset()
        self._current_assessment = None
        self.logger.info("Session reset")

    async def shutdown(self) -> None:
        await self.stop_monitoring()
        status = self.get_status_report()
        self.logger.info("Final status: %s", json.dumps(status, indent=2))
        self.logger.info("RRT AIdvocAIte shutdown complete")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _wrap(payload: Dict[str, Any], assessment: CrisisAssessment) -> Dict[str, Any]:
        payload["assessment"] = {
            "level": assessment.crisis_level.value,
            "confidence": assessment.confidence_score,
            "safety_score": assessment.user_safety_score,
            "indicators": assessment.primary_indicators,
        }
        return payload
