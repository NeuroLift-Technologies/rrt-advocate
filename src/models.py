"""
Shared models for the TOI-compliant RRT Advocate architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ToneProfile(str, Enum):
    """Supported tone profiles driven by user TOI."""

    SUPPORTIVE_DEFAULT = "supportive_default"
    MINIMAL = "minimal"
    DIRECTIVE = "directive"
    THERAPEUTIC_REFLECTIVE = "therapeutic_reflective"


class DistressSignal(str, Enum):
    """Stage-2 distress options in the tiered activation tree."""

    MELTDOWN = "everything_hurts_meltdown"
    TASKS_IMPOSSIBLE = "cant_do_basic_tasks"
    SELF_BLAME_LOOP = "cant_stop_self_blame"
    HYPERFOCUS_LOOP = "stuck_in_hyperfocus_loop"
    SHUTDOWN = "dont_know_shutdown"
    UNSPECIFIED = "unspecified"


@dataclass
class TOIConfig:
    """User Terms of Interaction configuration."""

    tone_profile: ToneProfile = ToneProfile.SUPPORTIVE_DEFAULT
    pacing: str = "gentle"
    cognitive_scaffolding: str = "moderate"
    safety_boundaries: Dict[str, Any] = field(
        default_factory=lambda: {
            "require_consent_before_activation": True,
            "disallowed_response_patterns": [],
            "allow_external_escalation_without_consent": False,
        }
    )


@dataclass
class OTOIPolicy:
    """Policy controls for persona orchestration behavior."""

    max_persona_weight: float = 0.7
    min_active_personas: int = 2


@dataclass
class FusionResult:
    """Result of persona fusion."""

    distress_signal: DistressSignal
    persona_weights: Dict[str, float]
    silent_mode: bool = False
    rationale: str = ""


@dataclass
class CDELayerResult:
    """Single CDE layer output."""

    score: float
    signals: Dict[str, float] = field(default_factory=dict)


@dataclass
class CDEAssessment:
    """Aggregate result from local-first crisis detection engine."""

    layer_1_keywords: CDELayerResult
    layer_2_sentiment: CDELayerResult
    layer_3_behavior: CDELayerResult
    overall_risk_score: float
    distress_tags: List[str]
    polarity: float


@dataclass
class RRTResponse:
    """Structured orchestration payload for the caller/LLM layer."""

    stage: int
    consent_required: bool
    consent_granted: bool
    distress_signal: DistressSignal
    fusion: FusionResult
    cde: CDEAssessment
    tone_profile: ToneProfile
    prompt_package: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageDirective:
    """Dialogue tree routing decision."""

    stage: int
    needs_consent: bool
    distress_signal: DistressSignal = DistressSignal.UNSPECIFIED
    prompt: Optional[str] = None
