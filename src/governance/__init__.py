"""
TOI-OTOI Governance Layer
RRT AIdvocAIte - Solidarity Framework Protective Layer

This module implements the Terms of Interaction (TOI) parser and
Orchestrated TOI (OTOI) coordinator that wraps all RRT interactions.
"""

from .toi_parser import TOIParser, TOIConfig
from .otoi_coordinator import OTOICoordinator

__all__ = ["TOIParser", "TOIConfig", "OTOICoordinator"]
