"""
Configurable Tone Profiles
LLM prompt engineering - distinct tone profiles per TOI selection.
"""

from pathlib import Path
from typing import Optional
import yaml

from governance.toi_parser import ToneProfile


DEFAULT_PROFILES = {
    "supportive_default": {
        "description": "Warm, validating. Default for most users.",
        "instructions": (
            "Use a warm, validating tone. Acknowledge feelings before offering support. "
            "Balance empathy with gentle encouragement. Avoid minimizing or rushing."
        ),
        "persona_alignment": ["ash", "echo", "myra"],
    },
    "minimal": {
        "description": "Extremely concise, lowest possible cognitive load.",
        "instructions": (
            "Be extremely concise. Use short sentences. Avoid elaboration. "
            "One idea per message. No fluff. Ideal for cognitive overload."
        ),
        "persona_alignment": ["sol", "myra"],
    },
    "directive": {
        "description": "Clear, action-oriented. Ideal for Sol/Kai scaffolding.",
        "instructions": (
            "Be clear and direct. Offer concrete next steps. Use numbered lists when helpful. "
            "Action-focused. Avoid open-ended questions when user needs structure."
        ),
        "persona_alignment": ["sol", "kai"],
    },
    "therapeutic_reflective": {
        "description": "Empathetic mirroring, soft Socratic questioning. Ideal for Ash/Echo.",
        "instructions": (
            "Mirror feelings gently. Use soft Socratic questions to explore rather than instruct. "
            "Validate first. Invite reflection. Avoid giving advice until invited."
        ),
        "persona_alignment": ["ash", "echo"],
    },
}


class ToneProfileLoader:
    """Load tone profiles from YAML or use defaults."""

    def __init__(self, config_path: Optional[str] = None):
        config_path = config_path or "config/tone_profiles.yaml"
        self._profiles = DEFAULT_PROFILES.copy()

        if Path(config_path).exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                profiles = data.get("profiles", {})
                for name, cfg in profiles.items():
                    self._profiles[name] = {
                        "description": cfg.get("description", ""),
                        "instructions": cfg.get("instructions", "").strip(),
                        "persona_alignment": cfg.get("persona_alignment", []),
                    }

    def get_instructions(self, profile: ToneProfile) -> str:
        """Return prompt instructions for the given tone profile."""
        key = profile.value
        return self._profiles.get(key, self._profiles["supportive_default"])["instructions"]

    def get_persona_alignment(self, profile: ToneProfile) -> list:
        """Return preferred personas for this tone (for prompt hints)."""
        key = profile.value
        return self._profiles.get(key, self._profiles["supportive_default"])["persona_alignment"]


def get_prompt_instructions(profile: ToneProfile, loader: Optional[ToneProfileLoader] = None) -> str:
    """Convenience: get prompt instructions for a tone profile."""
    loader = loader or ToneProfileLoader()
    return loader.get_instructions(profile)
