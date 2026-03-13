"""
Persona Base — abstract contract for every Original Guide (OG) persona.

Each persona produces a ``PersonaResponse`` when given a distress context.
The Fusion Engine blends these responses according to dynamic weights.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PersonaResponse:
    """A single persona's contribution to the blended response."""
    persona_id: str
    text: str
    tone_tag: str
    suggested_actions: List[str] = field(default_factory=list)
    visual_cues: Dict[str, Any] = field(default_factory=dict)
    silent_mode: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class Persona(ABC):
    """Abstract base for all 5 OG personas."""

    @property
    @abstractmethod
    def persona_id(self) -> str:
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        ...

    @property
    @abstractmethod
    def core_role(self) -> str:
        ...

    @abstractmethod
    def generate_response(
        self,
        distress_context: Dict[str, Any],
        tone: str = "supportive",
    ) -> PersonaResponse:
        """
        Produce a response for the given distress context.

        Parameters
        ----------
        distress_context :
            Dictionary with at least ``distress_type`` and ``severity``
            keys, plus any extra CDE or dialogue-tree data.
        tone :
            One of the four tone profile identifiers.
        """
        ...
