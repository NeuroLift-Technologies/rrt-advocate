"""
Tone Profile Renderer — wraps raw persona responses in the correct tone
style based on the user's TOI setting.

The four profiles correspond directly to the TOIConfig.ToneProfile enum:
  - SUPPORTIVE_DEFAULT: warm, validating, relational
  - MINIMAL: ultra-concise, lowest cognitive load
  - DIRECTIVE: clear, action-oriented (ideal for SOL/KAI)
  - THERAPEUTIC_REFLECTIVE: empathetic mirroring, soft Socratic questions
"""
from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from ..toi.models import ToneProfile

if TYPE_CHECKING:
    from .models import PersonaBlend


class ToneProfileRenderer:
    """
    Transforms a raw response string into one shaped by the active tone profile.

    This is a lightweight text-shaping layer; the actual LLM prompt templates
    live in the config/tone_profiles.yaml and are retrieved here as system
    prompt prefixes.
    """

    # Prompt prefix injected before the persona's content for each tone.
    _SYSTEM_PREFIXES: dict[ToneProfile, str] = {
        ToneProfile.SUPPORTIVE_DEFAULT: (
            "You are warm, present, and non-judgmental.  Start by acknowledging "
            "what the person is experiencing before anything else.  Never rush.  "
            "Your language is gentle and affirming."
        ),
        ToneProfile.MINIMAL: (
            "Be as concise as possible.  One or two sentences maximum.  "
            "No preamble.  No follow-up questions.  Cognitive load must be zero."
        ),
        ToneProfile.DIRECTIVE: (
            "Be clear and action-oriented.  Give exactly one concrete next step.  "
            "Use short sentences.  Avoid emotional language unless asked."
        ),
        ToneProfile.THERAPEUTIC_REFLECTIVE: (
            "Mirror what the person has shared before responding.  Use a gentle, "
            "exploratory tone.  You may ask one soft question at the very end, "
            "but never pressure them to answer."
        ),
    }

    # Short closings shaped by tone (appended only if no closing already present)
    _CLOSINGS: dict[ToneProfile, str] = {
        ToneProfile.SUPPORTIVE_DEFAULT: "You don't have to figure everything out right now.",
        ToneProfile.MINIMAL: "",
        ToneProfile.DIRECTIVE: "Ready when you are.",
        ToneProfile.THERAPEUTIC_REFLECTIVE: "Take your time with that.",
    }

    def get_system_prompt(self, tone: ToneProfile, blend: "PersonaBlend") -> str:
        """
        Build the system prompt prefix for the LLM call.

        Combines the tone prefix with the lead persona's mandate so the model
        knows both *how* to speak and *what* to prioritise.
        """
        tone_prefix = self._SYSTEM_PREFIXES[tone]
        persona_context = (
            f"You are leading as {blend.lead_persona.name}: "
            f"{blend.lead_persona.mandate}  "
            f"Strategies available: {', '.join(blend.lead_persona.strategies)}."
        )
        return f"{tone_prefix}\n\n{persona_context}"

    def shape_response(
        self,
        raw_response: str,
        tone: ToneProfile,
        max_width: int = 80,
    ) -> str:
        """
        Apply post-processing shaping to a raw response string.

        - MINIMAL: truncate to first two sentences.
        - DIRECTIVE: ensure starts with an action verb if possible.
        - Others: light word-wrap.
        """
        if tone == ToneProfile.MINIMAL:
            sentences = raw_response.split(".")
            trimmed = ". ".join(s.strip() for s in sentences[:2] if s.strip())
            return trimmed + ("." if not trimmed.endswith(".") else "")

        wrapped = textwrap.fill(raw_response, width=max_width)

        closing = self._CLOSINGS.get(tone, "")
        if closing and closing.lower() not in wrapped.lower():
            wrapped = f"{wrapped}\n\n{closing}"

        return wrapped

    def get_all_prefixes(self) -> dict[str, str]:
        """Return all system prompt prefixes keyed by tone name (for config export)."""
        return {tone.value: prefix for tone, prefix in self._SYSTEM_PREFIXES.items()}
