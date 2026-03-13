from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any


class ToneProfile(str, Enum):
    SUPPORTIVE_DEFAULT = "supportive_default"
    MINIMAL = "minimal"
    DIRECTIVE = "directive"
    THERAPEUTIC_REFLECTIVE = "therapeutic_reflective"


class ActivationStage(IntEnum):
    STAGE_0_PASSIVE = 0
    STAGE_1_ENTRY = 1
    STAGE_2_DISTRESS_SORT = 2
    STAGE_3_REGULATION = 3
    STAGE_4_STABILIZATION = 4
    STAGE_5_ESCALATION = 5


class DistressInput(str, Enum):
    EVERYTHING_HURTS_MELTDOWN = "Everything hurts / Meltdown"
    CANT_DO_BASIC_TASKS = "Can't do basic tasks"
    CANT_STOP_SELF_BLAME = "Can't stop self-blame"
    STUCK_IN_HYPERFOCUS_LOOP = "Stuck in hyperfocus/loop"
    DONT_KNOW_SHUT_DOWN = "Don't know / Shut down"


PERSONA_ORDER = ("ash", "sol", "echo", "kai", "myra")


@dataclass(frozen=True)
class SafetyBoundaries:
    require_explicit_consent: bool = True
    allow_external_escalation: bool = False
    allow_reflective_questions: bool = True
    allow_silent_mode: bool = True
    max_active_personas: int = 3
    blocked_personas: tuple[str, ...] = ()


@dataclass(frozen=True)
class TOIConfig:
    tone: ToneProfile = ToneProfile.SUPPORTIVE_DEFAULT
    pacing: str = "gentle"
    cognitive_scaffolding: str = "moderate"
    safety_boundaries: SafetyBoundaries = field(default_factory=SafetyBoundaries)


@dataclass
class InteractionContext:
    user_message: str = ""
    distress_input: DistressInput = DistressInput.DONT_KNOW_SHUT_DOWN
    response_latency_seconds: float | None = None
    recent_user_messages: list[str] = field(default_factory=list)
    consent_granted: bool = False
    stage: ActivationStage = ActivationStage.STAGE_1_ENTRY
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CDELayerResult:
    name: str
    score: float
    summary: str
    details: dict[str, float] = field(default_factory=dict)


@dataclass
class CrisisAssessment:
    timestamp: datetime
    distress_input: DistressInput
    severity_score: float
    confidence_score: float
    risk_level: str
    layer_results: list[CDELayerResult]
    semantic_hits: list[str]
    behavioral_flags: list[str]
    silent_mode: bool = False


@dataclass
class StageResponse:
    stage: ActivationStage
    message: str
    tone_profile: ToneProfile
    active_personas: list[str]
    persona_weights: dict[str, float]
    recommended_actions: list[str]
    silent_mode: bool
    consent_required: bool
    metadata: dict[str, Any] = field(default_factory=dict)
