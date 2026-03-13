"""
De-Escalation Engine
Generates persona-blended de-escalation sequences for sustained crisis support.
"""

import asyncio
import logging
from typing import Any, Optional

from toi.toi_models import TOIConfig
from personas.fusion_engine import FusionEngine, EngineContext, DistressInput

logger = logging.getLogger(__name__)


class DeEscalationEngine:
    """
    Generates and manages de-escalation sequences.

    Uses the FusionEngine to produce persona-appropriate de-escalation
    content, prioritizing Ash and Myra for high-severity situations.
    """

    def __init__(
        self,
        toi_config: Optional[TOIConfig] = None,
        fusion_engine: Optional[FusionEngine] = None,
    ):
        self.toi_config = toi_config
        self.fusion_engine = fusion_engine or FusionEngine()

    async def start_de_escalation(self, assessment: Any):
        """
        Begin a de-escalation sequence for a crisis assessment.

        Args:
            assessment: CrisisAssessment from the assessor.
        """
        level_value = getattr(assessment.crisis_level, "value", "high")
        logger.info("Starting de-escalation sequence (level=%s)", level_value)

        if self.toi_config:
            context = EngineContext(
                distress_input=DistressInput.EVERYTHING_HURTS_MELTDOWN,
                crisis_level_score=assessment.confidence_score,
                session_context={"de_escalation": True},
            )
            weights = self.fusion_engine.compute_weights(context, self.toi_config)
            blended = self.fusion_engine.blend_response(context, weights, self.toi_config)
            logger.info(
                "De-escalation: dominant_persona=%s, template=%s",
                blended.dominant_persona,
                blended.template_response[:80],
            )

        # Brief de-escalation pause to avoid overwhelming the user
        await asyncio.sleep(0.5)
