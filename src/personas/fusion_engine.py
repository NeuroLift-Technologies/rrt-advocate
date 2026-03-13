"""
Persona Fusion Engine - Dynamic Weighting Algorithm

Blends the 5 OGs (Ash, Sol, Echo, Kai, Myra) using modular weights (0.0–1.0)
based on the specific flavor of neurodivergent distress.
Replaces generic severity responder with persona-aware response.
"""

from typing import Dict, Optional
from dataclasses import dataclass

from .persona_definitions import PersonaID, Persona, PERSONAE, get_persona
from .distress_mapper import PersonaWeights, DistressMapper


@dataclass
class FusionResult:
    """Result of persona fusion: dominant persona + blend description."""
    weights: PersonaWeights
    dominant_persona: PersonaID
    silent_mode: bool
    blend_description: str


class PersonaFusionEngine:
    """
    Computes persona blend from distress input and optional CDE signals.
    Local-first: no external calls.
    """

    def __init__(self, distress_mapper: Optional[DistressMapper] = None):
        self.distress_mapper = distress_mapper or DistressMapper()

    def get_default_weights(self) -> Dict[str, float]:
        """Balanced default when no distress input; used as fallback."""
        return PersonaWeights(ash=0.2, sol=0.2, echo=0.2, kai=0.2, myra=0.2).to_dict()

    def fuse(
        self,
        stage2_input: Optional[str] = None,
        force_silent_mode: bool = False,
        cde_supplement: Optional[Dict[str, float]] = None,
    ) -> FusionResult:
        """
        Compute persona weights from Stage 2 input and optional CDE data.
        CDE supplement can adjust weights (e.g. higher Echo if negative self-talk detected).
        """
        if force_silent_mode:
            weights = self.distress_mapper.get_silent_mode_weights()
            return FusionResult(
                weights=weights,
                dominant_persona=PersonaID.MYRA,
                silent_mode=True,
                blend_description="Silent Mode: calm, low-demand, Myra-led presence.",
            )

        if stage2_input:
            weights = self.distress_mapper.map_input(stage2_input)
        else:
            weights = PersonaWeights(ash=0.2, sol=0.2, echo=0.2, kai=0.2, myra=0.2)

        # Optional CDE supplement: blend with additional signals
        if cde_supplement:
            weights = self._blend_with_cde(weights, cde_supplement)

        # Normalize to sum ~1.0
        weights = self._normalize(weights)

        dominant = self._dominant_persona(weights)
        silent_mode = weights.myra >= 0.7 and not stage2_input or "shut" in (stage2_input or "").lower()

        blend_desc = self._describe_blend(weights, dominant)
        return FusionResult(
            weights=weights,
            dominant_persona=dominant,
            silent_mode=silent_mode,
            blend_description=blend_desc,
        )

    def _blend_with_cde(
        self, base: PersonaWeights, cde: Dict[str, float]
    ) -> PersonaWeights:
        """Blend base weights with CDE-derived adjustments."""
        d = base.to_dict()
        # CDE keys: e.g. negative_self_talk -> echo, overwhelm -> ash, task_avoidance -> sol
        mapping = {
            "negative_self_talk": "echo",
            "overwhelm": "ash",
            "task_avoidance": "sol",
            "hyperfocus_loop": "kai",
            "withdrawal": "myra",
        }
        for cde_key, persona_key in mapping.items():
            adj = cde.get(cde_key, 0.0)
            d[persona_key] = min(1.0, d[persona_key] + adj * 0.2)
        return PersonaWeights.from_dict(d)

    def _normalize(self, w: PersonaWeights) -> PersonaWeights:
        total = w.ash + w.sol + w.echo + w.kai + w.myra
        if total <= 0:
            return PersonaWeights(0.2, 0.2, 0.2, 0.2, 0.2)
        return PersonaWeights(
            ash=w.ash / total,
            sol=w.sol / total,
            echo=w.echo / total,
            kai=w.kai / total,
            myra=w.myra / total,
        )

    def _dominant_persona(self, w: PersonaWeights) -> PersonaID:
        d = w.to_dict()
        return PersonaID(max(d, key=d.get))

    def _describe_blend(self, w: PersonaWeights, dominant: PersonaID) -> str:
        persona = get_persona(dominant)
        parts = [f"Primary: {persona.name} ({persona.role})"]
        secondary = [
            (PersonaID.ASH, w.ash),
            (PersonaID.SOL, w.sol),
            (PersonaID.ECHO, w.echo),
            (PersonaID.KAI, w.kai),
            (PersonaID.MYRA, w.myra),
        ]
        secondary.sort(key=lambda x: -x[1])
        for pid, weight in secondary[1:3]:
            if weight >= 0.15:
                p = get_persona(pid)
                parts.append(f"Support: {p.name} ({weight:.0%})")
        return "; ".join(parts)
