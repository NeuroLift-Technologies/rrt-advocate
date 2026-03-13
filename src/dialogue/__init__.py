"""
Tiered Activation Dialogue Tree
RRT AIdvocAIte — Protective Layer of the Solidarity Framework

Implements the Stage 0–5 user journey, prioritizing user agency and
explicit consent at the moment of intervention.
"""
from .stages import ActivationStage, StageConfig, STAGE_CONFIGS
from .dialogue_tree import DialogueTree, DialogueState, StageTransition

__all__ = [
    "ActivationStage",
    "StageConfig",
    "STAGE_CONFIGS",
    "DialogueTree",
    "DialogueState",
    "StageTransition",
]
