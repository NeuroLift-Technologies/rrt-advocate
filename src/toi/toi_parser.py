"""TOI Parser — ingests a user's TOI configuration from YAML/dict and validates it."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .models import (
    CognitiveScaffolding,
    PacingMode,
    SafetyBoundaries,
    TOIConfig,
    ToneProfile,
)

logger = logging.getLogger(__name__)


class TOIParser:
    """
    Parses and validates a user's Terms of Interaction configuration.

    Supports loading from a YAML file, a raw dict, or individual keyword
    arguments.  Missing keys fall back to sensible, non-judgmental defaults.
    """

    def __init__(self, schema_path: str | Path | None = None) -> None:
        self._schema_path = Path(schema_path) if schema_path else None

    def from_yaml(self, path: str | Path) -> TOIConfig:
        """Load TOI from a YAML file."""
        yaml_path = Path(path)
        if not yaml_path.exists():
            logger.warning(
                "TOI config file not found at %s — using sensible defaults.",
                yaml_path,
            )
            return self._default_config(user_id="unknown")

        with yaml_path.open("r", encoding="utf-8") as fh:
            raw: dict[str, Any] = yaml.safe_load(fh) or {}

        return self.from_dict(raw)

    def from_dict(self, raw: dict[str, Any]) -> TOIConfig:
        """Parse TOI from a Python dict (e.g. after JSON deserialization)."""
        user_id = str(raw.get("user_id", "anonymous"))

        tone_raw = raw.get("tone_profile", ToneProfile.SUPPORTIVE_DEFAULT)
        try:
            tone = ToneProfile(tone_raw)
        except ValueError:
            logger.warning("Unrecognised tone_profile '%s' — defaulting to supportive.", tone_raw)
            tone = ToneProfile.SUPPORTIVE_DEFAULT

        pacing_raw = raw.get("pacing", PacingMode.STANDARD)
        try:
            pacing = PacingMode(pacing_raw)
        except ValueError:
            logger.warning("Unrecognised pacing '%s' — defaulting to standard.", pacing_raw)
            pacing = PacingMode.STANDARD

        scaffolding_raw = raw.get("cognitive_scaffolding", {})
        scaffolding = CognitiveScaffolding(
            chunking_enabled=scaffolding_raw.get("chunking_enabled", True),
            visual_anchors=scaffolding_raw.get("visual_anchors", False),
            working_memory_offload=scaffolding_raw.get("working_memory_offload", True),
            no_open_loops=scaffolding_raw.get("no_open_loops", True),
        )

        safety_raw = raw.get("safety_boundaries", {})
        safety = SafetyBoundaries(
            no_productivity_pressure=safety_raw.get("no_productivity_pressure", True),
            require_explicit_consent=safety_raw.get("require_explicit_consent", True),
            emergency_contact_threshold=float(
                safety_raw.get("emergency_contact_threshold", 0.1)
            ),
            external_resource_threshold=float(
                safety_raw.get("external_resource_threshold", 0.2)
            ),
            silent_mode_eligible=safety_raw.get("silent_mode_eligible", True),
        )

        return TOIConfig(
            user_id=user_id,
            tone_profile=tone,
            pacing=pacing,
            cognitive_scaffolding=scaffolding,
            safety_boundaries=safety,
            persona_mute_list=list(raw.get("persona_mute_list", [])),
            preferred_personas=list(raw.get("preferred_personas", [])),
            last_updated=str(raw.get("last_updated", "")),
            raw_config=raw,
        )

    def _default_config(self, user_id: str) -> TOIConfig:
        return TOIConfig(user_id=user_id)

    def validate(self, config: TOIConfig) -> list[str]:
        """
        Validate a parsed TOIConfig.  Returns a list of human-readable
        concern messages (not errors — never shame the user's choices).
        """
        concerns: list[str] = []

        if config.safety_boundaries.emergency_contact_threshold > 0.3:
            concerns.append(
                "emergency_contact_threshold is set higher than 0.3 — "
                "this may delay reaching safety resources."
            )
        if config.safety_boundaries.external_resource_threshold > 0.5:
            concerns.append(
                "external_resource_threshold is set above 0.5 — "
                "consider whether earlier referrals would feel supportive."
            )

        all_personas = {"ASH", "SOL", "ECHO", "KAI", "MYRA"}
        muted = {p.upper() for p in config.persona_mute_list}
        if muted == all_personas:
            concerns.append(
                "All five personas are muted — the system will have no voice to respond with."
            )

        return concerns
