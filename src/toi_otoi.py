"""TOI/OTOI governance primitives for the RRT Advocate."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


SUPPORTED_TONE_PROFILES = {
    "supportive_default",
    "minimal",
    "directive",
    "therapeutic_reflective",
}

SUPPORTED_PERSONAS = {"ash", "sol", "echo", "kai", "myra"}


@dataclass(frozen=True)
class TOIConfig:
    """User Terms of Interaction configuration."""

    tone_profile: str = "supportive_default"
    pacing: str = "steady"
    cognitive_scaffolding: str = "moderate"
    safety_boundaries: List[str] = field(default_factory=list)
    allowed_personas: Optional[List[str]] = None
    max_personas_per_turn: int = 2


class TOIParser:
    """Strict TOI parser that validates user interaction contract values."""

    def parse(self, payload: Dict[str, object]) -> TOIConfig:
        tone_profile = str(payload.get("tone_profile", "supportive_default")).lower()
        if tone_profile not in SUPPORTED_TONE_PROFILES:
            tone_profile = "supportive_default"

        pacing = str(payload.get("pacing", "steady")).lower()
        scaffolding = str(payload.get("cognitive_scaffolding", "moderate")).lower()

        boundaries = payload.get("safety_boundaries", [])
        if not isinstance(boundaries, list):
            boundaries = []
        boundaries = [str(item).strip() for item in boundaries if str(item).strip()]

        allowed = payload.get("allowed_personas")
        normalized_allowed: Optional[List[str]] = None
        if isinstance(allowed, list):
            filtered = [
                str(persona).strip().lower()
                for persona in allowed
                if str(persona).strip().lower() in SUPPORTED_PERSONAS
            ]
            normalized_allowed = filtered or None

        max_personas = payload.get("max_personas_per_turn", 2)
        try:
            max_personas = int(max_personas)
        except (TypeError, ValueError):
            max_personas = 2
        max_personas = min(5, max(1, max_personas))

        return TOIConfig(
            tone_profile=tone_profile,
            pacing=pacing,
            cognitive_scaffolding=scaffolding,
            safety_boundaries=boundaries,
            allowed_personas=normalized_allowed,
            max_personas_per_turn=max_personas,
        )


class OTOICoordinator:
    """
    Coordinates persona turn-taking according to TOI constraints.

    OTOI behavior here is deterministic and transparent:
    1) Filter personas by TOI allowed list.
    2) Rank by fusion weight.
    3) Cap speaking personas by max_personas_per_turn.
    """

    def choose_personas(
        self,
        weights: Dict[str, float],
        toi: TOIConfig,
    ) -> List[str]:
        allowed = set(toi.allowed_personas or list(weights.keys()))
        filtered = {name: score for name, score in weights.items() if name in allowed}

        if not filtered:
            # Preserve agency by refusing to speak outside allowed personas.
            return []

        ranked = sorted(filtered.items(), key=lambda item: item[1], reverse=True)
        selected = [name for name, _ in ranked[: toi.max_personas_per_turn]]
        return selected
