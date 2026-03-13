"""Data models for the TOI-OTOI Constitutional Layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToneProfile(str, Enum):
    """Four supported tone profiles a user may declare in their TOI."""

    SUPPORTIVE_DEFAULT = "supportive_default"
    """Warm, validating — the baseline interaction mode."""

    MINIMAL = "minimal"
    """Extremely concise; lowest possible cognitive load."""

    DIRECTIVE = "directive"
    """Clear, action-oriented — ideal for Sol/Kai activation."""

    THERAPEUTIC_REFLECTIVE = "therapeutic_reflective"
    """Empathetic mirroring with soft Socratic questioning — ideal for Ash/Echo."""


class PacingMode(str, Enum):
    SLOW = "slow"
    """Long pauses, minimal prompts, no urgency signals."""

    STANDARD = "standard"
    """Balanced pacing with gentle check-ins."""

    RESPONSIVE = "responsive"
    """Rapid follow-through when the user is in a high-agency moment."""


@dataclass
class CognitiveScaffolding:
    """Controls how much structural support is wrapped around responses."""

    chunking_enabled: bool = True
    """Break multi-step instructions into numbered micro-chunks."""

    visual_anchors: bool = False
    """Include simple emoji anchors as spatial markers in text."""

    working_memory_offload: bool = True
    """Repeat the user's stated goal back before offering next steps."""

    no_open_loops: bool = True
    """Never end a message with an unresolved question during distress."""


@dataclass
class SafetyBoundaries:
    """Hard limits that the OTOI layer enforces — never overridden by personas."""

    no_productivity_pressure: bool = True
    """System must never push task completion when burnout is detected."""

    require_explicit_consent: bool = True
    """Full RRT activation always needs a user opt-in signal."""

    emergency_contact_threshold: float = 0.1
    """Minimum user_safety_score before emergency contacts are considered."""

    external_resource_threshold: float = 0.2
    """Minimum safety score before suggesting external crisis lines."""

    silent_mode_eligible: bool = True
    """Whether the user may enter Silent Mode (no text, calm visuals only)."""


@dataclass
class TOIConfig:
    """A user's Terms of Interaction — the interaction contract that governs every response."""

    user_id: str
    tone_profile: ToneProfile = ToneProfile.SUPPORTIVE_DEFAULT
    pacing: PacingMode = PacingMode.STANDARD
    cognitive_scaffolding: CognitiveScaffolding = field(default_factory=CognitiveScaffolding)
    safety_boundaries: SafetyBoundaries = field(default_factory=SafetyBoundaries)

    persona_mute_list: list[str] = field(default_factory=list)
    """Personas the user has explicitly asked not to hear from."""

    preferred_personas: list[str] = field(default_factory=list)
    """Personas the user has expressed affinity for — slight weight boost."""

    last_updated: str = ""
    raw_config: dict[str, Any] = field(default_factory=dict)

    def is_persona_allowed(self, persona_name: str) -> bool:
        return persona_name.upper() not in [p.upper() for p in self.persona_mute_list]


@dataclass
class OTOIDirective:
    """
    A runtime instruction produced by the OTOICoordinator that specifies
    which personas may speak, in what order, and with what constraints.
    """

    permitted_personas: list[str]
    lead_persona: str
    max_personas_per_response: int = 2
    tone_override: ToneProfile | None = None
    scaffolding_override: CognitiveScaffolding | None = None
    silence_requested: bool = False
    consent_checkpoint_required: bool = False


@dataclass
class InteractionContract:
    """
    The combined runtime object: a user's TOI bound to the current
    session state.  Passed through every layer of the system.
    """

    toi: TOIConfig
    session_id: str
    active_directive: OTOIDirective | None = None
    consent_granted: bool = False
    silent_mode_active: bool = False
