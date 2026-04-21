"""
TOI and OTOI Data Models
Solidarity Framework — Constitutional Layer

Defines the data structures for the Terms of Interaction (TOI) and
Orchestrated TOI (OTOI) governance layer.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class ToneProfile(Enum):
    """The four configurable tone profiles for LLM prompt engineering."""
    SUPPORTIVE_DEFAULT = "supportive_default"
    MINIMAL = "minimal"
    DIRECTIVE = "directive"
    THERAPEUTIC_REFLECTIVE = "therapeutic_reflective"


class Pacing(Enum):
    """Interaction pacing — controls follow-up prompt timing."""
    STANDARD = "standard"
    SLOW = "slow"
    VERY_SLOW = "very_slow"


@dataclass
class TOIConfig:
    """
    Terms of Interaction configuration.

    This is the user's interaction contract. Every RRT response must pass
    through TOI validation before delivery. No persona may override the
    user's explicit interaction contract.
    """
    tone_profile: ToneProfile = ToneProfile.SUPPORTIVE_DEFAULT
    pacing: Pacing = Pacing.STANDARD
    cognitive_scaffolding_level: int = 2  # 0=none, 1=light, 2=moderate, 3=full
    safety_boundaries: List[str] = field(default_factory=list)
    silent_mode_preferred: bool = False
    allow_timers: bool = True
    allow_task_loops: bool = False  # Anti-forced-productivity: never default to True
    preferred_personas: List[str] = field(default_factory=list)
    excluded_personas: List[str] = field(default_factory=list)
    max_response_length: Optional[int] = None  # None = derived from tone_profile
    consent_given: bool = False  # Stage 1 consent — must be True before full RRT

    def requires_silent_mode(self) -> bool:
        return self.silent_mode_preferred

    def persona_is_excluded(self, persona_name: str) -> bool:
        return persona_name.lower() in [p.lower() for p in self.excluded_personas]

    def persona_is_preferred(self, persona_name: str) -> bool:
        return persona_name.lower() in [p.lower() for p in self.preferred_personas]

    def effective_max_length(self) -> int:
        """Return the effective max response length based on tone profile."""
        if self.max_response_length is not None:
            return self.max_response_length
        defaults = {
            ToneProfile.SUPPORTIVE_DEFAULT: 200,
            ToneProfile.MINIMAL: 50,
            ToneProfile.DIRECTIVE: 150,
            ToneProfile.THERAPEUTIC_REFLECTIVE: 250,
        }
        return defaults.get(self.tone_profile, 200)


@dataclass
class OTOIState:
    """
    Orchestrated TOI runtime state.

    Tracks the active persona routing decisions and TOI compliance
    status during a live RRT session. The OTOI state ensures no single
    persona can override the user's TOI contract.
    """
    session_id: str
    toi_config: TOIConfig
    active_personas: List[str] = field(default_factory=list)
    dominant_persona: Optional[str] = None
    silent_mode_active: bool = False
    consent_checkpoint_passed: bool = False
    last_interaction: Optional[datetime] = None
    interaction_count: int = 0
    toi_violations_blocked: int = 0
    context_metadata: Dict[str, Any] = field(default_factory=dict)

    def record_interaction(self):
        self.interaction_count += 1
        self.last_interaction = datetime.now()

    def block_violation(self, violation_description: str):
        """Record that a TOI violation was detected and blocked."""
        self.toi_violations_blocked += 1
        if "violations" not in self.context_metadata:
            self.context_metadata["violations"] = []
        self.context_metadata["violations"].append({
            "timestamp": datetime.now().isoformat(),
            "description": violation_description,
        })
