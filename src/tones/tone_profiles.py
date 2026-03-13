"""
Configurable Tone Profiles — four distinct communication modes that the
TOI can select.  Each profile governs vocabulary complexity, sentence
length, emotional register, and LLM prompt-engineering directives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ToneType(Enum):
    SUPPORTIVE = "supportive"
    MINIMAL = "minimal"
    DIRECTIVE = "directive"
    THERAPEUTIC = "therapeutic"


@dataclass
class ToneProfile:
    """Full specification for a single tone profile."""
    tone_type: ToneType
    label: str
    description: str
    max_sentence_length: int
    vocabulary_level: str
    emotional_register: str
    llm_system_directive: str
    persona_affinity: Dict[str, float] = field(default_factory=dict)


_PROFILES: Dict[ToneType, ToneProfile] = {
    ToneType.SUPPORTIVE: ToneProfile(
        tone_type=ToneType.SUPPORTIVE,
        label="Supportive Default",
        description="Warm, validating, emotionally present",
        max_sentence_length=30,
        vocabulary_level="everyday",
        emotional_register="warm_validating",
        llm_system_directive=(
            "Respond with warmth and unconditional validation. Use everyday "
            "language. Affirm the user's experience without minimising or "
            "catastrophising. Avoid productivity framing."
        ),
        persona_affinity={"ash": 1.0, "myra": 1.0, "echo": 0.9, "sol": 0.7, "kai": 0.6},
    ),
    ToneType.MINIMAL: ToneProfile(
        tone_type=ToneType.MINIMAL,
        label="Minimal Tone",
        description="Extremely concise, lowest possible cognitive load",
        max_sentence_length=10,
        vocabulary_level="simple",
        emotional_register="neutral_calm",
        llm_system_directive=(
            "Use the fewest words possible. One short sentence per idea. "
            "No metaphors, no questions unless essential. Prioritise "
            "clarity over warmth."
        ),
        persona_affinity={"sol": 0.9, "kai": 0.8, "myra": 0.6, "ash": 0.5, "echo": 0.4},
    ),
    ToneType.DIRECTIVE: ToneProfile(
        tone_type=ToneType.DIRECTIVE,
        label="Directive Tone",
        description="Clear, action-oriented (ideal for Sol/Kai)",
        max_sentence_length=20,
        vocabulary_level="clear",
        emotional_register="calm_confident",
        llm_system_directive=(
            "Be clear and action-oriented. Provide concrete next steps. "
            "Use imperative mood when suggesting actions. Stay calm and "
            "confident. Never shame; frame actions as invitations, not demands."
        ),
        persona_affinity={"sol": 1.0, "kai": 1.0, "echo": 0.5, "ash": 0.4, "myra": 0.3},
    ),
    ToneType.THERAPEUTIC: ToneProfile(
        tone_type=ToneType.THERAPEUTIC,
        label="Therapeutic / Reflective",
        description="Empathetic mirroring, soft Socratic questioning (ideal for Ash/Echo)",
        max_sentence_length=25,
        vocabulary_level="reflective",
        emotional_register="empathetic_curious",
        llm_system_directive=(
            "Mirror the user's emotional state with empathy. Use soft "
            "Socratic questions to invite self-reflection. Never lead "
            "with advice. Validate before exploring. Language should "
            "feel like a skilled, compassionate therapist."
        ),
        persona_affinity={"ash": 1.0, "echo": 1.0, "myra": 0.8, "sol": 0.5, "kai": 0.4},
    ),
}


class ToneManager:
    """Registry and accessor for tone profiles."""

    def __init__(self) -> None:
        self._profiles: Dict[ToneType, ToneProfile] = dict(_PROFILES)

    def get_profile(self, tone: ToneType | str) -> ToneProfile:
        if isinstance(tone, str):
            tone = ToneType(tone)
        return self._profiles[tone]

    def get_llm_directive(self, tone: ToneType | str) -> str:
        return self.get_profile(tone).llm_system_directive

    def get_persona_affinity(self, tone: ToneType | str) -> Dict[str, float]:
        return dict(self.get_profile(tone).persona_affinity)

    @property
    def available_tones(self) -> List[ToneType]:
        return list(self._profiles.keys())

    def register_profile(self, profile: ToneProfile) -> None:
        self._profiles[profile.tone_type] = profile
