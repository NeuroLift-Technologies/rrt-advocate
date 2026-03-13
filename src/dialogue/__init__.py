"""
Tiered Activation Dialogue Tree - User-Led, Agency-First Intervention Flow

Stages 0-5 support low-demand, consent-based activation of the RRT Advocate.
Stage 1 Entry Prompt ensures explicit user consent before full deployment.
"""

from .stage_handlers import StageHandlers, DialogueStage
from .stage1_entry import Stage1EntryHandler
from .distress_options import DISTRESS_OPTIONS, get_stage2_options

__all__ = [
    "StageHandlers",
    "DialogueStage",
    "Stage1EntryHandler",
    "DISTRESS_OPTIONS",
    "get_stage2_options",
]
