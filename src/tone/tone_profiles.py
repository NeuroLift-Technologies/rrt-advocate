"""
Tone Profiles - RRT AIdvocAIte
Configurable tone configurations for LLM prompt engineering.
Loads from config/tone_profiles.yaml; maps to user's TOI tone_profile.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import yaml

# Default profile when TOI doesn't specify
DEFAULT_TONE_PROFILE = "supportive_default"


@dataclass
class ToneProfile:
    """A tone profile defining how the RRT Advocate responds."""
    id: str
    name: str
    description: str
    characteristics: List[str]
    ideal_personas: List[str]
    prompt_guidance: str
    example_phrases: List[str] = field(default_factory=list)

    def to_prompt_section(self) -> str:
        """Render this profile as a section for LLM prompt assembly."""
        lines = [
            f"## Tone: {self.name}",
            self.description,
            "",
            "Characteristics:",
        ]
        for c in self.characteristics:
            lines.append(f"- {c}")
        lines.extend([
            "",
            "Guidance:",
            self.prompt_guidance.strip(),
        ])
        if self.example_phrases:
            lines.extend([
                "",
                "Example phrases to use:",
            ])
            for p in self.example_phrases:
                lines.append(f'- "{p}"')
        return "\n".join(lines)


def _load_tone_config() -> Dict[str, Any]:
    """Load tone profiles from config file. Local-only, no cloud."""
    config_paths = [
        "config/tone_profiles.yaml",
        os.path.join(os.path.dirname(__file__), "..", "..", "config", "tone_profiles.yaml"),
    ]
    for path in config_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


_tone_cache: Optional[Dict[str, ToneProfile]] = None


def get_tone_profile(profile_id: Optional[str] = None) -> ToneProfile:
    """
    Get a tone profile by ID. Falls back to supportive_default if not found.
    Anti-gaslight: never judge the request; return safe default on error.
    """
    global _tone_cache
    if _tone_cache is None:
        raw = _load_tone_config()
        profiles = raw.get("tone_profiles", {})
        _tone_cache = {}
        for pid, data in profiles.items():
            _tone_cache[pid] = ToneProfile(
                id=pid,
                name=data.get("name", pid),
                description=data.get("description", ""),
                characteristics=data.get("characteristics", []),
                ideal_personas=data.get("ideal_personas", []),
                prompt_guidance=data.get("prompt_guidance", ""),
                example_phrases=data.get("example_phrases", []),
            )
    key = (profile_id or "").strip().lower() or DEFAULT_TONE_PROFILE
    if key not in _tone_cache:
        key = DEFAULT_TONE_PROFILE
    return _tone_cache.get(key, _tone_cache[DEFAULT_TONE_PROFILE])
