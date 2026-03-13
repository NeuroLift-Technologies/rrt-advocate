"""
RRT AIdvocAIte — Protective Layer of the Human-AI ElevAItion Foundation
Solidarity Framework.

NeuroLift Technologies | Solidarity Framework v2.0

This module is the primary orchestration entry point.  It wires together:

  Constitutional Layer
    TOIParser          — ingests and validates the user's Terms of Interaction
    OTOICoordinator    — enforces the interaction contract at runtime

  Protective Layer (this module)
    CrisisDetectionEngine (CDE)  — 3-layer local-first detection pipeline
    FusionEngine                 — dynamic 5-persona blending
    TieredDialogueTree           — 6-stage agency-first activation flow
    ConsentManager               — consent gating before any full deployment
    InterventionManager          — assembles and delivers blended responses

Design ethos (non-negotiable):
  - Local-first & privacy-centric: CDE never calls a remote endpoint.
  - Anti-gaslight / shame-resistant: error messages never pathologise the user.
  - No forced productivity: burnout inputs never trigger task loops.
  - Agency first: consent is required before full RRT deployment.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .crisis.detection_engine import CrisisDetectionEngine
from .crisis.models import CrisisLevel, DetectionResult
from .dialogue.consent_manager import ConsentManager
from .dialogue.tiered_tree import DialogueStage, StageResult, TieredDialogueTree
from .personas.fusion_engine import FusionEngine
from .personas.models import PersonaBlend
from .response.intervention_manager import InterventionManager, InterventionRecord
from .toi.models import InteractionContract, ToneProfile
from .toi.otoi_coordinator import OTOICoordinator
from .toi.toi_parser import TOIParser

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

@dataclass
class SessionState:
    """Tracks the runtime state of a single user session."""

    user_id: str
    contract: InteractionContract
    detection_result: DetectionResult | None = None
    persona_blend: PersonaBlend | None = None
    last_intervention: InterventionRecord | None = None
    dialogue_stage: DialogueStage = DialogueStage.AMBIENT
    activation_count: int = 0
    session_start: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

class RRTAdvocate:
    """
    The RRT AIdvocAIte — top-level orchestrator for the Protective Layer.

    Instantiate once per user session.  Use ``process_message()`` as the
    primary entry point for incoming user text.  Use ``activate()`` to
    manually trigger the tiered dialogue when a non-text event (e.g. a UI
    tap or inactivity timeout) warrants intervention.
    """

    def __init__(
        self,
        user_id: str,
        toi_config_path: str | Path | None = None,
        crisis_config_path: str | Path = "config/crisis_thresholds.yaml",
    ) -> None:
        self._user_id = user_id
        self._toi_parser = TOIParser()
        self._otoi = OTOICoordinator()
        self._cde = CrisisDetectionEngine()
        self._fusion = FusionEngine()
        self._dialogue = TieredDialogueTree(fusion_engine=self._fusion)
        self._consent = ConsentManager()
        self._intervention_mgr = InterventionManager(otoi_coordinator=self._otoi)
        self._crisis_config = self._load_crisis_config(crisis_config_path)

        toi_raw = self._toi_parser.from_yaml(toi_config_path) if toi_config_path else self._toi_parser._default_config(user_id)
        import uuid
        self._contract = InteractionContract(
            toi=toi_raw,
            session_id=str(uuid.uuid4()),
        )
        self._session = SessionState(user_id=user_id, contract=self._contract)
        self._is_monitoring = False

        logger.info("RRT AIdvocAIte initialised | user=%s | tone=%s", user_id, toi_raw.tone_profile.value)

    # ------------------------------------------------------------------
    # Primary API
    # ------------------------------------------------------------------

    def process_message(self, text: str) -> dict[str, Any]:
        """
        Process an incoming user message through the full pipeline.

        Pipeline:
          CDE analysis → consent check → dialogue routing → response assembly

        Returns a response dict suitable for serialisation to JSON.
        """
        detection = self._cde.analyse(text)
        self._session.detection_result = detection

        logger.info(
            "CDE | level=%s | score=%.3f | distress=%s",
            detection.crisis_level.value,
            detection.composite_score,
            detection.dominant_distress_type,
        )

        if detection.crisis_level == CrisisLevel.GREEN:
            return self._build_response(
                message="I'm here in the background, listening.",
                stage=DialogueStage.AMBIENT,
                detection=detection,
            )

        if not self._consent.consented:
            stage_result = self._dialogue.trigger_entry(self._contract.toi)
            return self._stage_result_to_response(stage_result, detection)

        blend = self._fusion.compute(
            distress_input=detection.dominant_distress_type,
            raw_text=text,
            toi_config=self._contract.toi,
        )
        self._session.persona_blend = blend

        directive = self._otoi.produce_directive(
            contract=self._contract,
            persona_weights=blend.weights,
            distress_type=blend.distress_type,
        )

        silent = directive.silence_requested or self._contract.silent_mode_active
        record = self._intervention_mgr.assemble(blend, self._contract, silent_mode=silent)
        self._session.last_intervention = record
        self._session.activation_count += 1

        return self._build_response(
            message=record.response_text,
            stage=DialogueStage.PERSONA_RESPONSE,
            detection=detection,
            blend=blend,
            silent_mode=silent,
            system_prompt=self._intervention_mgr.get_system_prompt(blend, self._contract),
        )

    def handle_dialogue_input(self, stage: DialogueStage, user_input: str) -> dict[str, Any]:
        """
        Handle a structured dialogue input (e.g. a button tap from the UI).

        Parameters
        ----------
        stage:
            The current stage expecting a response.
        user_input:
            The user's selection or text input.
        """
        if stage == DialogueStage.CONSENT_CHECKPOINT:
            consent_state = self._consent.evaluate(user_input)
            self._contract.consent_granted = consent_state.consented
            self._contract.silent_mode_active = consent_state.silent_mode_requested

            stage_result = self._dialogue.handle_consent(user_input, self._contract.toi)
            return self._stage_result_to_response(stage_result)

        if stage == DialogueStage.DISTRESS_ASSESSMENT:
            stage_result = self._dialogue.handle_distress_assessment(
                selection_id=user_input,
                toi_config=self._contract.toi,
            )
            if stage_result.persona_blend:
                blend = stage_result.persona_blend
                self._session.persona_blend = blend
                record = self._intervention_mgr.assemble(
                    blend, self._contract, silent_mode=stage_result.silent_mode
                )
                self._session.last_intervention = record
                stage_result.message = record.response_text
            return self._stage_result_to_response(stage_result)

        if stage == DialogueStage.CHECKIN:
            helpful = user_input.lower() in ("yes", "y", "helped", "better")
            stage_result = self._dialogue.handle_checkin(helpful)
            return self._stage_result_to_response(stage_result)

        if stage == DialogueStage.CLOSURE:
            stage_result = self._dialogue.close_session()
            self._consent.reset()
            self._contract.consent_granted = False
            return self._stage_result_to_response(stage_result)

        return self._build_response(
            message="I'm not sure what you need right now — take your time.",
            stage=stage,
        )

    def activate(self) -> dict[str, Any]:
        """
        Manually trigger Stage 1 consent checkpoint (e.g. from a UI button
        or inactivity timeout).
        """
        stage_result = self._dialogue.trigger_entry(self._contract.toi)
        return self._stage_result_to_response(stage_result)

    def get_status(self) -> dict[str, Any]:
        """Return a serialisable status snapshot of the current session."""
        return {
            "user_id": self._user_id,
            "session_id": self._contract.session_id,
            "dialogue_stage": self._dialogue.current_stage.name,
            "consent_granted": self._contract.consent_granted,
            "silent_mode": self._contract.silent_mode_active,
            "tone_profile": self._contract.toi.tone_profile.value,
            "activations_this_session": self._session.activation_count,
            "session_start": self._session.session_start.isoformat(),
            "last_detection": {
                "level": self._session.detection_result.crisis_level.value
                if self._session.detection_result
                else "none",
                "score": self._session.detection_result.composite_score
                if self._session.detection_result
                else 0.0,
                "distress_type": self._session.detection_result.dominant_distress_type
                if self._session.detection_result
                else "none",
            },
            "last_blend": {
                "lead": self._session.persona_blend.lead_persona.name
                if self._session.persona_blend
                else "none",
                "distress_type": self._session.persona_blend.distress_type
                if self._session.persona_blend
                else "none",
            },
        }

    def reset_session(self) -> None:
        """Reset all session state for a fresh interaction cycle."""
        self._cde.reset_session()
        self._consent.reset()
        self._dialogue.reset()
        self._contract.consent_granted = False
        self._contract.silent_mode_active = False
        self._session = SessionState(
            user_id=self._user_id,
            contract=self._contract,
        )
        logger.info("Session reset | user=%s", self._user_id)

    # ------------------------------------------------------------------
    # Async monitoring interface (backward-compat surface)
    # ------------------------------------------------------------------

    async def start_monitoring(self) -> bool:
        """Start async background monitoring loop."""
        if self._is_monitoring:
            return True
        self._is_monitoring = True
        asyncio.create_task(self._monitoring_loop())
        logger.info("Monitoring started | user=%s", self._user_id)
        return True

    async def stop_monitoring(self) -> bool:
        """Stop async monitoring loop."""
        self._is_monitoring = False
        logger.info("Monitoring stopped | user=%s", self._user_id)
        return True

    async def _monitoring_loop(self) -> None:
        """Lightweight async loop — processes queued messages if any."""
        while self._is_monitoring:
            await asyncio.sleep(1)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _stage_result_to_response(
        self,
        stage_result: StageResult,
        detection: DetectionResult | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "stage": stage_result.stage.name,
            "next_stage": stage_result.next_stage.name,
            "message": stage_result.message,
            "options": stage_result.options,
            "silent_mode": stage_result.silent_mode,
            "escalation_signal": stage_result.escalation_signal,
            "metadata": stage_result.metadata,
        }
        if stage_result.persona_blend:
            payload["blend"] = {
                "lead": stage_result.persona_blend.lead_persona.name,
                "distress_type": stage_result.persona_blend.distress_type,
                "rationale": stage_result.persona_blend.rationale,
                "weights": stage_result.persona_blend.weights.as_dict(),
            }
        if detection:
            payload["detection"] = {
                "level": detection.crisis_level.value,
                "score": detection.composite_score,
                "distress_type": detection.dominant_distress_type,
            }
        return payload

    def _build_response(
        self,
        message: str,
        stage: DialogueStage,
        detection: DetectionResult | None = None,
        blend: PersonaBlend | None = None,
        silent_mode: bool = False,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "stage": stage.name,
            "message": message,
            "silent_mode": silent_mode,
        }
        if system_prompt:
            payload["system_prompt"] = system_prompt
        if blend:
            payload["blend"] = {
                "lead": blend.lead_persona.name,
                "distress_type": blend.distress_type,
                "rationale": blend.rationale,
                "weights": blend.weights.as_dict(),
            }
        if detection:
            payload["detection"] = {
                "level": detection.crisis_level.value,
                "score": detection.composite_score,
                "distress_type": detection.dominant_distress_type,
                "escalation_required": detection.escalation_required,
            }
        return payload

    @staticmethod
    def _load_crisis_config(path: str | Path) -> dict:
        p = Path(path)
        if p.exists():
            with p.open("r", encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        return {}


# ---------------------------------------------------------------------------
# Package-level factory
# ---------------------------------------------------------------------------

def create_rrt_advocate(
    user_id: str,
    toi_config_path: str | Path | None = None,
    crisis_config_path: str | Path = "config/crisis_thresholds.yaml",
) -> "RRTAdvocate":
    """
    Create a fully initialised RRT AIdvocAIte.

    Parameters
    ----------
    user_id:
        Unique identifier for the user.
    toi_config_path:
        Path to the user's TOI YAML file.  If None, sensible defaults apply.
    crisis_config_path:
        Path to the crisis thresholds config.
    """
    return RRTAdvocate(
        user_id=user_id,
        toi_config_path=toi_config_path,
        crisis_config_path=crisis_config_path,
    )


# ---------------------------------------------------------------------------
# CLI demo harness
# ---------------------------------------------------------------------------

def _demo() -> None:
    """Quick smoke-test / demo of the full pipeline."""
    print("\n" + "=" * 60)
    print("  RRT AIdvocAIte — Solidarity Framework Demo")
    print("=" * 60)

    advocate = create_rrt_advocate("demo_user")

    test_messages = [
        ("Feeling a bit distracted today.", "GREEN — ambient check"),
        ("I can't stop blaming myself for everything.  It's my fault.", "YELLOW+ — ECHO/ASH blend"),
        ("I'm so overwhelmed, everything hurts, I can't do anything right.", "ORANGE+ — ASH/MYRA blend"),
    ]

    for text, label in test_messages:
        print(f"\n--- {label} ---")
        print(f"Input: {text!r}")
        result = advocate.process_message(text)
        print(f"Stage : {result['stage']}")
        if "detection" in result:
            d = result["detection"]
            print(f"CDE   : level={d['level']}  score={d['score']:.3f}  distress={d['distress_type']}")
        if "blend" in result:
            b = result["blend"]
            print(f"Blend : lead={b['lead']}  distress={b['distress_type']}")
            for name, w in sorted(b["weights"].items(), key=lambda kv: -kv[1]):
                bar = "█" * int(w * 20)
                print(f"        {name:<5} {bar:<20} {w:.3f}")
        if result.get("message"):
            print(f"Response: {result['message']}")

    print("\n--- Consent + Stage 2 walkthrough ---")
    advocate.reset_session()
    # Manually trigger entry
    entry = advocate.activate()
    print(f"Stage 1 prompt: {entry['message']}")
    print("Options:", [o["label"] for o in entry.get("options", [])])

    consent_resp = advocate.handle_dialogue_input(
        DialogueStage.CONSENT_CHECKPOINT, "yes"
    )
    print(f"\nStage 2 prompt: {consent_resp['message']}")
    print("Options:", [o["label"] for o in consent_resp.get("options", [])])

    assessment_resp = advocate.handle_dialogue_input(
        DialogueStage.DISTRESS_ASSESSMENT, "meltdown"
    )
    print(f"\nPersona response: {assessment_resp.get('message', '[silent]')}")
    if "blend" in assessment_resp:
        b = assessment_resp["blend"]
        print(f"Lead persona: {b['lead']} ({b['distress_type']})")
        print(f"Rationale: {b['rationale']}")

    print("\n" + "=" * 60)
    print("Status snapshot:")
    print(json.dumps(advocate.get_status(), indent=2))
    print("=" * 60 + "\n")


if __name__ == "__main__":
    _demo()
