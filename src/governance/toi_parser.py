"""
TOI (Terms of Interaction) Parser
Middleware filter that ingests and enforces user's interaction contract before any crisis response.

NLT Ethos: Agency First. The user's TOI acts as a strict middleware filter.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ToneProfile(str, Enum):
    """Supported tone profiles from user TOI."""
    SUPPORTIVE_DEFAULT = "supportive_default"
    MINIMAL = "minimal"
    DIRECTIVE = "directive"
    THERAPEUTIC_REFLECTIVE = "therapeutic_reflective"


@dataclass
class TOIConfig:
    """
    Parsed and validated TOI configuration.
    All interaction logic must respect these boundaries.
    """

    tone_profile: ToneProfile
    warmth_level: float
    validation_frequency: str
    response_speed: str
    chunk_size: str
    pause_between_messages: float
    breakdown_granularity: str
    explicit_instructions: bool
    offer_alternatives: bool
    avoid_assumptions: bool
    no_forced_productivity: bool
    consent_required_escalation: bool
    silent_mode_available: bool
    max_intervention_intensity: float
    persona_overrides: Dict[str, Optional[float]] = field(default_factory=dict)
    prompt_before_activation: bool = True
    explicit_consent_required: bool = True

    def allows_intervention_intensity(self, intensity: float) -> bool:
        """Check if proposed intervention respects safety boundary."""
        return intensity <= self.max_intervention_intensity

    def requires_consent_before_activation(self) -> bool:
        """Stage 1: Agency-first check."""
        return self.prompt_before_activation and self.explicit_consent_required


class TOIParser:
    """
    Parses and validates TOI configuration from YAML or dict.
    Enforces structure required for OTOI coordination.
    """

    DEFAULT_TOI = {
        "tone": {
            "profile": "supportive_default",
            "warmth_level": 0.8,
            "validation_frequency": "balanced",
        },
        "pacing": {
            "response_speed": "moderate",
            "chunk_size": "medium",
            "pause_between_messages": 1.5,
        },
        "cognitive_scaffolding": {
            "breakdown_granularity": "medium",
            "explicit_instructions": True,
            "offer_alternatives": True,
            "avoid_assumptions": True,
        },
        "safety_boundaries": {
            "no_forced_productivity": True,
            "consent_required_escalation": True,
            "silent_mode_available": True,
            "max_intervention_intensity": 0.8,
        },
        "persona_overrides": {},
        "stage1_entry": {
            "prompt_before_activation": True,
            "explicit_consent_required": True,
        },
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize parser. If config_path provided, load from file.
        Otherwise uses defaults until parse() is called with explicit config.
        """
        self._config_path = config_path
        self._raw: Dict[str, Any] = {}

        if config_path and Path(config_path).exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._raw = yaml.safe_load(f) or {}

    def parse(self, config: Optional[Dict[str, Any]] = None) -> TOIConfig:
        """
        Parse TOI from provided config dict, or from loaded file.
        Merges with defaults for missing keys.
        """
        raw = config if config is not None else self._raw
        if not raw:
            raw = self.DEFAULT_TOI.copy()

        # Deep merge with defaults
        merged = self._deep_merge(self.DEFAULT_TOI.copy(), raw)

        tone = merged.get("tone", {})
        pacing = merged.get("pacing", {})
        scaffolding = merged.get("cognitive_scaffolding", {})
        safety = merged.get("safety_boundaries", {})
        stage1 = merged.get("stage1_entry", {})

        profile_str = tone.get("profile", "supportive_default")
        try:
            tone_profile = ToneProfile(profile_str)
        except ValueError:
            tone_profile = ToneProfile.SUPPORTIVE_DEFAULT

        return TOIConfig(
            tone_profile=tone_profile,
            warmth_level=float(tone.get("warmth_level", 0.8)),
            validation_frequency=str(tone.get("validation_frequency", "balanced")),
            response_speed=str(pacing.get("response_speed", "moderate")),
            chunk_size=str(pacing.get("chunk_size", "medium")),
            pause_between_messages=float(pacing.get("pause_between_messages", 1.5)),
            breakdown_granularity=str(scaffolding.get("breakdown_granularity", "medium")),
            explicit_instructions=bool(scaffolding.get("explicit_instructions", True)),
            offer_alternatives=bool(scaffolding.get("offer_alternatives", True)),
            avoid_assumptions=bool(scaffolding.get("avoid_assumptions", True)),
            no_forced_productivity=bool(safety.get("no_forced_productivity", True)),
            consent_required_escalation=bool(safety.get("consent_required_escalation", True)),
            silent_mode_available=bool(safety.get("silent_mode_available", True)),
            max_intervention_intensity=float(safety.get("max_intervention_intensity", 0.8)),
            persona_overrides=dict(merged.get("persona_overrides", {})),
            prompt_before_activation=bool(stage1.get("prompt_before_activation", True)),
            explicit_consent_required=bool(stage1.get("explicit_consent_required", True)),
        )

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Merge override into base, recursively."""
        result = base.copy()
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = self._deep_merge(result[k], v)
            else:
                result[k] = v
        return result

    def validate_for_response(self, toi: TOIConfig, proposed_action: Dict[str, Any]) -> bool:
        """
        Validate that a proposed crisis response respects TOI.
        Returns True if allowed, False if violates boundaries.

        Anti-gaslight: Variable names and logic reflect non-judgmental stance.
        """
        # No forced productivity when user signals burnout
        if toi.no_forced_productivity and proposed_action.get("forces_task_loop", False):
            return False

        intensity = proposed_action.get("intervention_intensity", 0.0)
        if not toi.allows_intervention_intensity(intensity):
            return False

        return True
