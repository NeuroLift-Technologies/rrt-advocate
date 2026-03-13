from __future__ import annotations

from typing import Any

from .cde import CrisisDetectionEngine
from .config import DEFAULT_CDE_CONFIG_PATH, DEFAULT_TOI_CONFIG_PATH, load_yaml
from .models import ActivationStage, DistressInput, InteractionContext, StageResponse, TOIConfig, ToneProfile
from .personas import PERSONA_SUMMARIES, PersonaFusionEngine
from .toi import OTOIGovernor, TOIParser
from .tone_profiles import ToneProfileRenderer


class RRTAdvocate:
    def __init__(
        self,
        user_id: str,
        config_path: str | None = None,
        toi_config_path: str | None = None,
    ):
        self.user_id = user_id
        self.cde_config = load_yaml(config_path or DEFAULT_CDE_CONFIG_PATH)
        self.toi_policy = load_yaml(toi_config_path or DEFAULT_TOI_CONFIG_PATH)
        self.toi_parser = TOIParser(self.toi_policy)
        self.otoi_governor = OTOIGovernor()
        self.cde = CrisisDetectionEngine(self.cde_config)
        self.fusion_engine = PersonaFusionEngine(self.cde_config)
        self.tone_renderer = ToneProfileRenderer(self.toi_policy)
        self.stage_definitions = self.cde_config.get("activation_stages", {})
        self.last_response: StageResponse | None = None
        self.is_monitoring = False

    def create_entry_prompt(self, toi_config: dict[str, Any] | TOIConfig | None = None) -> StageResponse:
        toi = self.toi_parser.parse(toi_config)
        response = StageResponse(
            stage=ActivationStage.STAGE_1_ENTRY,
            message=self.tone_renderer.render_entry_prompt(toi),
            tone_profile=toi.tone,
            active_personas=[],
            persona_weights={},
            recommended_actions=[],
            silent_mode=False,
            consent_required=toi.safety_boundaries.require_explicit_consent,
            metadata={
                "governance": self.toi_policy.get("governance", {}),
                "stage": self.stage_definitions.get("stage_1", {}),
            },
        )
        self.last_response = response
        return response

    def assess_interaction(
        self,
        *,
        user_message: str,
        distress_input: DistressInput | str,
        toi_config: dict[str, Any] | TOIConfig | None = None,
        response_latency_seconds: float | None = None,
        recent_user_messages: list[str] | None = None,
        consent_granted: bool = False,
    ) -> StageResponse:
        toi = self.toi_parser.parse(toi_config)
        distress = distress_input if isinstance(distress_input, DistressInput) else DistressInput(distress_input)

        if toi.safety_boundaries.require_explicit_consent and not consent_granted:
            return self.create_entry_prompt(toi)

        context = InteractionContext(
            user_message=user_message,
            distress_input=distress,
            response_latency_seconds=response_latency_seconds,
            recent_user_messages=recent_user_messages or [],
            consent_granted=consent_granted,
            stage=ActivationStage.STAGE_2_DISTRESS_SORT,
        )
        assessment = self.cde.analyze(context)
        fusion = self.fusion_engine.compose(distress, assessment, toi)
        governed_weights = self.otoi_governor.govern(fusion.weights, toi, silent_mode=fusion.silent_mode)
        active_personas = list(governed_weights)
        recommended_actions = self._limit_actions(fusion.response_focus, toi, fusion.silent_mode)
        stage = self._select_stage(assessment.risk_level)
        message = self.tone_renderer.render_support_message(
            toi=toi,
            distress_input=distress,
            active_personas=active_personas,
            recommended_actions=recommended_actions,
            silent_mode=fusion.silent_mode,
        )

        response = StageResponse(
            stage=stage,
            message=message,
            tone_profile=toi.tone,
            active_personas=active_personas,
            persona_weights=governed_weights,
            recommended_actions=recommended_actions,
            silent_mode=fusion.silent_mode,
            consent_required=False,
            metadata={
                "assessment": {
                    "risk_level": assessment.risk_level,
                    "severity_score": assessment.severity_score,
                    "confidence_score": assessment.confidence_score,
                    "semantic_hits": assessment.semantic_hits,
                    "behavioral_flags": assessment.behavioral_flags,
                    "layer_scores": {layer.name: layer.score for layer in assessment.layer_results},
                    "layer_details": {layer.name: layer.details for layer in assessment.layer_results},
                },
                "persona_summaries": {persona: PERSONA_SUMMARIES[persona] for persona in active_personas},
                "stage": self.stage_definitions.get(f"stage_{int(stage)}", {}),
                "governance": self.toi_policy.get("governance", {}),
            },
        )
        self.last_response = response
        return response

    async def assess_current_state(self, **kwargs: Any) -> StageResponse:
        return self.assess_interaction(**kwargs)

    async def start_monitoring(self) -> bool:
        self.is_monitoring = True
        return True

    async def stop_monitoring(self) -> bool:
        self.is_monitoring = False
        return True

    async def get_status_report(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "monitoring_active": self.is_monitoring,
            "last_stage": int(self.last_response.stage) if self.last_response else None,
            "last_tone": self.last_response.tone_profile.value if self.last_response else None,
            "last_personas": self.last_response.active_personas if self.last_response else [],
        }

    def _select_stage(self, risk_level: str) -> ActivationStage:
        if risk_level == "acute":
            return ActivationStage.STAGE_5_ESCALATION
        if risk_level == "crisis":
            return ActivationStage.STAGE_4_STABILIZATION
        return ActivationStage.STAGE_3_REGULATION

    def _limit_actions(self, actions: list[str], toi: TOIConfig, silent_mode: bool) -> list[str]:
        if silent_mode or toi.tone == ToneProfile.MINIMAL:
            return actions[:2]
        if toi.cognitive_scaffolding in {"high", "structured"}:
            return actions[:3]
        return actions[:2]


async def create_rrt_advocate(
    user_id: str,
    config_path: str | None = None,
    toi_config_path: str | None = None,
) -> RRTAdvocate:
    return RRTAdvocate(user_id=user_id, config_path=config_path, toi_config_path=toi_config_path)
