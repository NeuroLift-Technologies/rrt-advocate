"""
Base class for all Original Guide personas.

Each persona implements `generate()` which returns a context-aware message
given the user's distress context, the requested tone, and a weight.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from src.models import PersonaName, PersonaResponse, ToneProfile


class BasePersona(ABC):
    """Abstract base for the five Original Guides."""

    name: PersonaName

    @abstractmethod
    def generate(
        self,
        context: Dict[str, Any],
        tone: ToneProfile,
        weight: float,
    ) -> PersonaResponse:
        """Produce this persona's contribution to the blended response."""
        ...

    def _make_response(
        self, message: str, tone: ToneProfile, weight: float, **meta: Any
    ) -> PersonaResponse:
        return PersonaResponse(
            persona=self.name,
            weight=weight,
            message=message,
            tone=tone,
            metadata=dict(meta),
        )
