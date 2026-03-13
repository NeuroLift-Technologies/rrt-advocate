"""Core data models for the Solidarity Framework protective layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class CrisisLevel(str, Enum):
    """Support intensity bands used by the local-first detection engine."""

    GREEN = "stable"
    YELLOW = "elevated"
    ORANGE = "high"
    RED = "critical"
    BLACK = "emergency"


class ResponseStatus(str, Enum):
    """Lifecycle status for any manual or automated intervention."""

    PENDING = "pending"
    ACTIVE = "active"
    SUCCESSFUL = "successful"
    ESCALATED = "escalated"
    FAILED = "failed"


class ToneProfile(str, Enum):
    """Supported tone profiles enforced by TOI middleware."""

    SUPPORTIVE_DEFAULT = "supportive_default"
    MINIMAL = "minimal"
    DIRECTIVE = "directive"
    THERAPEUTIC_REFLECTIVE = "therapeutic_reflective"


class DistressSignal(str, Enum):
    """Tier-2 user-selected distress flavors."""

    MELTDOWN = "meltdown"
    TASK_PARALYSIS = "task_paralysis"
    SELF_BLAME = "self_blame"
    HYPERFOCUS_LOOP = "hyperfocus_loop"
    SHUTDOWN = "shutdown"

    @classmethod
    def from_input(cls, value: Optional[str]) -> Optional["DistressSignal"]:
        """Map a label or enum value into a canonical distress signal."""
        if value is None:
            return None

        normalized = value.strip().lower()
        aliases = {
            "everything hurts / meltdown": cls.MELTDOWN,
            "meltdown": cls.MELTDOWN,
            "everything hurts": cls.MELTDOWN,
            "can't do basic tasks": cls.TASK_PARALYSIS,
            "cant do basic tasks": cls.TASK_PARALYSIS,
            "task paralysis": cls.TASK_PARALYSIS,
            "can't stop self-blame": cls.SELF_BLAME,
            "cant stop self-blame": cls.SELF_BLAME,
            "self-blame": cls.SELF_BLAME,
            "stuck in hyperfocus/loop": cls.HYPERFOCUS_LOOP,
            "stuck in hyperfocus": cls.HYPERFOCUS_LOOP,
            "hyperfocus loop": cls.HYPERFOCUS_LOOP,
            "don't know / shut down": cls.SHUTDOWN,
            "dont know / shut down": cls.SHUTDOWN,
            "shut down": cls.SHUTDOWN,
            "shutdown": cls.SHUTDOWN,
        }
        return aliases.get(normalized) or next(
            (signal for signal in cls if signal.value == normalized),
            None,
        )


class DialogueStage(int, Enum):
    """User-led activation path for the protective layer."""

    STAGE_0_IDLE = 0
    STAGE_1_CONSENT = 1
    STAGE_2_SIGNAL_SELECTION = 2
    STAGE_3_SUPPORT = 3
    STAGE_4_STABILIZATION = 4
    STAGE_5_ESCALATION = 5


@dataclass
class SilentModeConfig:
    """Non-verbal / low-demand interaction preferences."""

    enabled: bool = True
    no_timers: bool = True
    calm_visuals: bool = True
    minimal_text: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "no_timers": self.no_timers,
            "calm_visuals": self.calm_visuals,
            "minimal_text": self.minimal_text,
        }


@dataclass
class SafetyBoundaries:
    """Hard constraints that the orchestration layer must not cross."""

    require_stage1_consent: bool = True
    allow_directive_tone: bool = True
    allow_reflective_questions: bool = True
    protect_from_productivity_pressure: bool = True
    allow_external_escalation: bool = False
    max_single_persona_weight: float = 0.58

    def to_dict(self) -> Dict[str, Any]:
        return {
            "require_stage1_consent": self.require_stage1_consent,
            "allow_directive_tone": self.allow_directive_tone,
            "allow_reflective_questions": self.allow_reflective_questions,
            "protect_from_productivity_pressure": self.protect_from_productivity_pressure,
            "allow_external_escalation": self.allow_external_escalation,
            "max_single_persona_weight": self.max_single_persona_weight,
        }


@dataclass
class TOIConfig:
    """Parsed Terms of Interaction contract for a user."""

    tone: ToneProfile = ToneProfile.SUPPORTIVE_DEFAULT
    pacing: str = "gentle"
    cognitive_scaffolding: str = "layered"
    preferred_personas: List[str] = field(default_factory=list)
    blocked_personas: List[str] = field(default_factory=list)
    silent_mode: SilentModeConfig = field(default_factory=SilentModeConfig)
    safety_boundaries: SafetyBoundaries = field(default_factory=SafetyBoundaries)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tone": self.tone.value,
            "pacing": self.pacing,
            "cognitive_scaffolding": self.cognitive_scaffolding,
            "preferred_personas": list(self.preferred_personas),
            "blocked_personas": list(self.blocked_personas),
            "silent_mode": self.silent_mode.to_dict(),
            "safety_boundaries": self.safety_boundaries.to_dict(),
        }


@dataclass
class CDELayerScore:
    """Inspection result from one local CDE layer."""

    layer_name: str
    score: float
    indicators: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_name": self.layer_name,
            "score": self.score,
            "indicators": list(self.indicators),
            "details": dict(self.details),
        }


@dataclass
class CrisisDetectionResult:
    """Aggregate output from the local-first crisis detection engine."""

    timestamp: datetime
    crisis_level: CrisisLevel
    overall_score: float
    layer_scores: List[CDELayerScore]
    primary_indicators: List[str]
    secondary_indicators: List[str]
    semantic_categories: List[str]
    dominant_distress: Optional[DistressSignal]
    sentiment_shift: float
    behavioral_risk: float
    safety_keywords: List[str] = field(default_factory=list)
    local_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "crisis_level": self.crisis_level.value,
            "overall_score": self.overall_score,
            "layer_scores": [layer.to_dict() for layer in self.layer_scores],
            "primary_indicators": list(self.primary_indicators),
            "secondary_indicators": list(self.secondary_indicators),
            "semantic_categories": list(self.semantic_categories),
            "dominant_distress": self.dominant_distress.value if self.dominant_distress else None,
            "sentiment_shift": self.sentiment_shift,
            "behavioral_risk": self.behavioral_risk,
            "safety_keywords": list(self.safety_keywords),
            "local_only": self.local_only,
        }


@dataclass
class PersonaBlend:
    """Weighted blend of the five OG personas."""

    weights: Dict[str, float]
    dominant_personas: List[str]
    tone_profile: ToneProfile
    silent_mode: bool
    rationale: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weights": dict(self.weights),
            "dominant_personas": list(self.dominant_personas),
            "tone_profile": self.tone_profile.value,
            "silent_mode": self.silent_mode,
            "rationale": list(self.rationale),
        }


@dataclass
class CrisisAssessment:
    """Public assessment structure exposed by the RRT advocate."""

    timestamp: datetime
    crisis_level: CrisisLevel
    primary_indicators: List[str]
    secondary_indicators: List[str]
    confidence_score: float
    estimated_duration: Optional[timedelta]
    recommended_interventions: List[str]
    escalation_threshold: float
    user_safety_score: float
    dominant_distress: Optional[DistressSignal] = None
    persona_weights: Dict[str, float] = field(default_factory=dict)
    recommended_tone: ToneProfile = ToneProfile.SUPPORTIVE_DEFAULT
    silent_mode: bool = False
    context_factors: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "crisis_level": self.crisis_level.value,
            "primary_indicators": list(self.primary_indicators),
            "secondary_indicators": list(self.secondary_indicators),
            "confidence_score": self.confidence_score,
            "estimated_duration_minutes": (
                int(self.estimated_duration.total_seconds() // 60)
                if self.estimated_duration
                else None
            ),
            "recommended_interventions": list(self.recommended_interventions),
            "escalation_threshold": self.escalation_threshold,
            "user_safety_score": self.user_safety_score,
            "dominant_distress": self.dominant_distress.value if self.dominant_distress else None,
            "persona_weights": dict(self.persona_weights),
            "recommended_tone": self.recommended_tone.value,
            "silent_mode": self.silent_mode,
            "context_factors": dict(self.context_factors),
        }


@dataclass
class InterventionResponse:
    """State container for manual interventions and follow-up hooks."""

    intervention_id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: ResponseStatus
    effectiveness_score: Optional[float]
    user_feedback: Optional[str]
    side_effects: List[str] = field(default_factory=list)
    follow_up_required: bool = False


@dataclass
class ResponsePlan:
    """Response plan after TOI gating, fusion, and dialogue staging."""

    stage: DialogueStage
    next_stage: Optional[DialogueStage]
    consent_required: bool
    consent_granted: bool
    user_message: str
    options: List[str]
    system_prompt: str
    toi: TOIConfig
    detection: CrisisDetectionResult
    blend: Optional[PersonaBlend]
    ui_hints: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": int(self.stage),
            "next_stage": int(self.next_stage) if self.next_stage is not None else None,
            "consent_required": self.consent_required,
            "consent_granted": self.consent_granted,
            "user_message": self.user_message,
            "options": list(self.options),
            "system_prompt": self.system_prompt,
            "toi": self.toi.to_dict(),
            "detection": self.detection.to_dict(),
            "blend": self.blend.to_dict() if self.blend else None,
            "ui_hints": dict(self.ui_hints),
        }
