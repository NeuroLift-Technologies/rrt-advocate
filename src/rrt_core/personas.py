from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import CrisisAssessment, DistressInput, TOIConfig


PERSONA_SUMMARIES = {
    "ash": "Validates burnout, diffuses shame, and protects rest.",
    "sol": "Breaks overwhelm into workable next steps.",
    "echo": "Mirrors self-talk and gently reframes distortions.",
    "kai": "Redirects hyperfocus and stuck loops into a bounded path.",
    "myra": "Provides relational safety, co-regulation, and silent mode anchoring.",
}


@dataclass
class FusionPlan:
    weights: dict[str, float]
    silent_mode: bool
    response_focus: list[str]


class PersonaFusionEngine:
    def __init__(self, config: dict[str, Any]):
        self.stage_map = config.get("stage_2_distress_map", {})

    def compose(self, distress_input: DistressInput, assessment: CrisisAssessment, toi: TOIConfig) -> FusionPlan:
        distress_config = self.stage_map[distress_input.value]
        weights = {
            persona: float(value)
            for persona, value in distress_config.get("persona_weights", {}).items()
        }

        semantic_details = next(
            (layer.details for layer in assessment.layer_results if layer.name == "semantic"),
            {},
        )
        sentiment_details = next(
            (layer.details for layer in assessment.layer_results if layer.name == "sentiment"),
            {},
        )
        behavioral_details = next(
            (layer.details for layer in assessment.layer_results if layer.name == "behavioral"),
            {},
        )

        weights["echo"] = weights.get("echo", 0.0) + semantic_details.get("negative_self_talk", 0.0) * 0.35
        weights["ash"] = weights.get("ash", 0.0) + semantic_details.get("overwhelm", 0.0) * 0.22
        weights["myra"] = weights.get("myra", 0.0) + semantic_details.get("shutdown", 0.0) * 0.40
        weights["sol"] = weights.get("sol", 0.0) + semantic_details.get("task_avoidance", 0.0) * 0.30
        weights["kai"] = weights.get("kai", 0.0) + semantic_details.get("hyperfocus_loop", 0.0) * 0.35

        weights["echo"] += sentiment_details.get("negative_ratio", 0.0) * 0.20
        weights["ash"] += sentiment_details.get("intensity_ratio", 0.0) * 0.10
        weights["myra"] += behavioral_details.get("latency_score", 0.0) * 0.12
        weights["myra"] += behavioral_details.get("complexity_score", 0.0) * 0.15
        weights["kai"] += behavioral_details.get("looping_score", 0.0) * 0.20

        if toi.cognitive_scaffolding in {"high", "structured"}:
            weights["sol"] += 0.08
        if toi.tone.value == "directive":
            weights["sol"] += 0.05
            weights["kai"] += 0.05

        total = sum(weights.values()) or 1.0
        normalized = {persona: value / total for persona, value in weights.items()}
        silent_mode = bool(distress_config.get("silent_mode", False) or assessment.silent_mode)

        return FusionPlan(
            weights=normalized,
            silent_mode=silent_mode,
            response_focus=list(distress_config.get("response_focus", [])),
        )
