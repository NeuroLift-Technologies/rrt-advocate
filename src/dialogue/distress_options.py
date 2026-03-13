"""
Stage 2 Distress Options - User-Led Assessment Inputs

Maps the Tiered Activation Dialogue Tree Stage 2 choices to:
- Persona Fusion Engine weights (via distress_mapper)
- Silent Mode trigger (for "Don't know / Shut down")
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class DistressOption:
    """Single Stage 2 distress assessment option"""
    id: str
    label: str
    triggers_silent_mode: bool = False
    primary_personas: List[str] = None  # Ash, Sol, Echo, Kai, Myra
    description: str = ""

    def __post_init__(self):
        if self.primary_personas is None:
            self.primary_personas = []


# Stage 2 Distress Assessment Options
# Input → Heavily weighted personas per Handoff Briefing Section 3C
DISTRESS_OPTIONS: Dict[str, DistressOption] = {
    "everything_hurts_meltdown": DistressOption(
        id="everything_hurts_meltdown",
        label="Everything hurts / Meltdown",
        triggers_silent_mode=False,
        primary_personas=["ash", "myra"],
        description="Overwhelm, sensory overload, burnout—prioritize being over doing"
    ),
    "cant_do_basic_tasks": DistressOption(
        id="cant_do_basic_tasks",
        label="Can't do basic tasks",
        triggers_silent_mode=False,
        primary_personas=["sol"],
        description="Executive function collapse—scaffolding and task breakdown"
    ),
    "cant_stop_self_blame": DistressOption(
        id="cant_stop_self_blame",
        label="Can't stop self-blame",
        triggers_silent_mode=False,
        primary_personas=["echo"],
        description="Negative self-talk, cognitive distortions—mirroring and reframing"
    ),
    "stuck_hyperfocus_loop": DistressOption(
        id="stuck_hyperfocus_loop",
        label="Stuck in hyperfocus/loop",
        triggers_silent_mode=False,
        primary_personas=["kai"],
        description="Fixation, repetitive loops—redirect into constructive pathways"
    ),
    "dont_know_shut_down": DistressOption(
        id="dont_know_shut_down",
        label="Don't know / Shut down",
        triggers_silent_mode=True,
        primary_personas=["myra"],
        description="Non-verbal shutdown—Myra anchors, calm visuals, no timers"
    ),
}


def get_stage2_options() -> List[Dict[str, Any]]:
    """Return Stage 2 options for UI/backend binding (id, label, triggers_silent_mode)."""
    return [
        {
            "id": opt.id,
            "label": opt.label,
            "triggers_silent_mode": opt.triggers_silent_mode,
        }
        for opt in DISTRESS_OPTIONS.values()
    ]


def get_option_by_id(option_id: str) -> Optional[DistressOption]:
    """Get distress option by ID."""
    return DISTRESS_OPTIONS.get(option_id)


def get_option_by_label_fuzzy(label: str) -> Optional[DistressOption]:
    """Fuzzy match label to option (e.g. 'meltdown' -> everything_hurts_meltdown)."""
    label_lower = label.strip().lower()
    for opt in DISTRESS_OPTIONS.values():
        if label_lower in opt.label.lower() or opt.label.lower() in label_lower:
            return opt
    return None
