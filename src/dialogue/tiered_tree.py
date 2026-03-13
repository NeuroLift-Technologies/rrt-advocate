"""
Tiered Activation Dialogue Tree.

Implements a 6-stage (0–5) low-demand user journey that maps the user's
self-reported distress to the Fusion Engine's persona weights.

Stage overview:
  Stage 0 — Ambient monitoring (no active dialogue).
  Stage 1 — Entry prompt: consent checkpoint before RRT deploys.
  Stage 2 — Distress assessment: 5 soft input options.
  Stage 3 — Persona-blended response delivered.
  Stage 4 — Check-in: is this helping?
  Stage 5 — Closure or escalation path.

Design principles:
  - Agency First: the system always pauses at Stage 1 for consent.
  - No Forced Productivity: no task loop is ever triggered from burnout inputs.
  - Silent Mode: 'shutdown' input suppresses all text; calm anchors only.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from ..personas.fusion_engine import FusionEngine
from ..personas.models import PersonaBlend

if TYPE_CHECKING:
    from ..toi.models import InteractionContract, TOIConfig

logger = logging.getLogger(__name__)


class DialogueStage(int, Enum):
    AMBIENT = 0
    CONSENT_CHECKPOINT = 1
    DISTRESS_ASSESSMENT = 2
    PERSONA_RESPONSE = 3
    CHECKIN = 4
    CLOSURE = 5


# ---------------------------------------------------------------------------
# Stage 2 distress options — the 5 canonical inputs from the brief
# ---------------------------------------------------------------------------
STAGE2_OPTIONS: list[dict] = [
    {
        "id": "meltdown",
        "label": "Everything hurts / Meltdown",
        "distress_type": "meltdown",
        "silent_mode": False,
    },
    {
        "id": "task_paralysis",
        "label": "Can't do basic tasks",
        "distress_type": "task_paralysis",
        "silent_mode": False,
    },
    {
        "id": "self_blame",
        "label": "Can't stop self-blame",
        "distress_type": "self_blame",
        "silent_mode": False,
    },
    {
        "id": "hyperfocus_loop",
        "label": "Stuck in hyperfocus / loop",
        "distress_type": "hyperfocus_loop",
        "silent_mode": False,
    },
    {
        "id": "shutdown",
        "label": "Don't know / Shut down",
        "distress_type": "shutdown",
        "silent_mode": True,
    },
]


@dataclass
class StageResult:
    """The output of processing a single dialogue stage."""

    stage: DialogueStage
    next_stage: DialogueStage
    message: str
    persona_blend: PersonaBlend | None = None
    silent_mode: bool = False
    options: list[dict] = field(default_factory=list)
    escalation_signal: bool = False
    metadata: dict = field(default_factory=dict)


class TieredDialogueTree:
    """
    Manages state transitions and response generation for the 6-stage
    activation dialogue.
    """

    def __init__(
        self,
        fusion_engine: FusionEngine | None = None,
    ) -> None:
        self._fusion = fusion_engine or FusionEngine()
        self._current_stage: DialogueStage = DialogueStage.AMBIENT
        self._last_blend: PersonaBlend | None = None
        self._silent_mode: bool = False

    @property
    def current_stage(self) -> DialogueStage:
        return self._current_stage

    # ------------------------------------------------------------------
    # Stage entry points
    # ------------------------------------------------------------------

    def trigger_entry(self, toi_config: "TOIConfig | None" = None) -> StageResult:
        """
        Called when the CDE detects distress above GREEN.  Moves to Stage 1
        (consent checkpoint) if not already past Stage 0.
        """
        self._current_stage = DialogueStage.CONSENT_CHECKPOINT
        return StageResult(
            stage=DialogueStage.CONSENT_CHECKPOINT,
            next_stage=DialogueStage.DISTRESS_ASSESSMENT,
            message=self._consent_prompt(),
            options=[
                {"id": "yes", "label": "Yes, I'd like support right now"},
                {"id": "no", "label": "No, I'm okay for now"},
                {"id": "silent", "label": "Just be here with me (silent mode)"},
            ],
        )

    def handle_consent(
        self,
        user_response: str,
        toi_config: "TOIConfig | None" = None,
    ) -> StageResult:
        """
        Process the user's Stage 1 consent response.

        Accepted: 'yes' / affirmative → move to Stage 2.
        Declined: 'no' → return to ambient.
        Silent: 'silent' → activate Silent Mode, skip to Stage 3 with MYRA.
        """
        resp = user_response.strip().lower()

        if resp in ("no", "n", "nope", "i'm okay", "i'm fine", "not now"):
            self._current_stage = DialogueStage.AMBIENT
            return StageResult(
                stage=DialogueStage.CONSENT_CHECKPOINT,
                next_stage=DialogueStage.AMBIENT,
                message=(
                    "Okay, I'm here in the background whenever you're ready.  "
                    "No pressure at all."
                ),
            )

        if resp in ("silent", "just be here", "silent mode", "be here"):
            self._silent_mode = True
            self._current_stage = DialogueStage.PERSONA_RESPONSE
            blend = self._fusion.compute(
                distress_input="shutdown",
                toi_config=toi_config,
            )
            self._last_blend = blend
            return StageResult(
                stage=DialogueStage.CONSENT_CHECKPOINT,
                next_stage=DialogueStage.PERSONA_RESPONSE,
                message="",
                persona_blend=blend,
                silent_mode=True,
                metadata={"anchor": "🌿"},
            )

        # Default: any affirmative → proceed to Stage 2
        self._current_stage = DialogueStage.DISTRESS_ASSESSMENT
        return StageResult(
            stage=DialogueStage.DISTRESS_ASSESSMENT,
            next_stage=DialogueStage.PERSONA_RESPONSE,
            message=(
                "What feels closest to what you're experiencing right now?  "
                "There's no wrong answer."
            ),
            options=STAGE2_OPTIONS,
        )

    def handle_distress_assessment(
        self,
        selection_id: str,
        raw_text: str = "",
        toi_config: "TOIConfig | None" = None,
    ) -> StageResult:
        """
        Process the user's Stage 2 distress assessment selection.
        Maps the selection to the Fusion Engine and returns a persona blend.

        Parameters
        ----------
        selection_id:
            One of the STAGE2_OPTIONS 'id' values, or raw free text.
        raw_text:
            Optional additional context from the user.
        toi_config:
            Active TOI for this session.
        """
        option = next(
            (o for o in STAGE2_OPTIONS if o["id"] == selection_id),
            None,
        )

        if option is None:
            # Treat the selection as free text and classify it via FusionEngine
            blend = self._fusion.compute(
                distress_input=selection_id,
                raw_text=raw_text,
                toi_config=toi_config,
            )
            silent = blend.distress_type == "shutdown"
        else:
            blend = self._fusion.compute(
                distress_input=option["distress_type"],
                raw_text=raw_text,
                toi_config=toi_config,
            )
            silent = option["silent_mode"]

        self._last_blend = blend
        self._silent_mode = silent
        self._current_stage = DialogueStage.PERSONA_RESPONSE

        return StageResult(
            stage=DialogueStage.DISTRESS_ASSESSMENT,
            next_stage=DialogueStage.PERSONA_RESPONSE,
            message="",
            persona_blend=blend,
            silent_mode=silent,
            metadata={"distress_type": blend.distress_type, "rationale": blend.rationale},
        )

    def handle_checkin(self, helpful: bool) -> StageResult:
        """Stage 4 check-in: did the response help?"""
        self._current_stage = DialogueStage.CHECKIN

        if helpful:
            return StageResult(
                stage=DialogueStage.CHECKIN,
                next_stage=DialogueStage.CLOSURE,
                message=(
                    "I'm really glad that helped, even a little.  "
                    "We can keep going, or just rest here."
                ),
                options=[
                    {"id": "continue", "label": "Continue"},
                    {"id": "rest", "label": "Rest here"},
                ],
            )
        return StageResult(
            stage=DialogueStage.CHECKIN,
            next_stage=DialogueStage.DISTRESS_ASSESSMENT,
            message=(
                "That's okay — let's try something different.  "
                "What would feel more supportive right now?"
            ),
            options=STAGE2_OPTIONS,
        )

    def close_session(self) -> StageResult:
        """Stage 5 — graceful closure."""
        self._current_stage = DialogueStage.CLOSURE
        self._silent_mode = False
        return StageResult(
            stage=DialogueStage.CLOSURE,
            next_stage=DialogueStage.AMBIENT,
            message=(
                "You did something really hard by reaching out.  "
                "I'll be here whenever you need me."
            ),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _consent_prompt(self) -> str:
        return (
            "Hey.  I noticed things might be feeling heavy right now.  "
            "Would you like some support?  "
            "You're completely in charge — we only go at your pace."
        )

    def reset(self) -> None:
        """Return the tree to ambient state."""
        self._current_stage = DialogueStage.AMBIENT
        self._last_blend = None
        self._silent_mode = False
