"""
TOI Configuration — Terms of Interaction data models.

The TOI defines the user's explicit interaction contract: how the system
should communicate with them, what pacing feels safe, which cognitive
scaffolding strategies to use, and which safety boundaries must never
be crossed.  Every RRT response is filtered through the active TOI
before it reaches the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class TonePreference(Enum):
    """User-selected communication tone."""
    SUPPORTIVE = "supportive"
    MINIMAL = "minimal"
    DIRECTIVE = "directive"
    THERAPEUTIC = "therapeutic"


class PacingPreference(Enum):
    """Controls how quickly information is delivered."""
    SLOW = "slow"
    MODERATE = "moderate"
    FAST = "fast"
    USER_LED = "user_led"


class CognitiveScaffoldingLevel(Enum):
    """How much structure the system wraps around its responses."""
    NONE = "none"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"


class SafetyBoundary(Enum):
    """Hard boundaries the system must respect."""
    NO_EXTERNAL_CONTACTS = "no_external_contacts"
    NO_TIMERS = "no_timers"
    NO_TASK_LISTS = "no_task_lists"
    NO_PRODUCTIVITY_FRAMING = "no_productivity_framing"
    NO_UNSOLICITED_ADVICE = "no_unsolicited_advice"
    SILENT_MODE_ONLY = "silent_mode_only"


@dataclass
class TOIConfig:
    """
    Full Terms of Interaction configuration for a single user session.

    This is the *contract* between the user and the RRT AIdvocAIte.
    No response may violate these terms once they are set.
    """
    tone: TonePreference = TonePreference.SUPPORTIVE
    pacing: PacingPreference = PacingPreference.USER_LED
    cognitive_scaffolding: CognitiveScaffoldingLevel = CognitiveScaffoldingLevel.MODERATE
    safety_boundaries: List[SafetyBoundary] = field(default_factory=list)

    allowed_personas: List[str] = field(
        default_factory=lambda: ["ash", "sol", "echo", "kai", "myra"]
    )

    max_message_length: Optional[int] = None

    custom_preferences: Dict[str, str] = field(default_factory=dict)

    def persona_allowed(self, persona_id: str) -> bool:
        return persona_id.lower() in [p.lower() for p in self.allowed_personas]

    def boundary_active(self, boundary: SafetyBoundary) -> bool:
        return boundary in self.safety_boundaries

    @classmethod
    def from_dict(cls, data: Dict) -> "TOIConfig":
        """Construct a TOIConfig from a plain dictionary (e.g. loaded from YAML)."""
        tone = TonePreference(data.get("tone", "supportive"))
        pacing = PacingPreference(data.get("pacing", "user_led"))
        scaffolding = CognitiveScaffoldingLevel(
            data.get("cognitive_scaffolding", "moderate")
        )
        boundaries = [
            SafetyBoundary(b) for b in data.get("safety_boundaries", [])
        ]
        return cls(
            tone=tone,
            pacing=pacing,
            cognitive_scaffolding=scaffolding,
            safety_boundaries=boundaries,
            allowed_personas=data.get(
                "allowed_personas", ["ash", "sol", "echo", "kai", "myra"]
            ),
            max_message_length=data.get("max_message_length"),
            custom_preferences=data.get("custom_preferences", {}),
        )

    def to_dict(self) -> Dict:
        return {
            "tone": self.tone.value,
            "pacing": self.pacing.value,
            "cognitive_scaffolding": self.cognitive_scaffolding.value,
            "safety_boundaries": [b.value for b in self.safety_boundaries],
            "allowed_personas": self.allowed_personas,
            "max_message_length": self.max_message_length,
            "custom_preferences": self.custom_preferences,
        }
