"""
Data models for the five NLT Original Guides (OGs) and the weight structures
that the Fusion Engine operates on.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Persona:
    """
    Immutable definition of one of the five NLT sub-personas.

    Each persona has a core mandate, a set of distress signals it is
    optimised for, and a set of response strategies it brings to a blend.
    """

    name: str
    mandate: str
    distress_signals: tuple[str, ...]
    strategies: tuple[str, ...]
    preferred_tones: tuple[str, ...]

    def __str__(self) -> str:
        return self.name


ASH = Persona(
    name="ASH",
    mandate="Validates burnout, diffuses shame, prioritises being over doing.",
    distress_signals=(
        "burnout",
        "shame",
        "self-blame",
        "exhaustion",
        "meltdown",
        "everything hurts",
        "can't function",
    ),
    strategies=(
        "unconditional_validation",
        "shame_diffusion",
        "rest_permission",
        "low_demand_presence",
    ),
    preferred_tones=("supportive_default", "therapeutic_reflective"),
)

SOL = Persona(
    name="SOL",
    mandate="Scaffolds executive function, breaks down tasks, manages attention fatigue.",
    distress_signals=(
        "can't start",
        "overwhelmed by tasks",
        "paralysis",
        "executive dysfunction",
        "task avoidance",
        "can't do basic tasks",
    ),
    strategies=(
        "micro_task_breakdown",
        "next_action_identification",
        "working_memory_offload",
        "attention_anchoring",
    ),
    preferred_tones=("directive", "minimal"),
)

ECHO = Persona(
    name="ECHO",
    mandate="Mirrors internal monologue, reframes cognitive distortions and negative self-talk.",
    distress_signals=(
        "self-blame",
        "negative self-talk",
        "cognitive distortions",
        "rumination",
        "inner critic",
        "can't stop self-blame",
        "worthless",
        "failure",
    ),
    strategies=(
        "internal_monologue_mirroring",
        "cognitive_reframing",
        "distortion_labelling",
        "self_compassion_scaffolding",
    ),
    preferred_tones=("therapeutic_reflective", "supportive_default"),
)

KAI = Persona(
    name="KAI",
    mandate="Redirects hyperfocus and fixation into constructive pathways.",
    distress_signals=(
        "hyperfocus",
        "looping",
        "fixation",
        "stuck in loop",
        "can't stop",
        "obsessing",
        "intrusive loop",
    ),
    strategies=(
        "hyperfocus_channeling",
        "loop_interruption",
        "constructive_redirection",
        "curiosity_bridging",
    ),
    preferred_tones=("directive", "supportive_default"),
)

MYRA = Persona(
    name="MYRA",
    mandate="Provides relational safety, co-regulation, and anchors the non-verbal Silent Mode.",
    distress_signals=(
        "shutdown",
        "dissociation",
        "freeze",
        "don't know",
        "can't speak",
        "overwhelmed",
        "need safety",
    ),
    strategies=(
        "co_regulation",
        "non_verbal_presence",
        "silent_mode_anchor",
        "relational_safety",
        "calm_visuals",
    ),
    preferred_tones=("minimal", "supportive_default"),
)

PERSONAS: dict[str, Persona] = {
    "ASH": ASH,
    "SOL": SOL,
    "ECHO": ECHO,
    "KAI": KAI,
    "MYRA": MYRA,
}


@dataclass
class PersonaWeights:
    """
    A set of normalised weights (0.0–1.0) describing how much each persona
    should contribute to the blended response.

    The weights do not need to sum to 1.0 before normalisation; the
    FusionEngine handles normalisation internally.
    """

    ash: float = 0.0
    sol: float = 0.0
    echo: float = 0.0
    kai: float = 0.0
    myra: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "ASH": self.ash,
            "SOL": self.sol,
            "ECHO": self.echo,
            "KAI": self.kai,
            "MYRA": self.myra,
        }

    def normalised(self) -> "PersonaWeights":
        """Return a copy where all weights sum to 1.0."""
        total = self.ash + self.sol + self.echo + self.kai + self.myra
        if total == 0.0:
            return PersonaWeights(ash=0.2, sol=0.2, echo=0.2, kai=0.2, myra=0.2)
        factor = 1.0 / total
        return PersonaWeights(
            ash=round(self.ash * factor, 4),
            sol=round(self.sol * factor, 4),
            echo=round(self.echo * factor, 4),
            kai=round(self.kai * factor, 4),
            myra=round(self.myra * factor, 4),
        )

    def ranked(self) -> list[str]:
        """Return persona names sorted from highest to lowest weight."""
        items = list(self.as_dict().items())
        items.sort(key=lambda kv: kv[1], reverse=True)
        return [name for name, _ in items if _ > 0.0] or ["MYRA"]


@dataclass
class PersonaBlend:
    """The output of the FusionEngine: weights + resolved personas + lead persona."""

    weights: PersonaWeights
    lead_persona: Persona
    contributing_personas: list[Persona] = field(default_factory=list)
    distress_type: str = ""
    rationale: str = ""
