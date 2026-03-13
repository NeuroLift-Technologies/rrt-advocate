"""
Shared data models for the RRT AIdvocAIte system.

All enums, dataclasses, and type aliases used across the Protective Layer
live here so every sub-package imports from a single source of truth.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CrisisLevel(Enum):
    GREEN = "stable"
    YELLOW = "elevated"
    ORANGE = "high"
    RED = "critical"
    BLACK = "emergency"


class ResponseStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUCCESSFUL = "successful"
    ESCALATED = "escalated"
    FAILED = "failed"


class PersonaName(Enum):
    ASH = "ash"
    SOL = "sol"
    ECHO = "echo"
    KAI = "kai"
    MYRA = "myra"


class ToneProfile(Enum):
    SUPPORTIVE = "supportive"
    MINIMAL = "minimal"
    DIRECTIVE = "directive"
    THERAPEUTIC = "therapeutic"


class DialogueStage(Enum):
    STAGE_0_DETECTION = 0
    STAGE_1_CONSENT = 1
    STAGE_2_ASSESSMENT = 2
    STAGE_3_SUPPORT = 3
    STAGE_4_GROUNDING = 4
    STAGE_5_TRANSITION = 5


class DistressInput(Enum):
    MELTDOWN = "meltdown"
    TASK_PARALYSIS = "task_paralysis"
    SELF_BLAME = "self_blame"
    HYPERFOCUS_LOOP = "hyperfocus_loop"
    SHUTDOWN = "shutdown"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PersonaWeights:
    """Blend weights for the five Original Guides (0.0 – 1.0 each)."""
    ash: float = 0.2
    sol: float = 0.2
    echo: float = 0.2
    kai: float = 0.2
    myra: float = 0.2

    def as_dict(self) -> Dict[str, float]:
        return {
            PersonaName.ASH.value: self.ash,
            PersonaName.SOL.value: self.sol,
            PersonaName.ECHO.value: self.echo,
            PersonaName.KAI.value: self.kai,
            PersonaName.MYRA.value: self.myra,
        }

    def validate(self) -> None:
        for name in ("ash", "sol", "echo", "kai", "myra"):
            val = getattr(self, name)
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"Weight for {name} must be 0.0–1.0, got {val}")


@dataclass
class TOIConfig:
    """User-defined Terms of Interaction preferences."""
    tone: ToneProfile = ToneProfile.SUPPORTIVE
    pacing: str = "adaptive"
    cognitive_scaffolding: bool = True
    safety_boundaries: Dict[str, Any] = field(default_factory=lambda: {
        "allow_external_escalation": True,
        "allow_emergency_contacts": True,
        "silent_mode_available": True,
        "max_prompt_length": "medium",
    })
    persona_overrides: Optional[PersonaWeights] = None


@dataclass
class CDESignal:
    """Output from a single Crisis Detection Engine layer."""
    layer: str
    score: float
    indicators: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrisisAssessment:
    """Aggregate crisis assessment produced by the CDE."""
    timestamp: datetime
    crisis_level: CrisisLevel
    primary_indicators: List[str]
    secondary_indicators: List[str]
    confidence_score: float
    estimated_duration: Optional[timedelta]
    recommended_interventions: List[str]
    escalation_threshold: float
    user_safety_score: float
    cde_signals: List[CDESignal] = field(default_factory=list)
    context_factors: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonaResponse:
    """A single persona's contribution to a blended response."""
    persona: PersonaName
    weight: float
    message: str
    tone: ToneProfile
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FusedResponse:
    """The final blended output delivered to the user."""
    response_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: datetime = field(default_factory=datetime.now)
    stage: DialogueStage = DialogueStage.STAGE_3_SUPPORT
    tone: ToneProfile = ToneProfile.SUPPORTIVE
    primary_message: str = ""
    persona_contributions: List[PersonaResponse] = field(default_factory=list)
    weights_used: Optional[PersonaWeights] = None
    silent_mode: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterventionResponse:
    """Response data from a crisis intervention."""
    intervention_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: ResponseStatus = ResponseStatus.PENDING
    effectiveness_score: Optional[float] = None
    user_feedback: Optional[str] = None
    side_effects: List[str] = field(default_factory=list)
    follow_up_required: bool = False


@dataclass
class UserMessage:
    """An incoming message from the user to the RRT system."""
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
