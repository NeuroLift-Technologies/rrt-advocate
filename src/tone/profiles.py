"""
Configurable Tone Profiles — system-prompt preambles and guardrails
that shape how every persona response is presented to the user.

Four canonical profiles, selectable via the user's TOI:

  * Supportive (default) — warm, validating
  * Minimal — extremely concise, lowest cognitive load
  * Directive — clear, action-oriented (ideal for Sol / Kai)
  * Therapeutic — empathetic mirroring, soft Socratic questioning (Ash / Echo)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from src.models import ToneProfile


@dataclass(frozen=True)
class ToneSpec:
    """Immutable specification for a single tone profile."""
    profile: ToneProfile
    label: str
    system_preamble: str
    guardrails: str
    max_sentence_count: int
    ideal_personas: tuple[str, ...]


TONE_REGISTRY: Dict[ToneProfile, ToneSpec] = {
    ToneProfile.SUPPORTIVE: ToneSpec(
        profile=ToneProfile.SUPPORTIVE,
        label="Supportive Default",
        system_preamble=(
            "You are a warm, validating companion. Use gentle language, "
            "affirm the user's feelings, and avoid anything that could feel "
            "like pressure or judgment."
        ),
        guardrails=(
            "Never minimise the user's experience. "
            "Avoid toxic positivity. "
            "Do not suggest productivity unless the user asks."
        ),
        max_sentence_count=6,
        ideal_personas=("ash", "myra"),
    ),
    ToneProfile.MINIMAL: ToneSpec(
        profile=ToneProfile.MINIMAL,
        label="Minimal",
        system_preamble=(
            "You communicate with extreme brevity. Use the fewest words "
            "possible. No filler. Every word must earn its place."
        ),
        guardrails=(
            "Maximum two sentences per turn. "
            "No rhetorical questions. "
            "Prefer fragments over full sentences."
        ),
        max_sentence_count=2,
        ideal_personas=("sol", "kai", "myra"),
    ),
    ToneProfile.DIRECTIVE: ToneSpec(
        profile=ToneProfile.DIRECTIVE,
        label="Directive",
        system_preamble=(
            "You are clear and action-oriented. Give concrete, numbered "
            "steps when appropriate. Be kind but direct."
        ),
        guardrails=(
            "No open-ended questions unless explicitly scaffolding. "
            "Do not lecture or moralise. "
            "Keep instructions to three steps or fewer."
        ),
        max_sentence_count=4,
        ideal_personas=("sol", "kai"),
    ),
    ToneProfile.THERAPEUTIC: ToneSpec(
        profile=ToneProfile.THERAPEUTIC,
        label="Therapeutic / Reflective",
        system_preamble=(
            "You are an empathetic mirror. Use reflective listening, "
            "soft Socratic questioning, and gentle cognitive reframing."
        ),
        guardrails=(
            "Never diagnose. "
            "Avoid prescriptive language. "
            "One question per turn maximum."
        ),
        max_sentence_count=5,
        ideal_personas=("ash", "echo"),
    ),
}


class ToneProfileManager:
    """Look up and apply tone profiles at runtime."""

    @staticmethod
    def get(profile: ToneProfile) -> ToneSpec:
        return TONE_REGISTRY[profile]

    @staticmethod
    def system_preamble(profile: ToneProfile) -> str:
        return TONE_REGISTRY[profile].system_preamble

    @staticmethod
    def guardrails(profile: ToneProfile) -> str:
        return TONE_REGISTRY[profile].guardrails

    @staticmethod
    def all_profiles() -> Dict[ToneProfile, ToneSpec]:
        return dict(TONE_REGISTRY)
