"""
Persona definitions and fusion logic for RRT AIdvocAIte.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .models import DistressSignal, FusionResult


PERSONA_DEFINITIONS: Dict[str, str] = {
    "ASH": "Validates burnout, diffuses shame, and prioritizes being over doing.",
    "SOL": "Scaffolds executive function with simple, low-friction next steps.",
    "ECHO": "Mirrors internal monologue and gently reframes cognitive distortions.",
    "KAI": "Redirects hyperfocus loops into constructive and safe pathways.",
    "MYRA": "Provides relational safety, co-regulation, and silent-mode anchoring.",
}


@dataclass
class PersonaMappingRule:
    weights: Dict[str, float]
    silent_mode: bool
    rationale: str


class PersonaFusionEngine:
    """
    Maps Stage-2 distress selections to multi-persona blends and allows
    dynamic nudging based on CDE tags.
    """

    _base_rules: Dict[DistressSignal, PersonaMappingRule] = {
        DistressSignal.MELTDOWN: PersonaMappingRule(
            weights={"ASH": 0.45, "MYRA": 0.45, "SOL": 0.05, "ECHO": 0.03, "KAI": 0.02},
            silent_mode=False,
            rationale="Meltdown requires co-regulation and shame-resistant validation.",
        ),
        DistressSignal.TASKS_IMPOSSIBLE: PersonaMappingRule(
            weights={"SOL": 0.65, "ASH": 0.15, "MYRA": 0.1, "ECHO": 0.05, "KAI": 0.05},
            silent_mode=False,
            rationale="Task paralysis centers executive-function scaffolding.",
        ),
        DistressSignal.SELF_BLAME_LOOP: PersonaMappingRule(
            weights={"ECHO": 0.65, "ASH": 0.2, "MYRA": 0.1, "SOL": 0.03, "KAI": 0.02},
            silent_mode=False,
            rationale="Self-blame loop needs reflective reframing plus emotional safety.",
        ),
        DistressSignal.HYPERFOCUS_LOOP: PersonaMappingRule(
            weights={"KAI": 0.65, "SOL": 0.15, "MYRA": 0.1, "ASH": 0.05, "ECHO": 0.05},
            silent_mode=False,
            rationale="Hyperfocus redirection works best with structured repathing.",
        ),
        DistressSignal.SHUTDOWN: PersonaMappingRule(
            weights={"MYRA": 0.75, "ASH": 0.15, "SOL": 0.05, "ECHO": 0.03, "KAI": 0.02},
            silent_mode=True,
            rationale="Shutdown prioritizes non-verbal safety and reduced demand.",
        ),
        DistressSignal.UNSPECIFIED: PersonaMappingRule(
            weights={"MYRA": 0.35, "ASH": 0.25, "SOL": 0.15, "ECHO": 0.15, "KAI": 0.1},
            silent_mode=False,
            rationale="Ambiguous distress defaults to safety-first balanced support.",
        ),
    }

    _tag_adjustments: Dict[str, Dict[str, float]] = {
        "negative_self_talk": {"ECHO": 0.1, "ASH": 0.05},
        "task_avoidance": {"SOL": 0.12},
        "overwhelm": {"MYRA": 0.08, "ASH": 0.05},
        "looping_behavior": {"KAI": 0.1},
    }

    def fuse(self, distress_signal: DistressSignal, cde_tags: Iterable[str] | None = None) -> FusionResult:
        rule = self._base_rules.get(distress_signal, self._base_rules[DistressSignal.UNSPECIFIED])
        blended = dict(rule.weights)

        for tag in cde_tags or []:
            adjustments = self._tag_adjustments.get(tag, {})
            for persona, delta in adjustments.items():
                blended[persona] = blended.get(persona, 0.0) + delta

        normalized = _normalize(blended)
        return FusionResult(
            distress_signal=distress_signal,
            persona_weights=normalized,
            silent_mode=rule.silent_mode,
            rationale=rule.rationale,
        )

    def summarize_weights(self, weights: Dict[str, float]) -> str:
        parts: List[str] = []
        for persona, value in sorted(weights.items(), key=lambda item: item[1], reverse=True):
            parts.append(f"{persona}:{value:.2f}")
        return ", ".join(parts)


def _normalize(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, value) for value in weights.values())
    if total <= 0:
        return {name: 0.0 for name in PERSONA_DEFINITIONS}
    return {name: max(0.0, value) / total for name, value in weights.items()}
