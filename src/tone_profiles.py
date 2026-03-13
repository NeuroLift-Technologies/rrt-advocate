"""Configurable tone profiles for prompt/response shaping."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ToneProfile:
    name: str
    prompt_directive: str
    max_sentences: int
    sentence_style: str


class ToneProfileEngine:
    """Handles TOI-driven tone profile selection and response formatting."""

    _defaults: Dict[str, ToneProfile] = {
        "supportive_default": ToneProfile(
            name="supportive_default",
            prompt_directive="Warm, validating, and shame-resistant language.",
            max_sentences=4,
            sentence_style="gentle",
        ),
        "minimal": ToneProfile(
            name="minimal",
            prompt_directive="Ultra concise language with the lowest possible cognitive load.",
            max_sentences=2,
            sentence_style="brief",
        ),
        "directive": ToneProfile(
            name="directive",
            prompt_directive="Clear, action-oriented language with explicit next steps.",
            max_sentences=3,
            sentence_style="instructional",
        ),
        "therapeutic_reflective": ToneProfile(
            name="therapeutic_reflective",
            prompt_directive="Empathetic mirroring and soft Socratic questioning.",
            max_sentences=5,
            sentence_style="reflective",
        ),
    }

    def __init__(self, config: Optional[Dict[str, object]] = None):
        self._profiles = dict(self._defaults)
        cfg = config.get("tone_profiles", {}) if isinstance(config, dict) else {}
        for key, value in cfg.items():
            if key not in self._profiles or not isinstance(value, dict):
                continue
            original = self._profiles[key]
            self._profiles[key] = ToneProfile(
                name=key,
                prompt_directive=str(value.get("prompt_directive", original.prompt_directive)),
                max_sentences=int(value.get("max_sentences", original.max_sentences)),
                sentence_style=str(value.get("sentence_style", original.sentence_style)),
            )

    def get_profile(self, name: str) -> ToneProfile:
        return self._profiles.get(name, self._profiles["supportive_default"])

    def format_response(
        self,
        tone_name: str,
        personas: List[str],
        draft_lines: List[str],
        silent_mode: bool = False,
    ) -> str:
        profile = self.get_profile(tone_name)
        if not draft_lines:
            draft_lines = ["I'm here with you, and we can go one step at a time."]

        if profile.name == "minimal":
            return " ".join(line.strip() for line in draft_lines[:1])

        if profile.name == "directive":
            steps = draft_lines[: profile.max_sentences]
            numbered = [f"{idx + 1}) {line.strip()}" for idx, line in enumerate(steps)]
            return " ".join(numbered)

        if profile.name == "therapeutic_reflective":
            combined = " ".join(line.strip() for line in draft_lines[: profile.max_sentences])
            return f"{combined} What feels most supportive right now?"

        # supportive_default
        prefix = " / ".join(personas).upper() if personas else "RRT"
        suffix = " Silent Mode is on." if silent_mode else ""
        return f"{prefix}: " + " ".join(line.strip() for line in draft_lines[: profile.max_sentences]) + suffix
