"""Solidarity Framework protective-layer implementation for the RRT advocate."""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from protective_layer.engines import (
    DEFAULT_RRT_CONFIG_PATH,
    DEFAULT_TOI_CONFIG_PATH,
    LocalFirstCrisisDetectionEngine,
    PersonaFusionEngine,
    TOIParser,
    TieredActivationDialogueTree,
    load_yaml_config,
)
from protective_layer.models import (
    CrisisAssessment,
    CrisisLevel,
    DistressSignal,
    InterventionResponse,
    PersonaBlend,
    ResponsePlan,
    ResponseStatus,
    TOIConfig,
)


class RRTAdvocate:
    """Protective-layer advocate for TOI-governed, low-demand crisis support."""

    def __init__(
        self,
        user_id: str,
        config_path: Union[str, Path] = DEFAULT_RRT_CONFIG_PATH,
        toi_config_path: Union[str, Path] = DEFAULT_TOI_CONFIG_PATH,
        supervisor_interface: Optional[Any] = None,
    ):
        self.user_id = user_id
        self.config_path = Path(config_path)
        self.toi_config_path = Path(toi_config_path)
        self.supervisor = supervisor_interface

        self.config = load_yaml_config(self.config_path)
        self.toi_parser = TOIParser(self.toi_config_path)
        self.default_toi = self.toi_parser.load()
        self.detector = LocalFirstCrisisDetectionEngine(self.config)
        self.fusion_engine = PersonaFusionEngine(self.config)
        self.dialogue_tree = TieredActivationDialogueTree(self.config)

        self.is_monitoring = False
        self.current_crisis: Optional[CrisisAssessment] = None
        self.current_plan: Optional[ResponsePlan] = None
        self.crisis_history: List[CrisisAssessment] = []
        self.active_interventions: List[InterventionResponse] = []
        self.response_times: List[float] = []
        self.intervention_success_rate: float = 0.0
        self.last_assessment_time: Optional[datetime] = None

        self.logger = logging.getLogger(f"RRTAdvocate-{self.user_id}")
        self._setup_logging()
        self.logger.info("RRT Advocate initialized with local-first protective layer.")

    def _setup_logging(self) -> None:
        if self.logger.handlers:
            return
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _resolve_toi(self, toi_config: Optional[Union[Dict[str, Any], str, Path]]) -> TOIConfig:
        return self.toi_parser.load(toi_config) if toi_config is not None else self.default_toi

    def _build_assessment(
        self,
        blend: PersonaBlend,
        distress_signal: Optional[DistressSignal],
        detection_score: float,
        primary_indicators: List[str],
        secondary_indicators: List[str],
        crisis_level: CrisisLevel,
        safety_keywords: List[str],
    ) -> CrisisAssessment:
        estimated_minutes = max(2, int(round(detection_score * 20)))
        recommended_interventions = [
            f"{persona}_support"
            for persona in blend.dominant_personas[:2]
        ]
        if blend.silent_mode:
            recommended_interventions.append("silent_mode")
        if safety_keywords:
            recommended_interventions.append("consent_based_external_support_check")

        user_safety_score = 0.12 if safety_keywords else round(max(0.0, 1.0 - detection_score), 4)
        return CrisisAssessment(
            timestamp=datetime.now(),
            crisis_level=crisis_level,
            primary_indicators=primary_indicators,
            secondary_indicators=secondary_indicators,
            confidence_score=round(detection_score, 4),
            estimated_duration=timedelta(minutes=estimated_minutes),
            recommended_interventions=recommended_interventions,
            escalation_threshold=0.88,
            user_safety_score=user_safety_score,
            dominant_distress=distress_signal,
            persona_weights=blend.weights,
            recommended_tone=blend.tone_profile,
            silent_mode=blend.silent_mode,
            context_factors={
                "dominant_personas": blend.dominant_personas,
                "rationale": blend.rationale,
            },
        )

    async def _notify_supervisor(self, method_name: str, **payload: Any) -> None:
        if not self.supervisor or not hasattr(self.supervisor, method_name):
            return
        result = getattr(self.supervisor, method_name)(**payload)
        if inspect.isawaitable(result):
            await result

    async def start_monitoring(self) -> bool:
        if self.is_monitoring:
            return True
        self.is_monitoring = True
        await self._notify_supervisor(
            "notify_advocate_status",
            advocate_id="rrt",
            status="monitoring_active",
            user_id=self.user_id,
        )
        return True

    async def stop_monitoring(self) -> bool:
        if not self.is_monitoring:
            return True
        self.is_monitoring = False
        await self._notify_supervisor(
            "notify_advocate_status",
            advocate_id="rrt",
            status="monitoring_stopped",
            user_id=self.user_id,
        )
        return True

    async def assess_current_state(
        self,
        message: str = "",
        history: Optional[Sequence[str]] = None,
        response_latency_seconds: Optional[float] = None,
        distress_signal: Optional[str] = None,
        toi_config: Optional[Union[Dict[str, Any], str, Path]] = None,
    ) -> CrisisAssessment:
        start_time = datetime.now()
        toi = self._resolve_toi(toi_config)
        detection = self.detector.analyze(
            message=message,
            history=history,
            response_latency_seconds=response_latency_seconds,
        )
        selected_signal = DistressSignal.from_input(distress_signal) or detection.dominant_distress
        blend = self.fusion_engine.build_blend(selected_signal, detection, toi)
        assessment = self._build_assessment(
            blend=blend,
            distress_signal=selected_signal,
            detection_score=detection.overall_score,
            primary_indicators=detection.primary_indicators,
            secondary_indicators=detection.secondary_indicators,
            crisis_level=detection.crisis_level,
            safety_keywords=detection.safety_keywords,
        )

        self.current_crisis = assessment
        self.crisis_history.append(assessment)
        response_time = (datetime.now() - start_time).total_seconds()
        self.response_times.append(response_time)
        self.last_assessment_time = datetime.now()
        self.logger.info(
            "Assessment complete: level=%s distress=%s response_time=%.3fs",
            assessment.crisis_level.value,
            assessment.dominant_distress.value if assessment.dominant_distress else "undetermined",
            response_time,
        )
        return assessment

    async def plan_support(
        self,
        message: str,
        consent_granted: bool = False,
        distress_signal: Optional[str] = None,
        toi_config: Optional[Union[Dict[str, Any], str, Path]] = None,
        history: Optional[Sequence[str]] = None,
        response_latency_seconds: Optional[float] = None,
    ) -> ResponsePlan:
        toi = self._resolve_toi(toi_config)
        detection = self.detector.analyze(
            message=message,
            history=history,
            response_latency_seconds=response_latency_seconds,
        )
        selected_signal = DistressSignal.from_input(distress_signal) or detection.dominant_distress
        blend = None
        if consent_granted and selected_signal is not None:
            blend = self.fusion_engine.build_blend(selected_signal, detection, toi)
        plan = self.dialogue_tree.build_plan(
            toi=toi,
            detection=detection,
            blend=blend,
            consent_granted=consent_granted,
            distress_signal=selected_signal,
        )
        self.current_plan = plan
        self.logger.info(
            "Plan created: stage=%s consent=%s local_only=%s",
            int(plan.stage),
            consent_granted,
            plan.detection.local_only,
        )
        return plan

    async def respond(
        self,
        message: str,
        consent_granted: bool = False,
        distress_signal: Optional[str] = None,
        toi_config: Optional[Union[Dict[str, Any], str, Path]] = None,
        history: Optional[Sequence[str]] = None,
        response_latency_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        plan = await self.plan_support(
            message=message,
            consent_granted=consent_granted,
            distress_signal=distress_signal,
            toi_config=toi_config,
            history=history,
            response_latency_seconds=response_latency_seconds,
        )
        return plan.to_dict()

    async def manual_intervention(
        self,
        intervention_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        payload = context or {}
        plan = await self.plan_support(
            message=payload.get("message", intervention_type),
            consent_granted=True,
            distress_signal=intervention_type,
            toi_config=payload.get("toi_config"),
            history=payload.get("history"),
            response_latency_seconds=payload.get("response_latency_seconds"),
        )
        intervention = InterventionResponse(
            intervention_id=f"manual-{len(self.active_interventions) + 1}",
            start_time=datetime.now(),
            end_time=datetime.now(),
            status=ResponseStatus.SUCCESSFUL
            if int(plan.stage) in (3, 5)
            else ResponseStatus.PENDING,
            effectiveness_score=0.85 if int(plan.stage) in (3, 5) else None,
            user_feedback=None,
            follow_up_required=int(plan.stage) == 5,
        )
        self.active_interventions.append(intervention)
        self._update_success_rate()
        return int(plan.stage) in (3, 5)

    def _update_success_rate(self) -> None:
        completed = [
            intervention
            for intervention in self.active_interventions
            if intervention.effectiveness_score is not None
        ]
        if not completed:
            self.intervention_success_rate = 0.0
            return
        successful = sum(1 for intervention in completed if intervention.effectiveness_score >= 0.7)
        self.intervention_success_rate = round(successful / len(completed), 4)

    async def get_status_report(self) -> Dict[str, Any]:
        average_response_time = (
            sum(self.response_times[-100:]) / len(self.response_times[-100:])
            if self.response_times
            else 0.0
        )
        return {
            "user_id": self.user_id,
            "monitoring_active": self.is_monitoring,
            "current_crisis": self.current_crisis.to_dict() if self.current_crisis else None,
            "current_plan_stage": int(self.current_plan.stage) if self.current_plan else None,
            "active_interventions": len(self.active_interventions),
            "crisis_history_count": len(self.crisis_history),
            "performance": {
                "avg_response_time": round(average_response_time, 4),
                "success_rate": self.intervention_success_rate,
                "last_assessment": self.last_assessment_time.isoformat() if self.last_assessment_time else None,
            },
            "local_processing_only": self.config.get("protective_layer", {}).get("local_processing_only", True),
        }

    async def shutdown(self) -> None:
        await self.stop_monitoring()
        self.logger.info("RRT Advocate shutdown complete.")


async def create_rrt_advocate(
    user_id: str,
    config_path: Union[str, Path] = DEFAULT_RRT_CONFIG_PATH,
    toi_config_path: Union[str, Path] = DEFAULT_TOI_CONFIG_PATH,
    supervisor_interface: Optional[Any] = None,
) -> RRTAdvocate:
    """Factory helper that initializes the advocate with the new protective layer."""
    return RRTAdvocate(
        user_id=user_id,
        config_path=config_path,
        toi_config_path=toi_config_path,
        supervisor_interface=supervisor_interface,
    )


async def main() -> None:
    """Minimal demo entrypoint for the protective-layer workflow."""
    advocate = await create_rrt_advocate("demo-user")
    sample_plan = await advocate.respond(
        message="Everything hurts and I can't think straight.",
        consent_granted=True,
        distress_signal="Everything hurts / Meltdown",
        history=["I was trying to work", "Now everything feels too much"],
        response_latency_seconds=180,
    )
    print(json.dumps(sample_plan, indent=2))
    status = await advocate.get_status_report()
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
