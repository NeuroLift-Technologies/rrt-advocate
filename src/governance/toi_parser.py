"""
TOI Parser - Terms of Interaction Configuration Ingestion
RRT Advocate - Protective Layer of the Solidarity Framework

Ingests and validates user TOI configurations that dictate:
- Tone, Pacing, Cognitive Scaffolding, Safety Boundaries
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import yaml

logger = logging.getLogger(__name__)


class TonePreference(Enum):
    """User's preferred interaction tone"""
    SUPPORTIVE_DEFAULT = "supportive_default"  # Warm, validating
    MINIMAL = "minimal"  # Extremely concise, lowest cognitive load
    DIRECTIVE = "directive"  # Clear, action-oriented
    THERAPEUTIC_REFLECTIVE = "therapeutic_reflective"  # Empathetic mirroring, Socratic


class PacingLevel(Enum):
    """Interaction pacing preference"""
    SLOW = "slow"
    MODERATE = "moderate"
    ADAPTIVE = "adaptive"


@dataclass
class SafetyBoundaries:
    """User-defined safety boundaries from TOI"""
    no_productivity_pressure: bool = True  # Anti-gaslight: no forced task loops
    consent_required_before_intervention: bool = True  # Agency First
    silent_mode_available: bool = True  # Myra: calm visuals, no timers
    max_message_length: Optional[int] = None
    escalation_consent_required: bool = True


@dataclass
class CognitiveScaffolding:
    """Cognitive load management from TOI"""
    prefer_bullet_points: bool = True
    prefer_short_sentences: bool = True
    break_down_complex_tasks: bool = True
    avoid_multi_part_questions: bool = True


@dataclass
class TOIConfig:
    """
    Parsed and validated Terms of Interaction configuration.
    Acts as the user's explicit interaction contract.
    """
    tone: TonePreference = TonePreference.SUPPORTIVE_DEFAULT
    pacing: PacingLevel = PacingLevel.MODERATE
    safety: SafetyBoundaries = field(default_factory=SafetyBoundaries)
    cognitive: CognitiveScaffolding = field(default_factory=CognitiveScaffolding)
    allowed_personas: Optional[List[str]] = None  # None = all allowed
    raw_config: Dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass
class ValidationResult:
    """Result of TOI config validation"""
    valid: bool
    config: Optional[TOIConfig] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class TOIParser:
    """
    Parses and validates user TOI configuration.
    Non-judgmental error handling (anti-gaslight / shame-resistant design).
    """

    VALID_TONES = {t.value for t in TonePreference}
    VALID_PACING = {p.value for p in PacingLevel}
    VALID_PERSONAS = {"ash", "sol", "echo", "kai", "myra"}

    def __init__(self, schema_path: Optional[str] = None):
        self.schema_path = schema_path

    def parse(self, config_source: Union[Dict[str, Any], str]) -> ValidationResult:
        """
        Parse TOI configuration from dict or YAML file path.

        Args:
            config_source: Dict or path to YAML file

        Returns:
            ValidationResult with parsed TOIConfig or error details
        """
        errors: List[str] = []
        warnings: List[str] = []

        try:
            if isinstance(config_source, str):
                with open(config_source, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f)
            else:
                raw = config_source

            if not raw:
                return ValidationResult(valid=False, errors=["Configuration was empty"])

            # Normalize nested schema (tone: {profile: "..."}) to flat (tone: "...")
            tone_raw = raw.get("tone", "supportive_default")
            tone_str = tone_raw.get("profile", tone_raw) if isinstance(tone_raw, dict) else tone_raw
            pacing_raw = raw.get("pacing", "moderate")
            pacing_str = pacing_raw.get("response_speed", pacing_raw) if isinstance(pacing_raw, dict) else pacing_raw
            safety_raw = raw.get("safety_boundaries", raw.get("safety", {}))
            cognitive_raw = raw.get("cognitive_scaffolding", raw.get("cognitive", {}))

            # Parse tone
            if isinstance(tone_str, str):
                tone_str = tone_str.lower().replace(" ", "_")
            if tone_str in self.VALID_TONES:
                tone = TonePreference(tone_str)
            else:
                errors.append(f"Unknown tone '{tone_str}'; valid: {list(self.VALID_TONES)}")

            # Parse pacing
            if isinstance(pacing_str, str):
                pacing_str = pacing_str.lower()
            # Map schema values to PacingLevel
            pacing_map = {"immediate": "moderate", "patient": "moderate", "relaxed": "slow", "brief": "moderate", "medium": "moderate", "extended": "adaptive"}
            pacing_str = pacing_map.get(pacing_str, pacing_str)
            if pacing_str in self.VALID_PACING:
                pacing = PacingLevel(pacing_str)
            else:
                errors.append(f"Unknown pacing '{pacing_str}'; valid: {list(self.VALID_PACING)}")

            # Parse safety boundaries (support both flat and schema key names)
            safety_raw = raw.get("safety_boundaries", raw.get("safety", {}))
            if isinstance(safety_raw, dict):
                safety = SafetyBoundaries(
                    no_productivity_pressure=safety_raw.get("no_productivity_pressure", safety_raw.get("no_forced_productivity", True)),
                    consent_required_before_intervention=safety_raw.get(
                        "consent_required_before_intervention", safety_raw.get("consent_required", True)
                    ),
                    silent_mode_available=safety_raw.get("silent_mode_available", True),
                    max_message_length=safety_raw.get("max_message_length"),
                    escalation_consent_required=safety_raw.get("escalation_consent_required", safety_raw.get("escalation_opt_in", True)),
                )
            else:
                safety = SafetyBoundaries()

            # Parse cognitive scaffolding
            cognitive_raw = raw.get("cognitive_scaffolding", {})
            if isinstance(cognitive_raw, dict):
                cognitive = CognitiveScaffolding(
                    prefer_bullet_points=cognitive_raw.get("prefer_bullet_points", True),
                    prefer_short_sentences=cognitive_raw.get("prefer_short_sentences", True),
                    break_down_complex_tasks=cognitive_raw.get("break_down_complex_tasks", True),
                    avoid_multi_part_questions=cognitive_raw.get("avoid_multi_part_questions", True),
                )
            else:
                cognitive = CognitiveScaffolding()

            # Parse allowed personas
            allowed = raw.get("allowed_personas")
            if allowed is not None:
                if isinstance(allowed, list):
                    normalized = [p.lower() for p in allowed if isinstance(p, str)]
                    invalid = [p for p in normalized if p not in self.VALID_PERSONAS]
                    if invalid:
                        warnings.append(f"Unknown personas skipped: {invalid}")
                    allowed = [p for p in normalized if p in self.VALID_PERSONAS] or None
                else:
                    allowed = None

            if errors:
                return ValidationResult(valid=False, errors=errors)

            config = TOIConfig(
                tone=tone,
                pacing=pacing,
                safety=safety,
                cognitive=cognitive,
                allowed_personas=allowed,
                raw_config=raw,
            )
            return ValidationResult(valid=True, config=config, warnings=warnings)

        except FileNotFoundError as e:
            return ValidationResult(valid=False, errors=[f"Config file not found: {e}"])
        except yaml.YAMLError as e:
            return ValidationResult(valid=False, errors=[f"Invalid YAML: {e}"])
        except Exception as e:
            logger.exception("Unexpected error parsing TOI")
            return ValidationResult(valid=False, errors=[f"Parse error: {str(e)}"])

    def get_default_config(self) -> TOIConfig:
        """Return safe default TOI configuration (agency-first, supportive)."""
        return TOIConfig()
