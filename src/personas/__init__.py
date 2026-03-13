"""
Persona Fusion Engine - 5 Original Guides (OGs)

The RRT Advocate dynamically blends Ash, Sol, Echo, Kai, and Myra
based on neurodivergent distress flavor rather than raw severity.
"""

from .persona_definitions import Persona, PersonaID
from .fusion_engine import PersonaFusionEngine
from .distress_mapper import DistressMapper

__all__ = [
    "Persona",
    "PersonaID",
    "PersonaFusionEngine",
    "DistressMapper",
]
