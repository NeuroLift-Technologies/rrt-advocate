"""
RRT AIdvocAIte — Protective Layer of the Human-AI ElevAItion Foundation Solidarity Framework
NeuroLift Technologies

This module is the primary entry point for the RRT AIdvocAIte. It integrates:
  - TOI/OTOI Governance Layer (Constitutional Layer enforcement)
  - Persona Fusion Engine (5 OGs: Ash, Sol, Echo, Kai, Myra)
  - Tiered Activation Dialogue Tree (Stage 0–5)
  - 3-Layer Crisis Detection Engine (local-first, privacy-centric)
  - Response, Coordination, and Learning layers

Agency First. Local-First. Shame-Resistant. No Forced Productivity.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

# Ensure src/ is on the path when running directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# TOI/OTOI Governance Layer
from toi.toi_models import TOIConfig, ToneProfile, Pacing
from toi.toi_parser import TOIParser
from toi.otoi_middleware import OTOIMiddleware

# Persona Fusion Engine
from personas.fusion_engine import (
    FusionEngine,
    EngineContext,
    DistressInput,
    BlendedResponse,
    PersonaWeights,
)

# Tiered Activation Dialogue Tree
from dialogue.stages import ActivationStage, STAGE_CONFIGS
from dialogue.dialogue_tree import DialogueTree, DialogueState

# Crisis Detection Engine (3-layer local-first pipeline)
from crisis.detectors.crisis_detector import CrisisDetector, CrisisIndicators
from crisis.assessors.crisis_assessor import CrisisAssessor, CrisisLevel

# Response, Coordination, Learning
from response.interventions.intervention_manager import InterventionManager, ResponseStatus
from response.de_escalation.de_escalation_engine import DeEscalationEngine
from coordination.supervisor.supervisor_interface import SupervisorInterface, LocalSupervisor
from learning.patterns.pattern_analyzer import PatternAnalyzer


# ============================================================================
# Core Data Models (retained for API compatibility; CrisisLevel re-exported)
# ============================================================================

class _CrisisLevel(Enum):
    """Re-exported here for backwards compatibility."""
    GREEN = "stable"
    YELLOW = "elevated"
    ORANGE = "high"
    RED = "critical"
    BLACK = "emergency"


@dataclass
class CrisisAssessment:
    """Comprehensive crisis assessment data structure."""
    timestamp: datetime
    crisis_level: CrisisLevel
    primary_indicators: List[str]
    secondary_indicators: List[str]
    confidence_score: float
    estimated_duration: Optional[timedelta]
    recommended_interventions: List[str]
    escalation_threshold: float
    user_safety_score: float
    context_factors: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterventionResponse:
    """Response data from a crisis intervention."""
    intervention_id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: ResponseStatus
    effectiveness_score: Optional[float]
    user_feedback: Optional[str]
    side_effects: List[str] = field(default_factory=list)
    follow_up_required: bool = False


# ============================================================================
# RRT AIdvocAIte — Main Class
# ============================================================================

class RRTAdvocate:
    """
    RRT AIdvocAIte — Rapid Response Team Advocate.

    The Protective Layer of the Solidarity Framework.

    Primary interaction flow:
      1. Initialize with a user TOI config (or use system defaults).
      2. Call process_message() for conversational interaction.
      3. The Advocate routes through: CDE → TOI validation → FusionEngine → OTOI filter.
      4. Stage 1 consent is always required before full RRT deployment.
      5. Silent Mode is always available; no forced productivity.

    Architecture:
      - TOI/OTOI Governance: Every response is filtered through the user's
        Terms of Interaction. No persona may override the contract.
      - Persona Fusion Engine: Dynamically blends Ash/Sol/Echo/Kai/Myra based
        on the specific flavor of neurodivergent distress detected.
      - 3-Layer CDE: Keyword analysis, sentiment tracking, behavioral patterns —
        all running locally with zero external API calls.
      - Tiered Dialogue Tree: Stage 0–5 journey with Agency First design.
    """

    def __init__(
        self,
        user_id: str,
        config_path: str = "config/crisis_thresholds.yaml",
        toi_config: Optional[TOIConfig] = None,
        supervisor_interface: Optional[SupervisorInterface] = None,
    ):
        """
        Initialize the RRT AIdvocAIte.

        Args:
            user_id: Unique identifier for the user (used for local pattern storage).
            config_path: Path to crisis detection configuration YAML.
            toi_config: User's Terms of Interaction. Uses system defaults if None.
            supervisor_interface: Supervisor AI interface (defaults to LocalSupervisor).
        """
        self.user_id = user_id
        self.config_path = config_path

        # TOI/OTOI Governance
        self.toi_config = toi_config or TOIParser().default_config()
        self.otoi = OTOIMiddleware(self.toi_config)

        # Core components
        self.fusion_engine = FusionEngine()
        self.crisis_detector = CrisisDetector(config_path)
        self.crisis_assessor = CrisisAssessor(user_id, config_path)
        self.intervention_manager = InterventionManager(
            user_id, self.toi_config, self.fusion_engine
        )
        self.de_escalation_engine = DeEscalationEngine(self.toi_config, self.fusion_engine)
        self.supervisor = supervisor_interface or LocalSupervisor()
        self.pattern_analyzer = PatternAnalyzer(user_id)

        # Tiered Dialogue Tree
        self.dialogue_tree = DialogueTree(
            toi_config=self.toi_config,
            otoi_middleware=self.otoi,
            fusion_engine=self.fusion_engine,
        )

        # State management
        self.is_monitoring = False
        self.current_crisis: Optional[CrisisAssessment] = None
        self.active_interventions: List[InterventionResponse] = []
        self.crisis_history: List[CrisisAssessment] = []

        # Performance tracking
        self.response_times: List[float] = []
        self.intervention_success_rate: float = 0.0
        self.last_assessment_time: Optional[datetime] = None

        self.logger = logging.getLogger(f"RRTAdvocate-{user_id}")
        self._setup_logging()
        self.logger.info("RRT AIdvocAIte initialized for user %s (TOI: %s)", user_id, self.toi_config.tone_profile.value)

    def _setup_logging(self):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    # -------------------------------------------------------------------------
    # Primary interaction method (new — TOI-aware conversational interface)
    # -------------------------------------------------------------------------

    async def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Primary interaction entry point for conversational use.

        Routes user messages through the full pipeline:
          CDE analysis → TOI validation → Dialogue Tree → FusionEngine → OTOI filter

        Args:
            user_message: Free-form text from the user.

        Returns:
            Dict with response text, persona context, stage info, and crisis data.
        """
        start_time = datetime.now()

        # Step 1: Run 3-layer CDE analysis (local-first)
        indicators = await self.crisis_detector.detect_crisis_indicators(user_message)
        assessment = await self.crisis_assessor.assess_crisis(indicators)

        # Update crisis tracking
        self.last_assessment_time = datetime.now()
        crisis_score = assessment.confidence_score

        # Update dialogue tree's crisis awareness
        self.dialogue_tree.crisis_level_score = crisis_score

        # Step 2: Stage 1 consent gate — Agency First
        if not self.otoi.check_consent():
            # Return the Stage 1 entry prompt — always pause for consent
            self.dialogue_tree.state.current_stage = ActivationStage.STAGE_1_ENTRY
            response = self.dialogue_tree._build_stage_response()
            response["response_text"] = STAGE_CONFIGS[ActivationStage.STAGE_1_ENTRY].prompt
            response["crisis_level"] = assessment.crisis_level.value
            response["requires_consent"] = True
            return response

        # Step 3: Handle self-harm risk — immediate escalation regardless of stage
        if indicators.self_harm_risk:
            await self._emergency_escalation(assessment)
            return self._build_emergency_response(assessment)

        # Step 4: Escalate to crisis handling if above threshold
        if assessment.crisis_level not in (CrisisLevel.GREEN,):
            await self._handle_crisis(assessment)

        # Step 5: Route through dialogue tree
        dialogue_response = self.dialogue_tree.process_free_text(user_message)

        # Record performance
        elapsed = (datetime.now() - start_time).total_seconds()
        self.response_times.append(elapsed)

        # Build unified response
        return {
            **dialogue_response,
            "response_text": dialogue_response.get("prompt", "I'm here with you."),
            "crisis_level": assessment.crisis_level.value,
            "crisis_confidence": assessment.confidence_score,
            "response_time_seconds": round(elapsed, 3),
        }

    async def select_stage_option(
        self, option_key: str, free_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user's selection from the current stage's options.

        Args:
            option_key: The key of the selected option (e.g., "yes", "meltdown").
            free_text: Optional accompanying free text.

        Returns:
            Updated stage response dict.
        """
        return self.dialogue_tree.process_option_selection(option_key, free_text)

    # -------------------------------------------------------------------------
    # Crisis monitoring (retained for background monitoring use cases)
    # -------------------------------------------------------------------------

    async def start_monitoring(self) -> bool:
        """Start continuous crisis monitoring."""
        if self.is_monitoring:
            self.logger.warning("Monitoring already active")
            return True
        try:
            self.is_monitoring = True
            asyncio.create_task(self._monitoring_loop())
            await self.supervisor.notify_advocate_status("rrt", "monitoring_active", self.user_id)
            return True
        except Exception as e:
            self.logger.error("Failed to start monitoring: %s", e)
            self.is_monitoring = False
            return False

    async def stop_monitoring(self) -> bool:
        """Stop crisis monitoring."""
        if not self.is_monitoring:
            return True
        try:
            self.is_monitoring = False
            for intervention in self.active_interventions:
                if intervention.status == ResponseStatus.ACTIVE:
                    await self._complete_intervention(intervention)
            await self.supervisor.notify_advocate_status("rrt", "monitoring_stopped", self.user_id)
            return True
        except Exception as e:
            self.logger.error("Error stopping monitoring: %s", e)
            return False

    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while self.is_monitoring:
            try:
                assessment = await self.assess_current_state()
                if assessment.crisis_level != CrisisLevel.GREEN:
                    await self._handle_crisis(assessment)
                await self.pattern_analyzer.update_patterns(assessment)
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error("Error in monitoring loop: %s", e)
                await asyncio.sleep(5)

    async def assess_current_state(self, message: str = "") -> CrisisAssessment:
        """Perform a crisis assessment on an optional message."""
        start = datetime.now()
        try:
            indicators = await self.crisis_detector.detect_crisis_indicators(message)
            assessment = await self.crisis_assessor.assess_crisis(indicators)
            self.response_times.append((datetime.now() - start).total_seconds())
            self.last_assessment_time = datetime.now()
            return assessment
        except Exception as e:
            self.logger.error("Crisis assessment failed: %s", e)
            return CrisisAssessment(
                timestamp=datetime.now(),
                crisis_level=CrisisLevel.GREEN,
                primary_indicators=[],
                secondary_indicators=[],
                confidence_score=0.0,
                estimated_duration=None,
                recommended_interventions=[],
                escalation_threshold=0.8,
                user_safety_score=1.0,
            )

    async def _handle_crisis(self, assessment: CrisisAssessment):
        """Route crisis to appropriate intervention tier."""
        self.current_crisis = assessment
        self.crisis_history.append(assessment)
        self.logger.warning(
            "Crisis detected: %s (confidence=%.2f)",
            assessment.crisis_level.value,
            assessment.confidence_score,
        )

        try:
            if assessment.user_safety_score < 0.3:
                await self._emergency_escalation(assessment)
                return

            if assessment.crisis_level in (CrisisLevel.YELLOW, CrisisLevel.ORANGE):
                await self._deploy_standard_interventions(assessment)
            elif assessment.crisis_level == CrisisLevel.RED:
                await self._deploy_intensive_interventions(assessment)
            elif assessment.crisis_level == CrisisLevel.BLACK:
                await self._emergency_escalation(assessment)

            await self.supervisor.handle_crisis("rrt", assessment, self.user_id)

        except Exception as e:
            self.logger.error("Crisis handling failed: %s", e)
            await self._emergency_escalation(assessment)

    async def _deploy_standard_interventions(self, assessment: CrisisAssessment):
        for intervention_type in assessment.recommended_interventions:
            try:
                record = await self.intervention_manager.deploy_intervention(
                    intervention_type=intervention_type,
                    crisis_context=assessment.context_factors,
                    urgency_level="standard",
                )
                if record:
                    self.logger.info("Deployed: %s", intervention_type)
            except Exception as e:
                self.logger.error("Failed to deploy %s: %s", intervention_type, e)

    async def _deploy_intensive_interventions(self, assessment: CrisisAssessment):
        de_esc_task = asyncio.create_task(
            self.de_escalation_engine.start_de_escalation(assessment)
        )
        tasks = [
            asyncio.create_task(
                self.intervention_manager.deploy_intervention(
                    intervention_type=t,
                    crisis_context=assessment.context_factors,
                    urgency_level="intensive",
                )
            )
            for t in assessment.recommended_interventions
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        await de_esc_task

    async def _emergency_escalation(self, assessment: CrisisAssessment):
        self.logger.critical("EMERGENCY ESCALATION: %s", assessment.crisis_level.value)
        await self.supervisor.emergency_escalation("rrt", assessment, self.user_id)
        await self.intervention_manager.activate_emergency_protocols(assessment)

    def _build_emergency_response(self, assessment: CrisisAssessment) -> Dict[str, Any]:
        """Build a crisis-safe emergency response."""
        return {
            "stage": "EMERGENCY",
            "response_text": (
                "I'm here with you right now. "
                "You are not alone. "
                "If you're in immediate danger, please reach out to a crisis line: "
                "988 (Suicide & Crisis Lifeline) or text HOME to 741741."
            ),
            "crisis_level": assessment.crisis_level.value,
            "emergency": True,
            "crisis_resources": {
                "988_lifeline": "Call or text 988",
                "crisis_text_line": "Text HOME to 741741",
                "international_association_for_suicide_prevention": "https://www.iasp.info/resources/Crisis_Centres/",
            },
        }

    async def _complete_intervention(self, intervention: InterventionResponse):
        try:
            intervention.end_time = datetime.now()
            effectiveness = await self.intervention_manager.evaluate_intervention(
                intervention.intervention_id
            )
            intervention.effectiveness_score = effectiveness
            self._update_success_rate()
            if intervention in self.active_interventions:
                self.active_interventions.remove(intervention)
        except Exception as e:
            self.logger.error("Failed to complete intervention: %s", e)

    def _update_success_rate(self):
        completed = [
            i for i in self.active_interventions
            if i.end_time and i.effectiveness_score is not None
        ]
        if completed:
            success = sum(1 for i in completed if (i.effectiveness_score or 0) >= 0.7)
            self.intervention_success_rate = success / len(completed)

    # -------------------------------------------------------------------------
    # Status and lifecycle
    # -------------------------------------------------------------------------

    async def get_status_report(self) -> Dict[str, Any]:
        """Return a comprehensive status report."""
        return {
            "user_id": self.user_id,
            "monitoring_active": self.is_monitoring,
            "toi_config": {
                "tone_profile": self.toi_config.tone_profile.value,
                "pacing": self.toi_config.pacing.value,
                "consent_given": self.toi_config.consent_given,
                "silent_mode_preferred": self.toi_config.silent_mode_preferred,
                "allow_task_loops": self.toi_config.allow_task_loops,
            },
            "current_crisis": {
                "level": self.current_crisis.crisis_level.value if self.current_crisis else "none",
                "confidence": self.current_crisis.confidence_score if self.current_crisis else 0.0,
            },
            "dialogue_state": self.dialogue_tree.get_session_summary(),
            "active_interventions": len(self.active_interventions),
            "crisis_history_count": len(self.crisis_history),
            "performance": {
                "avg_response_time": (
                    sum(self.response_times[-100:]) / len(self.response_times[-100:])
                    if self.response_times else 0.0
                ),
                "success_rate": self.intervention_success_rate,
                "last_assessment": (
                    self.last_assessment_time.isoformat()
                    if self.last_assessment_time else None
                ),
            },
            "otoi_session": self.otoi.get_session_summary(),
            "pattern_summary": self.pattern_analyzer.get_summary(),
        }

    async def manual_intervention(
        self, intervention_type: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Manually trigger a specific intervention."""
        try:
            record = await self.intervention_manager.deploy_intervention(
                intervention_type=intervention_type,
                crisis_context=context or {},
                urgency_level="manual",
            )
            return record is not None
        except Exception as e:
            self.logger.error("Manual intervention failed: %s", e)
            return False

    async def shutdown(self):
        """Gracefully shut down the RRT AIdvocAIte."""
        self.logger.info("Shutting down RRT AIdvocAIte")
        await self.stop_monitoring()
        await self.pattern_analyzer.save_patterns()
        status = await self.get_status_report()
        self.logger.info("Final status: %s", json.dumps(status, indent=2, default=str))
        self.logger.info("RRT AIdvocAIte shutdown complete")


# ============================================================================
# Factory Functions
# ============================================================================

async def create_rrt_advocate(
    user_id: str,
    config_path: str = "config/crisis_thresholds.yaml",
    toi_config: Optional[TOIConfig] = None,
    supervisor_interface: Optional[SupervisorInterface] = None,
) -> RRTAdvocate:
    """
    Factory function to create and initialize an RRT AIdvocAIte.

    Args:
        user_id: Unique identifier for the user.
        config_path: Path to crisis detection configuration.
        toi_config: User's TOI contract. Defaults to system defaults.
        supervisor_interface: Supervisor AI interface. Defaults to LocalSupervisor.

    Returns:
        Initialized RRTAdvocate instance.
    """
    advocate = RRTAdvocate(user_id, config_path, toi_config, supervisor_interface)
    return advocate


def create_toi_config(
    tone_profile: str = "supportive_default",
    pacing: str = "standard",
    cognitive_scaffolding_level: int = 2,
    silent_mode_preferred: bool = False,
    allow_timers: bool = True,
    preferred_personas: Optional[List[str]] = None,
    excluded_personas: Optional[List[str]] = None,
) -> TOIConfig:
    """
    Helper to create a TOI configuration.

    Args:
        tone_profile: "supportive_default" | "minimal" | "directive" | "therapeutic_reflective"
        pacing: "standard" | "slow" | "very_slow"
        cognitive_scaffolding_level: 0–3
        silent_mode_preferred: If True, activates Silent Mode by default.
        allow_timers: If False, disables all timer-based interactions.
        preferred_personas: List of persona names to boost.
        excluded_personas: List of persona names to exclude.

    Returns:
        TOIConfig instance.
    """
    return TOIParser().parse_from_dict({
        "tone_profile": tone_profile,
        "pacing": pacing,
        "cognitive_scaffolding_level": cognitive_scaffolding_level,
        "silent_mode_preferred": silent_mode_preferred,
        "allow_timers": allow_timers,
        "allow_task_loops": False,  # Always False — no forced productivity
        "preferred_personas": preferred_personas or [],
        "excluded_personas": excluded_personas or [],
    })


# ============================================================================
# Main execution (demo / smoke test)
# ============================================================================

async def main():
    """Demo of the RRT AIdvocAIte Solidarity Framework integration."""
    print("=" * 60)
    print("RRT AIdvocAIte — Protective Layer of the Solidarity Framework")
    print("=" * 60)

    # Create with a minimal TOI config for demo
    toi = create_toi_config(tone_profile="supportive_default", pacing="slow")
    advocate = await create_rrt_advocate("demo_user_001", toi_config=toi)

    print("\n[Stage 0: Passive presence — Advocate initialized]")

    # Simulate a user message that triggers the entry prompt
    print("\n[User: 'I'm really struggling today']")
    response = await advocate.process_message("I'm really struggling today")
    print(f"[Stage: {response.get('stage')}]")
    print(f"[Prompt: {response.get('response_text')}]")
    print(f"[Options: {[opt['display_text'] for opt in response.get('options', [])]}]")

    # User gives consent
    print("\n[User selects: 'Yes, I'd like support']")
    response = await advocate.select_stage_option("yes")
    print(f"[Stage: {response.get('stage')}]")
    print(f"[Prompt: {response.get('response_text') or response.get('prompt')}]")

    # User selects distress type: meltdown
    print("\n[User selects: 'Everything hurts / I'm in meltdown']")
    response = await advocate.select_stage_option("meltdown")
    print(f"[Stage: {response.get('stage')}]")
    print(f"[Response: {response.get('response_text') or response.get('prompt')}]")
    if "persona_context" in response:
        pc = response["persona_context"]
        print(f"[Dominant Persona: {pc.get('dominant_persona')}]")
        print(f"[Active Personas: {pc.get('active_personas')}]")
        print(f"[Weights: {pc.get('weights')}]")

    # Final status
    print("\n[Status Report]")
    status = await advocate.get_status_report()
    print(json.dumps({
        "toi_config": status["toi_config"],
        "dialogue_state": status["dialogue_state"],
        "otoi_session": status["otoi_session"],
    }, indent=2))

    await advocate.shutdown()
    print("\n[RRT AIdvocAIte demo complete]")


if __name__ == "__main__":
    asyncio.run(main())
