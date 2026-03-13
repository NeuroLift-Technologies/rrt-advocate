"""Tiered Activation Dialogue Tree — agency-first crisis interaction flow."""
from .dialogue_tree import DialogueTree, ActivationStage, StageInput
from .stage_handlers import StageHandlers
from .consent_manager import ConsentManager, ConsentState

__all__ = [
    "DialogueTree",
    "ActivationStage",
    "StageInput",
    "StageHandlers",
    "ConsentManager",
    "ConsentState",
]
