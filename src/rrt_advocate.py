"""
RRT Advocate - TOI/OTOI compliant protective-layer orchestrator.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Iterable, Optional

from .cde import LocalFirstCrisisDetectionEngine
from .dialogue_tree import TieredActivationDialogueTree
from .models import DistressSignal, OTOIPolicy, RRTResponse, TOIConfig, ToneProfile
from .personas import PERSONA_DEFINITIONS, PersonaFusionEngine
from .toi_otoi import TOIOTOIGovernanceWrapper
from .tone_profiles import ToneProfileRenderer


class RRTAdvocate:
    """
    Protective-layer RRT AIdvocAIte with:
      - TOI/OTOI governance middleware
      - Dynamic persona fusion for Ash/Sol/Echo/Kai/Myra
      - Local-first 3-layer CDE
      - Stage-based consent-first dialogue routing
    """

    def __init__(
        self,
        user_id: str,
        toi_config: TOIConfig | Dict[str, Any] | None = None,
        *,
        otoi_policy: OTOIPolicy | None = None,
    ) -> None:
        self.user_id = user_id
        self.toi_config = _coerce_toi_config(toi_config)
        self.otoi_policy = otoi_policy or OTOIPolicy()
        self.consent_granted = False

        self.dialogue_tree = TieredActivationDialogueTree()
        self.fusion_engine = PersonaFusionEngine()
        self.cde = LocalFirstCrisisDetectionEngine()
        self.tone_renderer = ToneProfileRenderer()
        self.governance = TOIOTOIGovernanceWrapper(self.toi_config, self.otoi_policy)

    def stage_1_entry_prompt(self) -> str:
        return self.dialogue_tree.stage_1_entry_prompt()

    def stage_2_distress_options(self) -> Dict[str, str]:
        return {
            "everything_hurts_meltdown": "Everything hurts / Meltdown",
            "cant_do_basic_tasks": "Can't do basic tasks",
            "cant_stop_self_blame": "Can't stop self-blame",
            "stuck_in_hyperfocus_loop": "Stuck in hyperfocus/loop",
            "dont_know_shutdown": "Don't know / Shut down",
        }

    def process_interaction(
        self,
        *,
        user_message: str,
        stage: int = 1,
        consent: Optional[bool] = None,
        stage_2_input: Optional[str] = None,
        response_latency_seconds: Optional[float] = None,
        recent_messages: Optional[Iterable[str]] = None,
    ) -> RRTResponse:
        """
        Entry point for each local interaction cycle.
        """
        cleaned_message = self.governance.sanitize_user_text(user_message)
        if consent is not None:
            self.consent_granted = consent

        cde_assessment = self.cde.assess(
            message=cleaned_message,
            recent_messages=recent_messages,
            response_latency_seconds=response_latency_seconds,
        )

        directive = self.dialogue_tree.route(
            stage=stage,
            consent_granted=self.consent_granted,
            stage_2_input=stage_2_input,
        )

        if directive.needs_consent and self.governance.requires_stage_1_consent():
            neutral_fusion = self.fusion_engine.fuse(
                DistressSignal.UNSPECIFIED,
                cde_assessment.distress_tags,
            )
            entry_prompt = self.governance.enforce_safety_boundaries(
                directive.prompt or self.stage_1_entry_prompt()
            )
            return RRTResponse(
                stage=directive.stage,
                consent_required=True,
                consent_granted=False,
                distress_signal=DistressSignal.UNSPECIFIED,
                fusion=neutral_fusion,
                cde=cde_assessment,
                tone_profile=self.toi_config.tone_profile,
                prompt_package=entry_prompt,
                metadata={
                    "agency_first": True,
                    "next_stage": 2,
                    "local_first_cde": True,
                },
            )

        distress_signal = directive.distress_signal
        if distress_signal == DistressSignal.UNSPECIFIED:
            distress_signal = _infer_distress_from_cde(cde_assessment.distress_tags, cde_assessment.overall_risk_score)

        fusion = self.fusion_engine.fuse(distress_signal, cde_assessment.distress_tags)
        fusion.persona_weights = self.governance.enforce_persona_contract(fusion.persona_weights)

        guidance = self._build_response_guidance(distress_signal, fusion.silent_mode, cde_assessment.overall_risk_score)
        persona_summary = self.fusion_engine.summarize_weights(fusion.persona_weights)
        prompt_package = self.tone_renderer.render(
            tone_profile=self.toi_config.tone_profile,
            pacing=self.toi_config.pacing,
            cognitive_scaffolding=self.toi_config.cognitive_scaffolding,
            silent_mode=fusion.silent_mode,
            persona_summary=persona_summary,
            response_guidance=guidance,
        )
        prompt_package = self.governance.enforce_safety_boundaries(prompt_package)

        return RRTResponse(
            stage=max(2, stage),
            consent_required=False,
            consent_granted=self.consent_granted,
            distress_signal=distress_signal,
            fusion=fusion,
            cde=cde_assessment,
            tone_profile=self.toi_config.tone_profile,
            prompt_package=prompt_package,
            metadata={
                "agency_first": True,
                "local_first_cde": True,
                "persona_definitions": PERSONA_DEFINITIONS,
                "cde_layers": {
                    "layer_1": asdict(cde_assessment.layer_1_keywords),
                    "layer_2": asdict(cde_assessment.layer_2_sentiment),
                    "layer_3": asdict(cde_assessment.layer_3_behavior),
                },
            },
        )

    def _build_response_guidance(self, distress_signal: DistressSignal, silent_mode: bool, risk_score: float) -> str:
        """
        Produces behavior guidance for the LLM response generation layer.
        """
        if distress_signal in {DistressSignal.MELTDOWN, DistressSignal.SHUTDOWN}:
            return (
                "Prioritize co-regulation and emotional safety. "
                "Avoid forced productivity or multi-step task pressure. "
                "Offer one gentle anchoring suggestion and explicit permission to pause."
            )
        if distress_signal == DistressSignal.TASKS_IMPOSSIBLE:
            return (
                "Offer one ultra-small action with optional alternatives. "
                "Keep sequence clear and low-friction; avoid urgency framing."
            )
        if distress_signal == DistressSignal.SELF_BLAME_LOOP:
            return (
                "Mirror user experience without judgment, then reframe blame language softly. "
                "Use shame-resistant language and ask one reflective question at most."
            )
        if distress_signal == DistressSignal.HYPERFOCUS_LOOP:
            return (
                "Redirect fixation toward a safe transition target. "
                "Use clear directional steps and a single check-in point."
            )

        default_guidance = "Stay validating, concise, and collaborative."
        if silent_mode:
            return default_guidance + " Keep language sparse and non-urgent."
        if risk_score > 0.75:
            return default_guidance + " Include a brief safety check invitation."
        return default_guidance


def _coerce_toi_config(raw: TOIConfig | Dict[str, Any] | None) -> TOIConfig:
    if isinstance(raw, TOIConfig):
        return raw
    if not isinstance(raw, dict):
        return TOIConfig()

    tone_raw = str(raw.get("tone_profile", ToneProfile.SUPPORTIVE_DEFAULT.value))
    try:
        tone_profile = ToneProfile(tone_raw)
    except ValueError:
        tone_profile = ToneProfile.SUPPORTIVE_DEFAULT

    return TOIConfig(
        tone_profile=tone_profile,
        pacing=str(raw.get("pacing", "gentle")),
        cognitive_scaffolding=str(raw.get("cognitive_scaffolding", "moderate")),
        safety_boundaries=dict(raw.get("safety_boundaries", {})),
    )


def _infer_distress_from_cde(tags: Iterable[str], risk_score: float) -> DistressSignal:
    tag_set = set(tags)
    if "looping_behavior" in tag_set:
        return DistressSignal.HYPERFOCUS_LOOP
    if "task_avoidance" in tag_set:
        return DistressSignal.TASKS_IMPOSSIBLE
    if "negative_self_talk" in tag_set:
        return DistressSignal.SELF_BLAME_LOOP
    if "overwhelm" in tag_set:
        return DistressSignal.MELTDOWN if risk_score > 0.65 else DistressSignal.SHUTDOWN
    return DistressSignal.UNSPECIFIED


async def create_rrt_advocate(
    user_id: str,
    toi_config: TOIConfig | Dict[str, Any] | None = None,
    *,
    otoi_policy: OTOIPolicy | None = None,
) -> RRTAdvocate:
    """
    Async-compatible factory retained for integration compatibility.
    """
    return RRTAdvocate(user_id=user_id, toi_config=toi_config, otoi_policy=otoi_policy)
