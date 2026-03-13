"""
RRT AIdvocAIte - Rapid Response Team Advocate
Protective Layer of the HAIEF Solidarity Framework

TOI-compliant, dynamically weighted, multi-persona orchestration engine.
Every interaction passes through TOI middleware; responses are blended
via the Persona Fusion Engine (Ash, Sol, Echo, Kai, Myra).
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# TOI-OTOI Governance
from .governance.toi_parser import TOIParser, TOIConfig, TonePreference
from .governance.toi_middleware import TOIMiddleware
from .governance.otoi_coordinator import OTOICoordinator

# Persona Fusion Engine
from .personas.fusion_engine import PersonaFusionEngine
from .personas.distress_mapper import PersonaWeights

# Tiered Dialogue Tree
from .dialogue.stage_handlers import StageHandlers, DialogueStage, StageContext
from .dialogue.stage1_entry import Stage1EntryHandler

# Tone Profiles & Prompt Builder
from .tone.tone_profiles import get_tone_profile
from .tone.prompt_builder import PromptBuilder

# 3-Layer Crisis Detection Engine (local-first)
from .crisis.cde_pipeline import CDEPipeline, CDEOutput

# Optional supervisor interface for ecosystem integration
# Abstract - implement when NeuroLift Supervisor is available
try:
    from .coordination.supervisor_interface import SupervisorInterface
except ImportError:
    SupervisorInterface = None  # type: ignore


@dataclass
class RRTResponse:
    """TOI-compliant response from the RRT Advocate"""
    content: str
    persona_weights: Dict[str, float]
    tone_profile_used: str
    silent_mode_active: bool
    prompt_used: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class RRTAdvocate:
    """
    RRT AIdvocAIte - Protective Layer of the Solidarity Framework

    - TOI-gated: Every interaction passes through TOI middleware
    - Persona Fusion: Dynamic blend of Ash, Sol, Echo, Kai, Myra
    - Tiered Dialogue: Stage 1 consent first (Agency First)
    - 3-Layer CDE: Local-first crisis detection
    """

    def __init__(
        self,
        user_id: str,
        toi_config: Optional[TOIConfig] = None,
        toi_config_path: Optional[str] = None,
        supervisor_interface: Optional[Any] = None,
    ):
        """
        Initialize RRT Advocate with user-specific configuration.

        Args:
            user_id: Unique identifier for the user
            toi_config: Parsed TOI configuration (or load from path)
            toi_config_path: Path to TOI YAML (e.g. config/toi_schema.yaml)
            supervisor_interface: Optional Supervisor AI interface for escalation
        """
        self.user_id = user_id
        self.toi_config = toi_config or self._load_toi(toi_config_path)
        self.supervisor = supervisor_interface

        # TOI-OTOI Governance
        self.toi_middleware = TOIMiddleware(self.toi_config)
        self.otoi_coordinator = OTOICoordinator(self.toi_config)

        # Persona Fusion Engine
        self.fusion_engine = PersonaFusionEngine()

        # Tiered Dialogue Tree
        self.stage_handlers = StageHandlers(self.fusion_engine)

        # Tone & Prompt
        self.prompt_builder = PromptBuilder()

        # 3-Layer CDE (local-first)
        self.cde_pipeline = CDEPipeline()

        # State
        self._current_stage = DialogueStage.STAGE_0
        self._stage_context: Optional[StageContext] = None
        self._consent_granted = False
        self._interaction_history: List[Dict[str, Any]] = []

        # Logging
        self.logger = logging.getLogger(f"RRTAdvocate-{user_id}")
        self._setup_logging()

        self.logger.info(
            f"RRT Advocate initialized for {user_id} "
            f"(TOI tone: {self.toi_config.tone.value})"
        )

    def _load_toi(self, path: Optional[str]) -> TOIConfig:
        """Load TOI from path or return safe defaults."""
        parser = TOIParser()
        if path:
            try:
                result = parser.parse(path)
                if result.valid and result.config:
                    return result.config
            except (FileNotFoundError, OSError) as e:
                self.logger.warning(f"TOI file not found or unreadable: {path} - using defaults ({e})")
        return parser.get_default_config()

    def _setup_logging(self):
        """Configure logging for crisis response tracking"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    # -------------------------------------------------------------------------
    # Stage 1: Agency First - Consent before activation
    # -------------------------------------------------------------------------

    def get_stage1_entry_prompt(self) -> str:
        """
        Get Stage 1 entry prompt (Agency First).
        User must consent before full RRT Advocate activation.
        """
        tone_name = self.toi_config.tone.value
        return self.stage_handlers.get_stage1_prompt(tone_variant=tone_name)

    def process_stage1_consent(self, user_response: str) -> bool:
        """
        Process Stage 1 user response. Returns True if consent granted.
        Non-judgmental: 'no' or deferral is honored without pressure.
        """
        result = self.stage_handlers.process_stage1_response(user_response)
        self._consent_granted = result.consent_granted
        if result.consent_granted:
            self._current_stage = DialogueStage.STAGE_2
            self.logger.info("User consented to RRT activation")
        else:
            self._current_stage = DialogueStage.STAGE_0
            self.logger.info("User declined or deferred RRT activation")
        return result.consent_granted

    # -------------------------------------------------------------------------
    # Stage 2: Distress Assessment → Persona Weights
    # -------------------------------------------------------------------------

    def get_stage2_options(self) -> List[Dict[str, Any]]:
        """Get Stage 2 distress options for UI/backend binding."""
        from .dialogue.distress_options import get_stage2_options
        return get_stage2_options()

    def process_stage2_selection(self, distress_option_id: str) -> Optional[StageContext]:
        """
        Process Stage 2 distress selection.
        Maps to persona weights; determines Silent Mode.
        Returns StageContext for Stage 3 response generation.
        """
        ctx = self.stage_handlers.process_stage2_selection(distress_option_id)
        self._stage_context = ctx
        self._current_stage = ctx.stage
        return ctx

    # -------------------------------------------------------------------------
    # Stage 3: Persona-Weighted Response Generation
    # -------------------------------------------------------------------------

    def generate_response(
        self,
        user_message: str,
        distress_option_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> RRTResponse:
        """
        Generate TOI-compliant, persona-blended response.

        All responses pass through TOI middleware.
        Persona weights come from Stage 2 selection or CDE supplement.
        """
        # Run CDE (local-first) for supplemental signals
        self.cde_pipeline.add_interaction(user_message)
        cde_output = self.cde_pipeline.run(user_message)

        # Build CDE supplement for fusion (optional weight adjustments)
        cde_supplement = self._cde_to_supplement(cde_output)

        # Get persona weights
        if self._stage_context and self._stage_context.persona_weights:
            weights_dict = self._stage_context.persona_weights
        elif distress_option_id:
            from .personas.distress_mapper import get_persona_weights_for_distress
            weights_dict = get_persona_weights_for_distress(distress_option_id)
        else:
            fusion_result = self.fusion_engine.fuse(
                stage2_input=user_message,
                force_silent_mode=self._stage_context.silent_mode_active if self._stage_context else False,
                cde_supplement=cde_supplement,
            )
            weights_dict = fusion_result.weights.to_dict()

        # OTOI filter: respect TOI allowed_personas
        weights_dict = self.otoi_coordinator.filter_persona_weights(weights_dict)

        # TOI middleware: validate response would be compliant
        tone_profile_id = self.toi_config.tone.value
        tone_profile = get_tone_profile(tone_profile_id)

        # Build prompt for LLM (modular assembly)
        # In production, this would be sent to an LLM; here we return a template
        prompt = self.prompt_builder.build(
            persona_weights=weights_dict,
            tone_profile=tone_profile,
            user_message=user_message,
            silent_mode=self._stage_context.silent_mode_active if self._stage_context else False,
        )

        # Placeholder content (replace with actual LLM call in production)
        content = self._placeholder_response(
            weights_dict, tone_profile, user_message
        )

        # Final TOI check: block if non-compliant
        if not self.toi_middleware.validate_response_content(content):
            content = "[Response adjusted for TOI compliance. Supportive default.]"

        return RRTResponse(
            content=content,
            persona_weights=weights_dict,
            tone_profile_used=tone_profile_id,
            silent_mode_active=self._stage_context.silent_mode_active if self._stage_context else False,
            prompt_used=prompt[:500] + "..." if len(prompt) > 500 else prompt,
        )

    def _cde_to_supplement(self, cde: CDEOutput) -> Dict[str, float]:
        """Map CDE output to fusion engine supplement keys."""
        supplement = {}
        if cde.dominant_semantic_field:
            supplement[cde.dominant_semantic_field] = cde.combined_risk_score * 0.3
        if cde.polarity_drop_detected:
            supplement["negative_self_talk"] = 0.2
            supplement["overwhelm"] = 0.15
        if cde.looping_detected:
            supplement["hyperfocus_loop"] = 0.25
        return supplement

    def _placeholder_response(
        self,
        weights: Dict[str, float],
        tone_profile: Any,
        user_message: str,
    ) -> str:
        """
        Placeholder when no LLM is configured.
        In production, replace with actual LLM call using prompt_builder output.
        """
        dominant = max(weights, key=weights.get) if weights else "myra"
        if weights.get("myra", 0) >= 0.7:
            return "Here. No rush. Whenever you're ready."
        if dominant == "ash":
            return "That sounds really hard. It makes sense that you'd feel that way. You don't have to have answers."
        if dominant == "sol":
            return "One thing. What's the smallest next action you could take right now?"
        if dominant == "echo":
            return "What would you say to a friend in this situation?"
        if dominant == "kai":
            return "Loops can be redirected. What's one small shift you could make?"
        return "I'm here with you. Take your time."

    # -------------------------------------------------------------------------
    # CDE: Local-First Crisis Detection
    # -------------------------------------------------------------------------

    def assess_crisis_indicators(self, text: str) -> CDEOutput:
        """
        Run 3-layer CDE on input text.
        All processing is local; no cloud default.
        """
        return self.cde_pipeline.run(text)

    # -------------------------------------------------------------------------
    # Status & Integration
    # -------------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """Get current status for monitoring and debugging."""
        return {
            "user_id": self.user_id,
            "current_stage": self._current_stage.name,
            "consent_granted": self._consent_granted,
            "toi_tone": self.toi_config.tone.value,
            "interaction_count": len(self._interaction_history),
        }

    async def notify_supervisor(self, event: str, data: Dict[str, Any]) -> None:
        """Notify Supervisor AI if configured (ecosystem integration)."""
        if self.supervisor and hasattr(self.supervisor, "notify"):
            try:
                await self.supervisor.notify(
                    advocate_id="rrt",
                    event=event,
                    data=data,
                    user_id=self.user_id,
                )
            except Exception as e:
                self.logger.warning(f"Supervisor notification failed: {e}")


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_rrt_advocate(
    user_id: str,
    toi_config_path: Optional[str] = "config/toi_schema.yaml",
    toi_config: Optional[TOIConfig] = None,
    supervisor_interface: Optional[Any] = None,
) -> RRTAdvocate:
    """
    Factory to create and initialize RRT Advocate.

    Args:
        user_id: Unique user identifier
        toi_config_path: Path to TOI YAML (optional)
        toi_config: Pre-parsed TOI config (overrides path)
        supervisor_interface: Optional Supervisor AI interface

    Returns:
        Initialized RRT Advocate
    """
    return RRTAdvocate(
        user_id=user_id,
        toi_config=toi_config,
        toi_config_path=toi_config_path,
        supervisor_interface=supervisor_interface,
    )
