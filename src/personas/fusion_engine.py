"""
Persona Fusion Engine — dynamic weighting algorithm that blends the 5
Original Guide personas based on the flavour of neurodivergent distress.

The engine receives raw weights (0.0–1.0 per persona), applies OTOI
governance caps, normalises, and then asks each permitted persona to
generate a response.  The final ``FusedResponse`` is a weighted
composite that the TOI parser will post-process before delivery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .persona_base import Persona, PersonaResponse
from .ash import Ash
from .sol import Sol
from .echo import Echo
from .kai import Kai
from .myra import Myra


@dataclass
class PersonaWeights:
    """Mutable weight vector for the 5 OG personas (each 0.0–1.0)."""
    ash: float = 0.0
    sol: float = 0.0
    echo: float = 0.0
    kai: float = 0.0
    myra: float = 0.0

    def as_dict(self) -> Dict[str, float]:
        return {
            "ash": self.ash,
            "sol": self.sol,
            "echo": self.echo,
            "kai": self.kai,
            "myra": self.myra,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> "PersonaWeights":
        return cls(
            ash=d.get("ash", 0.0),
            sol=d.get("sol", 0.0),
            echo=d.get("echo", 0.0),
            kai=d.get("kai", 0.0),
            myra=d.get("myra", 0.0),
        )

    def clamp(self) -> None:
        """Clamp all weights into [0.0, 1.0]."""
        for attr in ("ash", "sol", "echo", "kai", "myra"):
            setattr(self, attr, max(0.0, min(1.0, getattr(self, attr))))

    def total(self) -> float:
        return self.ash + self.sol + self.echo + self.kai + self.myra

    def normalised(self) -> Dict[str, float]:
        """Return weight dict normalised so values sum to 1.0 (or all 0)."""
        t = self.total()
        if t == 0:
            return {k: 0.0 for k in self.as_dict()}
        return {k: round(v / t, 4) for k, v in self.as_dict().items()}


@dataclass
class FusedResponse:
    """Final blended output from all active personas."""
    primary_persona: str
    primary_text: str
    persona_contributions: Dict[str, PersonaResponse]
    weights_used: Dict[str, float]
    silent_mode: bool = False
    visual_cues: Dict[str, Any] = field(default_factory=dict)
    all_suggested_actions: List[str] = field(default_factory=list)


class FusionEngine:
    """
    Core engine that instantiates the 5 OG personas and blends their
    outputs based on dynamic weights.
    """

    def __init__(self) -> None:
        self._personas: Dict[str, Persona] = {
            "ash": Ash(),
            "sol": Sol(),
            "echo": Echo(),
            "kai": Kai(),
            "myra": Myra(),
        }

    @property
    def personas(self) -> Dict[str, Persona]:
        return dict(self._personas)

    def fuse(
        self,
        weights: PersonaWeights,
        distress_context: Dict[str, Any],
        tone: str = "supportive",
        otoi_caps: Optional[Dict[str, float]] = None,
    ) -> FusedResponse:
        """
        Run the fusion algorithm.

        1. Clamp raw weights.
        2. Apply OTOI caps (if provided).
        3. Normalise.
        4. Generate responses from every persona with weight > 0.
        5. Select the primary persona (highest weight) and assemble
           the ``FusedResponse``.
        """
        weights.clamp()

        effective = weights.as_dict()
        if otoi_caps:
            for pid, cap in otoi_caps.items():
                if pid in effective:
                    effective[pid] = min(effective[pid], cap)

        total = sum(effective.values())
        if total > 0:
            normalised = {k: round(v / total, 4) for k, v in effective.items()}
        else:
            normalised = {k: 0.0 for k in effective}

        contributions: Dict[str, PersonaResponse] = {}
        for pid, norm_weight in normalised.items():
            if norm_weight > 0 and pid in self._personas:
                resp = self._personas[pid].generate_response(distress_context, tone)
                contributions[pid] = resp

        if not contributions:
            return FusedResponse(
                primary_persona="myra",
                primary_text="",
                persona_contributions={},
                weights_used=normalised,
                silent_mode=True,
                visual_cues=Myra.SILENT_MODE_VISUALS,
            )

        primary_pid = max(normalised, key=lambda k: normalised[k])
        primary_resp = contributions.get(primary_pid)

        silent = any(r.silent_mode for r in contributions.values())
        visuals: Dict[str, Any] = {}
        actions: List[str] = []
        for r in contributions.values():
            if r.visual_cues:
                visuals.update(r.visual_cues)
            actions.extend(r.suggested_actions)

        return FusedResponse(
            primary_persona=primary_pid,
            primary_text=primary_resp.text if primary_resp else "",
            persona_contributions=contributions,
            weights_used=normalised,
            silent_mode=silent,
            visual_cues=visuals,
            all_suggested_actions=list(dict.fromkeys(actions)),
        )
