"""Tiered Activation Dialogue Tree — agency-first, consent-gated interaction flow."""
from .tiered_tree import TieredDialogueTree, DialogueStage, StageResult
from .consent_manager import ConsentManager

__all__ = [
    "TieredDialogueTree",
    "DialogueStage",
    "StageResult",
    "ConsentManager",
]
