"""
TOI Middleware - Request Filter Before Crisis Response
RRT Advocate - Protective Layer of the Solidarity Framework

Every interaction within the RRT must pass through this middleware.
Blocks or modifies responses that violate the user's TOI.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .toi_parser import TOIConfig, TOIParser, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class InteractionContext:
    """Context for an RRT interaction, TOI-filtered"""
    user_id: str
    toi_config: TOIConfig
    distress_input: Optional[str] = None
    stage: int = 0
    consent_given: bool = False
    silent_mode_requested: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MiddlewareResult:
    """Result of TOI middleware check"""
    allowed: bool
    context: Optional[InteractionContext] = None
    block_reason: Optional[str] = None
    modifications: Dict[str, Any] = field(default_factory=dict)


class TOIMiddleware:
    """
    Middleware that enforces TOI before any crisis response is generated.
    Implements Agency First and anti-gaslight design.
    """

    def __init__(self, toi_config: Optional[TOIConfig] = None):
        self.toi_config = toi_config
        self.parser = TOIParser()

    def load_toi(self, config_source) -> ValidationResult:
        """Load and validate TOI config."""
        result = self.parser.parse(config_source)
        if result.valid and result.config:
            self.toi_config = result.config
        return result

    def check_intervention_allowed(
        self,
        user_id: str,
        distress_input: Optional[str] = None,
        stage: int = 0,
        consent_given: bool = False,
        silent_mode_requested: bool = False,
    ) -> MiddlewareResult:
        """
        Check if intervention is allowed under the user's TOI.

        Agency First: If consent_required_before_intervention is True,
        stage must be >= 1 and consent_given must be True for stage >= 2.
        """
        if not self.toi_config:
            return MiddlewareResult(
                allowed=False,
                block_reason="No TOI configuration loaded; cannot proceed without user contract",
            )

        ctx = InteractionContext(
            user_id=user_id,
            toi_config=self.toi_config,
            distress_input=distress_input,
            stage=stage,
            consent_given=consent_given,
            silent_mode_requested=silent_mode_requested,
        )

        modifications: Dict[str, Any] = {}

        # Agency First: Stage 0/1 must ask for consent before deploying full RRT
        if self.toi_config.safety.consent_required_before_intervention:
            if stage < 1:
                return MiddlewareResult(
                    allowed=False,
                    context=ctx,
                    block_reason="Stage 1 Entry Prompt required: must ask for consent before RRT",
                    modifications={"suggested_action": "present_stage1_consent_prompt"},
                )
            if stage >= 2 and not consent_given:
                return MiddlewareResult(
                    allowed=False,
                    context=ctx,
                    block_reason="User consent required before Stage 2+ intervention",
                    modifications={"suggested_action": "re_present_consent"},
                )

        # No Forced Productivity: if user indicates burnout, block task loops
        if self.toi_config.safety.no_productivity_pressure and distress_input:
            burnout_indicators = [
                "everything hurts",
                "meltdown",
                "burnout",
                "can't do",
                "shut down",
                "don't know",
            ]
            input_lower = distress_input.lower()
            if any(ind in input_lower for ind in burnout_indicators):
                modifications["avoid_task_loops"] = True
                modifications["prefer_ash_myra"] = True

        # Silent Mode: if requested, ensure Myra-weighted, calm visuals
        if silent_mode_requested and self.toi_config.safety.silent_mode_available:
            modifications["silent_mode"] = True
            modifications["persona_override"] = {"myra": 1.0}
            modifications["no_timers"] = True
            modifications["calm_visuals_only"] = True

        return MiddlewareResult(allowed=True, context=ctx, modifications=modifications)

    def validate_response_content(self, content: str) -> bool:
        """
        Validate response content against TOI (e.g. length, forbidden patterns).
        Returns True if content is TOI-compliant.
        """
        if not self.toi_config:
            return True  # No TOI loaded; allow
        if self.toi_config.safety.max_message_length and len(content) > self.toi_config.safety.max_message_length:
            return False
        # Anti-gaslight: reject obviously judgmental phrases (extend as needed)
        forbidden = ["you should be", "you're lazy", "just try harder", "it's your fault"]
        lower = content.lower()
        if any(p in lower for p in forbidden):
            return False
        return True

    def apply_toi_to_response(
        self, response_draft: str, context: InteractionContext
    ) -> str:
        """
        Apply TOI constraints to a response draft (e.g., truncate if max length).
        """
        if not context.toi_config.safety.max_message_length:
            return response_draft

        max_len = context.toi_config.safety.max_message_length
        if len(response_draft) <= max_len:
            return response_draft

        # Truncate gently - at word boundary
        truncated = response_draft[: max_len - 3].rsplit(" ", 1)[0] + "..."
        return truncated
