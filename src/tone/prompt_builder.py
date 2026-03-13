"""
Prompt Builder - RRT AIdvocAIte
Modular LLM prompt assembly using TOI, persona fusion weights, and tone profile.
Local-first: no cloud calls; assembles prompt text only.
"""

from typing import Dict, Optional, Any
from ..governance.toi_parser import TOIConfig
from ..personas.fusion_engine import PersonaWeights
from .tone_profiles import get_tone_profile, ToneProfile


def build_crisis_response_prompt(
    toi: Optional[TOIConfig] = None,
    persona_weights: Optional[PersonaWeights] = None,
    distress_input: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Assemble a complete LLM prompt for crisis response.
    Respects TOI (tone, pacing, safety boundaries) and persona fusion.
    """
    tone_id = (toi and toi.tone_profile) or "supportive_default"
    tone = get_tone_profile(tone_id)

    sections = []

    # 1. Role and framework
    sections.append(_role_section())

    # 2. TOI constraints (safety boundaries)
    if toi:
        sections.append(_toi_section(toi))

    # 3. Tone profile
    sections.append(tone.to_prompt_section())

    # 4. Persona blend (if we have weights)
    if persona_weights:
        sections.append(_persona_section(persona_weights))

    # 5. Distress context
    if distress_input:
        sections.append(_distress_section(distress_input))

    # 6. Additional context
    if context:
        sections.append(_context_section(context))

    return "\n\n---\n\n".join(sections)


def _role_section() -> str:
    return """# RRT AIdvocAIte - Protective Layer
You are the RRT AIdvocAIte within the HAIEF Solidarity Framework. Your role is to provide neurodivergent-informed crisis support. You respond according to the user's Terms of Interaction (TOI) and the blended persona guidance below. Prioritize user agency and consent; never force productivity when the user indicates burnout."""


def _toi_section(toi: "TOIConfig") -> str:
    lines = [
        "## Terms of Interaction (TOI)",
        f"- Tone profile: {toi.tone_profile or 'supportive_default'}",
        f"- Pacing: {toi.pacing or 'moderate'}",
        f"- Cognitive scaffolding: {toi.cognitive_scaffolding or 'standard'}",
    ]
    if toi.safety_boundaries:
        lines.append("- Safety boundaries: " + "; ".join(toi.safety_boundaries))
    return "\n".join(lines)


def _persona_section(weights: PersonaWeights) -> str:
    active = [
        (name, w) for name, w in weights.as_dict().items() if w > 0
    ]
    active.sort(key=lambda x: -x[1])
    lines = [
        "## Persona Blend (prioritize these voices in order)",
    ]
    for name, w in active:
        lines.append(f"- {name.capitalize()}: weight {w:.2f}")
    return "\n".join(lines)


def _distress_section(input_text: str) -> str:
    return f"""## User's Distress Expression
"{input_text}"

Respond to this specific experience with the tone and persona blend above."""


def _context_section(ctx: Dict[str, Any]) -> str:
    lines = ["## Additional Context"]
    for k, v in ctx.items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)


class PromptBuilder:
    """
    Modular LLM prompt assembly for RRT Advocate responses.
    Used by RRTAdvocate.generate_response().
    """

    def build(
        self,
        persona_weights: Dict[str, float],
        tone_profile: ToneProfile,
        user_message: str,
        silent_mode: bool = False,
    ) -> str:
        """
        Assemble prompt for LLM using persona blend, tone, and user message.
        """
        sections = [_role_section(), tone_profile.to_prompt_section()]
        sections.append(_persona_section_dict(persona_weights))
        if silent_mode:
            sections.append(
                "## Silent Mode: Use minimal words. No timers. No lists. Calm presence only."
            )
        sections.append(_distress_section(user_message))
        return "\n\n---\n\n".join(sections)


def _persona_section_dict(weights: Dict[str, float]) -> str:
    """Persona blend section from Dict[str, float]."""
    active = [(name, w) for name, w in weights.items() if w > 0]
    active.sort(key=lambda x: -x[1])
    lines = ["## Persona Blend (prioritize these voices in order)"]
    for name, w in active:
        lines.append(f"- {name.capitalize()}: weight {w:.2f}")
    return "\n".join(lines)
