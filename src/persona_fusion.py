"""Persona fusion engine for dynamic distress-specific blending."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class DistressSignal(Enum):
    MELTDOWN = "everything hurts / meltdown"
    BASIC_TASKS = "can't do basic tasks"
    SELF_BLAME = "can't stop self-blame"
    HYPERFOCUS_LOOP = "stuck in hyperfocus/loop"
    SHUTDOWN = "don't know / shut down"


@dataclass(frozen=True)
class PersonaBlend:
    distress_signal: DistressSignal
    weights: Dict[str, float]
    rationale: List[str]
    silent_mode: bool


class PersonaFusionEngine:
    """Computes normalized persona weights using configurable distress maps."""

    PERSONAS = ("ash", "sol", "echo", "kai", "myra")

    def __init__(self, config: Optional[Dict[str, object]] = None):
        config = config or {}
        fusion_cfg = config.get("persona_fusion", {}) if isinstance(config, dict) else {}

        default_base = {persona: 0.2 for persona in self.PERSONAS}
        base_weights = fusion_cfg.get("base_weights", {}) if isinstance(fusion_cfg, dict) else {}
        self.base_weights = {
            persona: float(base_weights.get(persona, default_base[persona]))
            for persona in self.PERSONAS
        }

        self.stage2_mapping = fusion_cfg.get("stage2_mapping", {}) if isinstance(fusion_cfg, dict) else {}
        self.high_risk_myra_boost = float(fusion_cfg.get("high_risk_myra_boost", 0.25))
        self.high_risk_ash_boost = float(fusion_cfg.get("high_risk_ash_boost", 0.15))

    def compute_blend(
        self,
        distress_signal: DistressSignal,
        cde_risk: float = 0.0,
        layer1_matches: Optional[Dict[str, float]] = None,
    ) -> PersonaBlend:
        weights = dict(self.base_weights)
        rationale: List[str] = []

        signal_config = self.stage2_mapping.get(distress_signal.value, {})
        boosts = signal_config.get("persona_boosts", {}) if isinstance(signal_config, dict) else {}
        for persona, boost in boosts.items():
            key = str(persona).lower()
            if key in weights:
                weights[key] += float(boost)

        if layer1_matches:
            # Distress flavor tuning from CDE layer-1 lexical matches.
            if layer1_matches.get("task_avoidance", 0.0) > 0.0:
                weights["sol"] += 0.15
                rationale.append("Layer-1 task avoidance => Sol support increased.")
            if layer1_matches.get("negative_self_talk", 0.0) > 0.0:
                weights["echo"] += 0.15
                rationale.append("Layer-1 self-talk markers => Echo support increased.")
            if layer1_matches.get("overwhelm", 0.0) > 0.0:
                weights["ash"] += 0.12
                weights["myra"] += 0.12
                rationale.append("Layer-1 overwhelm markers => Ash/Myra co-regulation increased.")

        if cde_risk >= 0.75:
            weights["myra"] += self.high_risk_myra_boost
            weights["ash"] += self.high_risk_ash_boost
            rationale.append("Elevated crisis risk => safety-oriented Ash/Myra boost.")

        normalized = self._normalize(weights)

        silent_mode = bool(signal_config.get("silent_mode", False))
        if distress_signal == DistressSignal.SHUTDOWN:
            silent_mode = True
            rationale.append("Shutdown signal => Silent Mode enabled (calm visuals, no timers).")

        if not rationale:
            rationale.append("Applied Stage-2 distress mapping and normalized persona blend.")

        return PersonaBlend(
            distress_signal=distress_signal,
            weights=normalized,
            rationale=rationale,
            silent_mode=silent_mode,
        )

    @staticmethod
    def _normalize(weights: Dict[str, float]) -> Dict[str, float]:
        total = sum(max(value, 0.0) for value in weights.values())
        if total <= 0:
            default = 1.0 / max(1, len(weights))
            return {name: default for name in weights}
        return {name: max(value, 0.0) / total for name, value in weights.items()}
