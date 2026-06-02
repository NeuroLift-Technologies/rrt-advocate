"""
Intervention Manager
TOI-aware crisis intervention delivery.

Routes interventions through the Persona FusionEngine and OTOI middleware
to ensure every response is persona-blended and TOI-compliant.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from toi.toi_models import TOIConfig
from personas.fusion_engine import FusionEngine, EngineContext, DistressInput

logger = logging.getLogger(__name__)

# Avoid circular import
from enum import Enum


class ResponseStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUCCESSFUL = "successful"
    ESCALATED = "escalated"
    FAILED = "failed"


class InterventionManager:
    """
    Manages the deployment and tracking of crisis interventions.

    All interventions are routed through the FusionEngine to ensure
    persona-appropriate, TOI-compliant delivery.
    """

    def __init__(
        self,
        user_id: str,
        toi_config: Optional[TOIConfig] = None,
        fusion_engine: Optional[FusionEngine] = None,
    ):
        self.user_id = user_id
        self.toi_config = toi_config
        self.fusion_engine = fusion_engine or FusionEngine()
        self._active_interventions: Dict[str, Dict[str, Any]] = {}
        self._completed_interventions: List[Dict[str, Any]] = []
        logger.info("InterventionManager initialized for user %s", user_id)

    async def deploy_intervention(
        self,
        intervention_type: str,
        crisis_context: Dict[str, Any],
        urgency_level: str = "standard",
    ) -> Optional[Dict[str, Any]]:
        """
        Deploy a crisis intervention.

        Generates a FusionEngine-blended response for the intervention type
        and records it as an active intervention.

        Args:
            intervention_type: Named intervention (e.g., "breathing_exercise").
            crisis_context: Context from the CrisisAssessment.
            urgency_level: "standard" | "intensive" | "manual" | "emergency".

        Returns:
            Intervention record dict, or None if deployment failed.
        """
        intervention_id = str(uuid.uuid4())[:8]

        try:
            # Map intervention type to distress input for FusionEngine
            distress_input = self._map_intervention_to_distress(intervention_type)

            # Generate persona-blended response if TOI config is available
            system_prompt = ""
            template_response = self._get_intervention_template(intervention_type)

            if self.toi_config and self.fusion_engine:
                context = EngineContext(
                    distress_input=distress_input,
                    crisis_level_score=float(crisis_context.get("crisis_score", 0.5)),
                    session_context=crisis_context,
                )
                weights = self.fusion_engine.compute_weights(context, self.toi_config)
                blended = self.fusion_engine.blend_response(context, weights, self.toi_config)
                system_prompt = blended.system_prompt
                template_response = blended.template_response

            record = {
                "intervention_id": intervention_id,
                "intervention_type": intervention_type,
                "start_time": datetime.now(),
                "end_time": None,
                "status": ResponseStatus.ACTIVE,
                "urgency_level": urgency_level,
                "effectiveness_score": None,
                "user_feedback": None,
                "system_prompt": system_prompt,
                "template_response": template_response,
                "side_effects": [],
                "follow_up_required": urgency_level in ("intensive", "emergency"),
            }

            self._active_interventions[intervention_id] = record
            logger.info(
                "Deployed intervention %s (%s) urgency=%s",
                intervention_id, intervention_type, urgency_level,
            )
            return record

        except Exception as e:
            logger.error("Failed to deploy intervention %s: %s", intervention_type, e)
            return None

    async def evaluate_intervention(self, intervention_id: str) -> float:
        """
        Evaluate the effectiveness of a completed intervention.

        Returns a score between 0.0 and 1.0.
        """
        record = self._active_interventions.get(intervention_id)
        if not record:
            return 0.5  # Default to neutral if not found

        # Placeholder: effectiveness is derived from follow-up in future iterations
        # Currently returns a default based on intervention type
        effectiveness_defaults = {
            "breathing_exercise": 0.75,
            "grounding_technique": 0.72,
            "guided_meditation": 0.70,
            "cognitive_restructuring": 0.65,
            "intensive_grounding": 0.68,
            "crisis_counseling": 0.80,
            "emergency_stabilization": 0.85,
        }
        base = effectiveness_defaults.get(record.get("intervention_type", ""), 0.65)
        return base

    async def activate_emergency_protocols(self, assessment: Any):
        """Activate emergency-level protocols for BLACK crisis level."""
        logger.critical(
            "Emergency protocols activated for user %s at %s",
            self.user_id,
            datetime.now().isoformat(),
        )
        await self.deploy_intervention(
            intervention_type="emergency_stabilization",
            crisis_context={"crisis_score": 1.0, "emergency": True},
            urgency_level="emergency",
        )

    def _map_intervention_to_distress(
        self, intervention_type: str
    ) -> Optional[DistressInput]:
        mapping = {
            "breathing_exercise": DistressInput.EVERYTHING_HURTS_MELTDOWN,
            "grounding_technique": DistressInput.EVERYTHING_HURTS_MELTDOWN,
            "task_simplification": DistressInput.CANT_DO_BASIC_TASKS,
            "guided_meditation": DistressInput.EVERYTHING_HURTS_MELTDOWN,
            "cognitive_restructuring": DistressInput.CANT_STOP_SELF_BLAME,
            "break_scheduling": DistressInput.CANT_DO_BASIC_TASKS,
            "intensive_grounding": DistressInput.EVERYTHING_HURTS_MELTDOWN,
            "crisis_counseling": DistressInput.DONT_KNOW_SHUT_DOWN,
            "emergency_stabilization": DistressInput.DONT_KNOW_SHUT_DOWN,
        }
        return mapping.get(intervention_type)

    def _get_intervention_template(self, intervention_type: str) -> str:
        templates = {
            "breathing_exercise": (
                "Let's try a gentle breath together. "
                "In for 4 counts, hold for 4, out for 6. No pressure."
            ),
            "grounding_technique": (
                "Can you name 5 things you can see right now? "
                "We don't have to rush."
            ),
            "task_simplification": (
                "Let's forget everything except one small thing. "
                "What's the tiniest possible step?"
            ),
            "guided_meditation": (
                "Close your eyes if that feels okay. "
                "Just notice your breathing — nothing else required."
            ),
            "cognitive_restructuring": (
                "I notice the story you're telling yourself. "
                "Would it be okay to look at it together, gently?"
            ),
            "emergency_stabilization": (
                "I'm right here. You are safe. "
                "Breathe with me. We're going to get through this moment together."
            ),
        }
        return templates.get(intervention_type, "I'm here with you.")
