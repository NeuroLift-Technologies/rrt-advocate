"""
Governance Middleware — the single entry-point that wraps every RRT interaction.

Flow:
  1. Ingest the user's TOI (or fall back to defaults).
  2. Feed persona contributions through the OTOI coordinator.
  3. Return a FusedResponse that strictly conforms to the user's contract.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.models import (
    FusedResponse,
    PersonaResponse,
    PersonaWeights,
    TOIConfig,
    ToneProfile,
)
from src.toi.otoi_coordinator import OTOICoordinator
from src.toi.toi_parser import TOIParser

logger = logging.getLogger(__name__)


class GovernanceMiddleware:
    """Strict TOI-OTOI governance wrapper for the RRT AIdvocAIte."""

    def __init__(self, toi_data: Optional[Dict[str, Any]] = None):
        parser = TOIParser.from_dict(toi_data or {})
        self._toi = parser.parse()
        self._coordinator = OTOICoordinator(self._toi)

    @classmethod
    def from_yaml(cls, path: str) -> "GovernanceMiddleware":
        parser = TOIParser.from_yaml(path)
        toi = parser.parse()
        instance = cls.__new__(cls)
        instance._toi = toi
        instance._coordinator = OTOICoordinator(toi)
        return instance

    @property
    def toi(self) -> TOIConfig:
        return self._toi

    def update_toi(self, toi_data: Dict[str, Any]) -> None:
        """Hot-reload the user's TOI at runtime."""
        parser = TOIParser.from_dict(toi_data)
        self._toi = parser.parse()
        self._coordinator = OTOICoordinator(self._toi)
        logger.info("TOI updated at runtime — tone=%s", self._toi.tone.value)

    def process(
        self,
        contributions: List[PersonaResponse],
        weights: PersonaWeights,
        silent_mode: bool = False,
    ) -> FusedResponse:
        """
        Run the full governance pipeline on a set of persona contributions.

        This is the only public method that downstream code should call
        to produce user-facing output.
        """
        return self._coordinator.enforce(
            contributions=contributions,
            weights=weights,
            silent_mode=silent_mode,
        )
