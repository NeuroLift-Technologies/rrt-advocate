"""
Persona Layer — The 5 OGs (Original Guides)
RRT AIdvocAIte — Protective Layer of the Solidarity Framework

The five personas are dynamically blended via the FusionEngine based on
the specific flavor of neurodivergent distress, not just raw severity.
"""
from .base_persona import BasePersona, PersonaContribution
from .ash import AshPersona
from .sol import SolPersona
from .echo import EchoPersona
from .kai import KaiPersona
from .myra import MyraPersona
from .fusion_engine import (
    PersonaWeights,
    DistressInput,
    DISTRESS_WEIGHT_MAP,
    FusionEngine,
    BlendedResponse,
    EngineContext,
)

__all__ = [
    "BasePersona",
    "PersonaContribution",
    "AshPersona",
    "SolPersona",
    "EchoPersona",
    "KaiPersona",
    "MyraPersona",
    "PersonaWeights",
    "DistressInput",
    "DISTRESS_WEIGHT_MAP",
    "FusionEngine",
    "BlendedResponse",
    "EngineContext",
]
