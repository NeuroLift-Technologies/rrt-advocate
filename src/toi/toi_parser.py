"""
TOI Parser — ingests and validates a user's Terms of Interaction configuration.

The TOI dictates Tone, Pacing, Cognitive Scaffolding, and Safety Boundaries.
Every RRT response must pass through this parser before reaching the user.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import yaml

from src.models import PersonaWeights, TOIConfig, ToneProfile

logger = logging.getLogger(__name__)

_TONE_MAP = {
    "supportive": ToneProfile.SUPPORTIVE,
    "minimal": ToneProfile.MINIMAL,
    "directive": ToneProfile.DIRECTIVE,
    "therapeutic": ToneProfile.THERAPEUTIC,
}


class TOIParser:
    """Parse and manage a user's Terms of Interaction."""

    def __init__(self, toi_data: Optional[Dict[str, Any]] = None):
        self._raw = toi_data or {}
        self._config: Optional[TOIConfig] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: str) -> "TOIParser":
        with open(path, "r") as fh:
            data = yaml.safe_load(fh) or {}
        return cls(toi_data=data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TOIParser":
        return cls(toi_data=data)

    def parse(self) -> TOIConfig:
        """Parse raw TOI data into a validated TOIConfig."""
        tone = _TONE_MAP.get(
            str(self._raw.get("tone", "supportive")).lower(),
            ToneProfile.SUPPORTIVE,
        )

        pacing = str(self._raw.get("pacing", "adaptive")).lower()
        if pacing not in ("adaptive", "slow", "fast"):
            pacing = "adaptive"

        scaffolding = bool(self._raw.get("cognitive_scaffolding", True))

        boundaries = self._parse_safety_boundaries(
            self._raw.get("safety_boundaries", {})
        )

        overrides = self._parse_persona_overrides(
            self._raw.get("persona_overrides")
        )

        self._config = TOIConfig(
            tone=tone,
            pacing=pacing,
            cognitive_scaffolding=scaffolding,
            safety_boundaries=boundaries,
            persona_overrides=overrides,
        )
        logger.info("TOI parsed — tone=%s pacing=%s", tone.value, pacing)
        return self._config

    @property
    def config(self) -> TOIConfig:
        if self._config is None:
            return self.parse()
        return self._config

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_safety_boundaries(raw: Any) -> Dict[str, Any]:
        defaults: Dict[str, Any] = {
            "allow_external_escalation": True,
            "allow_emergency_contacts": True,
            "silent_mode_available": True,
            "max_prompt_length": "medium",
        }
        if not isinstance(raw, dict):
            return defaults
        for key in defaults:
            if key in raw:
                defaults[key] = raw[key]
        return defaults

    @staticmethod
    def _parse_persona_overrides(raw: Any) -> Optional[PersonaWeights]:
        if raw is None or not isinstance(raw, dict):
            return None
        try:
            pw = PersonaWeights(
                ash=float(raw.get("ash", 0.2)),
                sol=float(raw.get("sol", 0.2)),
                echo=float(raw.get("echo", 0.2)),
                kai=float(raw.get("kai", 0.2)),
                myra=float(raw.get("myra", 0.2)),
            )
            pw.validate()
            return pw
        except (ValueError, TypeError) as exc:
            logger.warning("Invalid persona overrides, ignoring: %s", exc)
            return None
