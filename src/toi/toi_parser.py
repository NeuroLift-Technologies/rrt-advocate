"""
TOI Parser
Solidarity Framework — Constitutional Layer

Parses and validates YAML-based TOI configuration into TOIConfig dataclasses.
Provides defaults for any missing fields, ensuring every interaction
has a valid interaction contract even without explicit user configuration.
"""

import logging
import os
from typing import Optional, Dict, Any

import yaml

from .toi_models import TOIConfig, ToneProfile, Pacing

logger = logging.getLogger(__name__)

_TONE_PROFILE_MAP = {
    "supportive_default": ToneProfile.SUPPORTIVE_DEFAULT,
    "minimal": ToneProfile.MINIMAL,
    "directive": ToneProfile.DIRECTIVE,
    "therapeutic_reflective": ToneProfile.THERAPEUTIC_REFLECTIVE,
}

_PACING_MAP = {
    "standard": Pacing.STANDARD,
    "slow": Pacing.SLOW,
    "very_slow": Pacing.VERY_SLOW,
}


class TOIParser:
    """
    Parses TOI configuration from YAML files or raw dicts.

    Applies the default TOI from toi_defaults.yaml as the baseline,
    then layers user-specific overrides on top.
    """

    def __init__(self, defaults_path: str = "config/toi_defaults.yaml"):
        self.defaults_path = defaults_path
        self._defaults: Optional[Dict[str, Any]] = None

    def _load_defaults(self) -> Dict[str, Any]:
        if self._defaults is not None:
            return self._defaults
        if os.path.exists(self.defaults_path):
            with open(self.defaults_path, "r") as f:
                data = yaml.safe_load(f)
            self._defaults = data.get("default_toi", {})
        else:
            logger.warning(
                "TOI defaults file not found at %s — using hardcoded defaults",
                self.defaults_path,
            )
            self._defaults = {}
        return self._defaults

    def parse_from_dict(self, user_toi: Optional[Dict[str, Any]] = None) -> TOIConfig:
        """
        Parse a TOIConfig from a dict, applying defaults for missing keys.

        Args:
            user_toi: User-supplied TOI overrides. None means use all defaults.

        Returns:
            Validated TOIConfig instance.
        """
        defaults = self._load_defaults()
        merged = {**defaults, **(user_toi or {})}
        return self._build_config(merged)

    def parse_from_yaml(self, yaml_path: str) -> TOIConfig:
        """Parse a TOIConfig from a user-supplied YAML file."""
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        user_toi = data.get("toi", data)
        return self.parse_from_dict(user_toi)

    def _build_config(self, data: Dict[str, Any]) -> TOIConfig:
        tone_raw = data.get("tone_profile", "supportive_default")
        tone = _TONE_PROFILE_MAP.get(tone_raw, ToneProfile.SUPPORTIVE_DEFAULT)
        if tone_raw not in _TONE_PROFILE_MAP:
            logger.warning("Unknown tone_profile '%s' — defaulting to supportive_default", tone_raw)

        pacing_raw = data.get("pacing", "standard")
        pacing = _PACING_MAP.get(pacing_raw, Pacing.STANDARD)
        if pacing_raw not in _PACING_MAP:
            logger.warning("Unknown pacing '%s' — defaulting to standard", pacing_raw)

        scaffolding = int(data.get("cognitive_scaffolding_level", 2))
        scaffolding = max(0, min(3, scaffolding))  # Clamp to 0–3

        return TOIConfig(
            tone_profile=tone,
            pacing=pacing,
            cognitive_scaffolding_level=scaffolding,
            safety_boundaries=list(data.get("safety_boundaries", [])),
            silent_mode_preferred=bool(data.get("silent_mode_preferred", False)),
            allow_timers=bool(data.get("allow_timers", True)),
            allow_task_loops=bool(data.get("allow_task_loops", False)),
            preferred_personas=list(data.get("preferred_personas", [])),
            excluded_personas=list(data.get("excluded_personas", [])),
            max_response_length=data.get("max_response_length"),
            consent_given=bool(data.get("consent_given", False)),
        )

    def default_config(self) -> TOIConfig:
        """Return the system default TOI config with no user overrides."""
        return self.parse_from_dict(None)
