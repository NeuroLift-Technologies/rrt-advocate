"""RRT Advocate Protective Layer implementation for TOI-compliant intervention."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from crisis_detection_engine import CDEAssessment, CrisisDetectionEngine
from dialogue_tree import ActivationStage, DialogueState, TieredActivationDialogueTree
from persona_fusion import DistressSignal, PersonaBlend, PersonaFusionEngine
from toi_otoi import OTOICoordinator, TOIConfig, TOIParser
from tone_profiles import ToneProfileEngine

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only if dependency is missing.
    yaml = None


PERSONA_DIRECTIVES = {
    "ash": "Validate burnout and diffuse shame. Prioritize being over doing.",
    "sol": "Scaffold executive function with low-friction micro-steps.",
    "echo": "Mirror internal monologue and gently reframe distortions.",
    "kai": "Redirect fixation/hyperfocus into constructive pathways.",
    "myra": "Provide relational safety, co-regulation, and quiet anchoring.",
}


@dataclass(frozen=True)
class ResponsePacket:
    stage: int
    message: str
    toi_applied: bool
    tone_profile: str
    selected_personas: List[str]
    persona_weights: Dict[str, float]
    cde_overall_risk: float
    cde_flags: List[str]
    silent_mode: bool
    ui_hints: Dict[str, Any]
    next_action: str


class RRTAdvocate:
    """TOI-governed, agency-first RRT orchestration engine."""

    def __init__(self, user_id: str, config_path: str = "config/crisis_thresholds.yaml"):
        self.user_id = user_id
        self.config_path = config_path
        self.config = self._load_config(config_path)

        self.toi_parser = TOIParser()
        self.otoi = OTOICoordinator()
        self.fusion = PersonaFusionEngine(self.config)
        self.tone_engine = ToneProfileEngine(self.config)
        self.cde = CrisisDetectionEngine(self.config)
        self.dialogue_tree = TieredActivationDialogueTree()

        self.toi_config: Optional[TOIConfig] = None
        self.state = DialogueState()
        self.message_history: List[str] = []
        self.latest_assessment: Optional[CDEAssessment] = None

    def ingest_toi(self, toi_payload: Dict[str, Any]) -> Dict[str, Any]:
        self.toi_config = self.toi_parser.parse(toi_payload)
        return asdict(self.toi_config)

    def stage1_entry_prompt(self) -> Dict[str, Any]:
        self.state.stage = ActivationStage.STAGE_1_CONSENT
        return {
            "stage": ActivationStage.STAGE_1_CONSENT.value,
            "message": self.dialogue_tree.stage_1_entry_prompt(),
            "next_action": "confirm_consent",
        }

    def handle_stage1_consent(self, consent_granted: bool) -> Dict[str, Any]:
        if not self.toi_config:
            return {
                "stage": ActivationStage.STAGE_1_CONSENT.value,
                "message": (
                    "Before support starts, please share your TOI settings "
                    "(tone, pacing, scaffolding, and boundaries)."
                ),
                "next_action": "provide_toi",
            }

        self.state.consent_granted = bool(consent_granted)
        if not self.state.consent_granted:
            self.state.stage = ActivationStage.STAGE_0_IDLE
            return {
                "stage": ActivationStage.STAGE_0_IDLE.value,
                "message": (
                    "No problem. RRT is paused. "
                    "If you want support later, say 'start RRT'."
                ),
                "next_action": "wait",
            }

        self.state.stage = ActivationStage.STAGE_2_DISTRESS
        stage2 = self.dialogue_tree.stage_2_prompt()
        return {
            "stage": ActivationStage.STAGE_2_DISTRESS.value,
            "message": stage2["prompt"],
            "options": stage2["options"],
            "note": stage2["note"],
            "next_action": "select_distress",
        }

    def handle_stage2_distress(
        self,
        distress_input: str,
        user_message: Optional[str] = None,
        response_latency_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        if not self.toi_config:
            return {
                "stage": ActivationStage.STAGE_1_CONSENT.value,
                "message": "TOI is required before interventions can run.",
                "next_action": "provide_toi",
            }
        if not self.state.consent_granted:
            return self.stage1_entry_prompt()

        text = (user_message or distress_input or "").strip()
        if text:
            self.message_history.append(text)

        signal = self.dialogue_tree.resolve_distress_signal(distress_input)
        self.state.distress_signal = signal
        self.state.stage = ActivationStage.STAGE_3_SUPPORT

        assessment = self.cde.analyze(
            message_history=self.message_history,
            response_latency_seconds=response_latency_seconds,
        )
        self.latest_assessment = assessment

        blend = self.fusion.compute_blend(
            distress_signal=signal,
            cde_risk=assessment.overall_risk,
            layer1_matches=assessment.layer1.details,
        )
        selected_personas = self.otoi.choose_personas(blend.weights, self.toi_config)

        draft_lines = self._build_draft_lines(signal, selected_personas, blend.silent_mode)
        message = self.tone_engine.format_response(
            tone_name=self.toi_config.tone_profile,
            personas=selected_personas,
            draft_lines=draft_lines,
            silent_mode=blend.silent_mode,
        )

        if assessment.overall_risk >= 0.8:
            self.state.stage = ActivationStage.STAGE_4_SAFETY_CONFIRM
            next_action = "confirm_safety_escalation"
        else:
            next_action = "continue_support"

        packet = ResponsePacket(
            stage=self.state.stage.value,
            message=message,
            toi_applied=True,
            tone_profile=self.toi_config.tone_profile,
            selected_personas=selected_personas,
            persona_weights=blend.weights,
            cde_overall_risk=assessment.overall_risk,
            cde_flags=assessment.flags,
            silent_mode=blend.silent_mode,
            ui_hints=self._ui_hints(blend),
            next_action=next_action,
        )

        response = asdict(packet)
        response["llm_prompt"] = self.build_llm_prompt(signal, blend, selected_personas)
        return response

    def handle_stage4_safety_check(self, allow_escalation: bool) -> Dict[str, Any]:
        if self.state.stage != ActivationStage.STAGE_4_SAFETY_CONFIRM:
            return {
                "stage": self.state.stage.value,
                "message": "Safety check is only available after high-risk detection.",
                "next_action": "continue_support",
            }

        if not allow_escalation:
            self.state.stage = ActivationStage.STAGE_3_SUPPORT
            return {
                "stage": ActivationStage.STAGE_3_SUPPORT.value,
                "message": "Okay. No escalation initiated. We continue at your pace.",
                "next_action": "continue_support",
            }

        self.state.stage = ActivationStage.STAGE_5_ESCALATION
        return {
            "stage": ActivationStage.STAGE_5_ESCALATION.value,
            "message": "Escalation enabled. I can share crisis resources now (988 / text HOME to 741741).",
            "next_action": "resource_handoff",
        }

    def process_interaction(
        self,
        user_message: str,
        toi_payload: Optional[Dict[str, Any]] = None,
        consent_granted: Optional[bool] = None,
        distress_input: Optional[str] = None,
        response_latency_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Entry point for all interactions.

        Every interaction path enforces TOI parsing before response generation.
        """
        if toi_payload is not None:
            self.ingest_toi(toi_payload)

        if not self.toi_config:
            return {
                "stage": ActivationStage.STAGE_1_CONSENT.value,
                "message": (
                    "Please provide TOI settings first: tone_profile, pacing, "
                    "cognitive_scaffolding, and safety_boundaries."
                ),
                "next_action": "provide_toi",
            }

        if consent_granted is None and not self.state.consent_granted:
            return self.stage1_entry_prompt()

        if consent_granted is not None and not self.state.consent_granted:
            return self.handle_stage1_consent(consent_granted)

        chosen_distress = distress_input or user_message
        return self.handle_stage2_distress(
            distress_input=chosen_distress,
            user_message=user_message,
            response_latency_seconds=response_latency_seconds,
        )

    def build_llm_prompt(
        self,
        signal: DistressSignal,
        blend: PersonaBlend,
        selected_personas: List[str],
    ) -> Dict[str, Any]:
        """Structured prompt payload for downstream model invocation."""
        tone_name = self.toi_config.tone_profile if self.toi_config else "supportive_default"
        tone_profile = self.tone_engine.get_profile(tone_name)
        persona_directives = {
            name: PERSONA_DIRECTIVES[name] for name in selected_personas if name in PERSONA_DIRECTIVES
        }
        return {
            "tone_profile": tone_name,
            "tone_directive": tone_profile.prompt_directive,
            "distress_signal": signal.value,
            "persona_weights": blend.weights,
            "persona_directives": persona_directives,
            "silent_mode": blend.silent_mode,
            "toi_constraints": asdict(self.toi_config) if self.toi_config else {},
            "instruction": "Respond within TOI boundaries. Preserve user agency. Avoid shaming language.",
        }

    def _build_draft_lines(
        self,
        signal: DistressSignal,
        selected_personas: List[str],
        silent_mode: bool,
    ) -> List[str]:
        lines: List[str] = []
        persona_text = ", ".join(selected_personas) if selected_personas else "RRT"

        if signal == DistressSignal.BASIC_TASKS:
            lines.append("We can make this tiny: one smallest next step, then pause.")
        elif signal == DistressSignal.SELF_BLAME:
            lines.append("You are not a failure; your system is under strain right now.")
        elif signal == DistressSignal.HYPERFOCUS_LOOP:
            lines.append("Let's redirect that loop into one bounded, constructive action.")
        elif signal == DistressSignal.MELTDOWN:
            lines.append("You are not doing this wrong. We can slow everything down safely.")
        else:
            lines.append("No pressure to explain. We can stay quiet and regulated first.")

        if silent_mode:
            lines.append("Silent Mode active: calm visuals on, timers off, low-demand prompts only.")

        lines.append(f"Active guides: {persona_text}.")
        return lines

    @staticmethod
    def _ui_hints(blend: PersonaBlend) -> Dict[str, Any]:
        return {
            "calm_visuals": blend.silent_mode,
            "show_timers": not blend.silent_mode,
            "low_demand_mode": blend.silent_mode,
        }

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        resolved = Path(config_path)
        if not resolved.is_absolute():
            resolved = Path(__file__).resolve().parents[1] / config_path

        if not resolved.exists():
            return {}
        if yaml is None:
            raise RuntimeError("PyYAML is required to read the RRT configuration.")
        with resolved.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}


def create_rrt_advocate(user_id: str, config_path: str = "config/crisis_thresholds.yaml") -> RRTAdvocate:
    return RRTAdvocate(user_id=user_id, config_path=config_path)
