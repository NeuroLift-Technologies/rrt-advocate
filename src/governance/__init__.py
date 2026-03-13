"""
TOI-OTOI Governance Layer - RRT Advocate Protective Layer
Solidarity Framework - Human-AI ElevAItion Foundation (HAIEF)

This module provides the Terms of Interaction (TOI) and Orchestrated TOI (OTOI)
governance wrapper that acts as strict middleware before any crisis response.
"""

from .toi_parser import TOIParser, TOIConfig, ValidationResult
from .toi_middleware import TOIMiddleware, InteractionContext
from .otoi_coordinator import OTOICoordinator

__all__ = [
    "TOIParser",
    "TOIConfig",
    "ValidationResult",
    "TOIMiddleware",
    "InteractionContext",
    "OTOICoordinator",
]
