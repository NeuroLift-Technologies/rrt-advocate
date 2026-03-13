"""
Tone profile rendering for TOI-driven response packaging.
"""

from __future__ import annotations

from typing import Dict

from .models import ToneProfile


TONE_PROMPT_PREFIX: Dict[ToneProfile, str] = {
    ToneProfile.SUPPORTIVE_DEFAULT: (
        "Tone: warm, validating, and non-judgmental. Use short supportive sentences."
    ),
    ToneProfile.MINIMAL: (
        "Tone: extremely concise. Minimize cognitive load, one small step at a time."
    ),
    ToneProfile.DIRECTIVE: (
        "Tone: clear and action-oriented. Use concrete instructions and sequencing."
    ),
    ToneProfile.THERAPEUTIC_REFLECTIVE: (
        "Tone: empathic reflective mirroring with gentle, soft Socratic questions."
    ),
}


class ToneProfileRenderer:
    """Builds prompt payloads that downstream LLM responders can follow."""

    def render(
        self,
        *,
        tone_profile: ToneProfile,
        pacing: str,
        cognitive_scaffolding: str,
        silent_mode: bool,
        persona_summary: str,
        response_guidance: str,
    ) -> str:
        prefix = TONE_PROMPT_PREFIX[tone_profile]
        silent_clause = (
            "Silent Mode: enabled. Use calm visuals language, no timers, no urgency markers."
            if silent_mode
            else "Silent Mode: disabled."
        )
        return (
            f"{prefix}\n"
            f"Pacing: {pacing}.\n"
            f"Cognitive scaffolding: {cognitive_scaffolding}.\n"
            f"{silent_clause}\n"
            f"Persona blend: {persona_summary}.\n"
            f"Guidance: {response_guidance}"
        )
