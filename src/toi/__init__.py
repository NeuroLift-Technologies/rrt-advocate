"""
TOI/OTOI Governance Layer — Solidarity Framework Constitutional Layer

Terms of Interaction (TOI): The user's personal interaction contract.
Orchestrated TOI (OTOI): The middleware that enforces TOI across all personas.
"""
from .toi_models import (
    ToneProfile,
    Pacing,
    TOIConfig,
    OTOIState,
)
from .toi_parser import TOIParser
from .otoi_middleware import OTOIMiddleware

__all__ = [
    "ToneProfile",
    "Pacing",
    "TOIConfig",
    "OTOIState",
    "TOIParser",
    "OTOIMiddleware",
]
