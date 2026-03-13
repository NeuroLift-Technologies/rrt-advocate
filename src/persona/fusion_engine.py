"""
Persona Fusion Engine
Dynamically blends the 5 OGs (Ash, Sol, Echo, Kai, Myra) based on distress flavor.

Replaces generic severity responder with distress-type-weighted persona selection.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import yaml

from governance.otoi_coordinator import PersonaBlend


# Stage 2 distress assessment input → config key mapping
DISTRESS_INPUT_MAP = {
    "everything hurts": "meltdown",
    "meltdown": "meltdown",
    "everything hurts / meltdown": "meltdown",
    "can't do basic tasks": "executive_dysfunction",
    "can't do basic task": "executive_dysfunction",
    "executive dysfunction": "executive_dysfunction",
    "can't stop self-blame": "negative_self_talk",
    "self-blame": "negative_self_talk",
    "negative self-talk": "negative_self_talk",
    "stuck in hyperfocus": "hyperfocus_stuck",
    "stuck in loop": "hyperfocus_stuck",
    "hyperfocus": "hyperfocus_stuck",
    "loop": "hyperfocus_stuck",
    "don't know": "shutdown",
    "shut down": "shutdown",
    "shutdown": "shutdown",
    "don't know / shut down": "shutdown",
}


@dataclass
class PersonaWeights:
    """Raw persona weights before normalization."""
    ash: float
    sol: float
    echo: float
    kai: float
    myra: float

    def to_dict(self) -> Dict[str, float]:
        return {"ash": self.ash, "sol": self.sol, "echo": self.echo, "kai": self.kai, "myra": self.myra}

    def normalize(self) -> Dict[str, float]:
        """Normalize so weights sum to 1.0."""
        d = self.to_dict()
        total = sum(d.values())
        if total <= 0:
            return {"ash": 0.2, "sol": 0.2, "echo": 0.2, "kai": 0.2, "myra": 0.2}
        return {k: v / total for k, v in d.items()}


class PersonaFusionEngine:
    """
    Translates Stage 2 distress input into persona blend.
    Uses persona_weights.yaml for mapping.
    """

    DEFAULT_WEIGHTS = {
        "meltdown": {"ash": 0.45, "sol": 0.05, "echo": 0.10, "kai": 0.05, "myra": 0.35},
        "executive_dysfunction": {"ash": 0.15, "sol": 0.55, "echo": 0.10, "kai": 0.10, "myra": 0.10},
        "negative_self_talk": {"ash": 0.20, "sol": 0.05, "echo": 0.55, "kai": 0.05, "myra": 0.15},
        "hyperfocus_stuck": {"ash": 0.05, "sol": 0.20, "echo": 0.10, "kai": 0.55, "myra": 0.10},
        "shutdown": {"ash": 0.10, "sol": 0.05, "echo": 0.05, "kai": 0.05, "myra": 0.75},
    }

    def __init__(self, config_path: Optional[str] = None):
        config_path = config_path or "config/persona_weights.yaml"
        self._weights_config: Dict = {}

        if Path(config_path).exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self._weights_config = data.get("distress_inputs", self.DEFAULT_WEIGHTS)
        else:
            self._weights_config = self.DEFAULT_WEIGHTS

    def _normalize_input(self, raw: str) -> str:
        """Normalize user input for matching."""
        return raw.lower().strip()

    def _map_to_config_key(self, user_input: str) -> str:
        """Map Stage 2 distress input to config key."""
        normalized = self._normalize_input(user_input)

        # Exact or partial match
        for phrase, key in DISTRESS_INPUT_MAP.items():
            if phrase in normalized or normalized in phrase:
                return key

        # Fallback: try direct key match
        if normalized.replace(" ", "_") in self._weights_config:
            return normalized.replace(" ", "_")

        # Default to shutdown (most gentle, Myra-heavy)
        return "shutdown"

    def compute_blend(self, distress_input: str) -> PersonaBlend:
        """
        Compute persona blend from Stage 2 distress assessment input.

        Input mapping (from briefing):
        - "Everything hurts / Meltdown" → Ash + Myra
        - "Can't do basic tasks" → Sol
        - "Can't stop self-blame" → Echo
        - "Stuck in hyperfocus/loop" → Kai
        - "Don't know / Shut down" → Myra (Silent Mode)
        """
        key = self._map_to_config_key(distress_input)
        raw_weights = self._weights_config.get(key, self.DEFAULT_WEIGHTS["shutdown"])

        # Ensure all 5 personas present
        defaults = {"ash": 0.2, "sol": 0.2, "echo": 0.2, "kai": 0.2, "myra": 0.2}
        for p in defaults:
            if p not in raw_weights:
                raw_weights[p] = defaults[p]

        total = sum(raw_weights.values())
        weights = {k: v / total for k, v in raw_weights.items()} if total > 0 else defaults

        sorted_p = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_p[0][0]
        secondary = [p for p, _ in sorted_p[1:3]]

        # Silent Mode: Myra-dominant + shutdown/meltdown
        silent_mode = key in ("shutdown", "meltdown") and weights.get("myra", 0) >= 0.5

        return PersonaBlend(
            weights=weights,
            primary_persona=primary,
            secondary_personas=secondary,
            silent_mode=silent_mode,
        )
