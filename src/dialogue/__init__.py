"""
Tiered Activation Dialogue Tree
Stage 0-5 user-led journey with backend handlers.

Stage 1: Consent gate (agency-first)
Stage 2: Distress assessment → Fusion Engine input
"""

from .stage_handlers import StageHandlers, DialogueStage

__all__ = ["StageHandlers", "DialogueStage"]
