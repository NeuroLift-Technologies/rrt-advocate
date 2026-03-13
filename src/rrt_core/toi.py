from __future__ import annotations

from typing import Any

from .models import PERSONA_ORDER, SafetyBoundaries, TOIConfig, ToneProfile


class TOIParser:
    def __init__(self, defaults: dict[str, Any]):
        self.defaults = defaults

    def parse(self, payload: dict[str, Any] | TOIConfig | None) -> TOIConfig:
        if isinstance(payload, TOIConfig):
            return payload

        base = self.defaults.get("toi_defaults", {})
        merged = dict(base)
        if payload:
            merged.update({k: v for k, v in payload.items() if k != "safety_boundaries"})
            merged_boundaries = dict(base.get("safety_boundaries", {}))
            merged_boundaries.update(payload.get("safety_boundaries", {}))
        else:
            merged_boundaries = dict(base.get("safety_boundaries", {}))

        tone_value = merged.get("tone", ToneProfile.SUPPORTIVE_DEFAULT.value)
        try:
            tone = ToneProfile(tone_value)
        except ValueError:
            tone = ToneProfile.SUPPORTIVE_DEFAULT

        blocked = tuple(
            persona for persona in merged_boundaries.get("blocked_personas", []) if persona in PERSONA_ORDER
        )
        max_active = int(merged_boundaries.get("max_active_personas", 3))
        max_active = max(1, min(max_active, len(PERSONA_ORDER)))

        return TOIConfig(
            tone=tone,
            pacing=str(merged.get("pacing", "gentle")),
            cognitive_scaffolding=str(merged.get("cognitive_scaffolding", "moderate")),
            safety_boundaries=SafetyBoundaries(
                require_explicit_consent=bool(merged_boundaries.get("require_explicit_consent", True)),
                allow_external_escalation=bool(merged_boundaries.get("allow_external_escalation", False)),
                allow_reflective_questions=bool(merged_boundaries.get("allow_reflective_questions", True)),
                allow_silent_mode=bool(merged_boundaries.get("allow_silent_mode", True)),
                max_active_personas=max_active,
                blocked_personas=blocked,
            ),
        )


class OTOIGovernor:
    def govern(self, weights: dict[str, float], toi: TOIConfig, *, silent_mode: bool) -> dict[str, float]:
        governed = {
            persona: max(0.0, value)
            for persona, value in weights.items()
            if persona in PERSONA_ORDER and persona not in toi.safety_boundaries.blocked_personas
        }
        if not governed:
            governed = {"myra": 1.0}

        if not toi.safety_boundaries.allow_reflective_questions:
            governed["echo"] = governed.get("echo", 0.0) * 0.7
            governed["ash"] = governed.get("ash", 0.0) * 0.9

        if toi.pacing in {"slow", "gentle", "minimal"}:
            governed["myra"] = governed.get("myra", 0.0) + 0.05
            governed["ash"] = governed.get("ash", 0.0) + 0.03
            governed["kai"] = governed.get("kai", 0.0) * 0.9

        if silent_mode and toi.safety_boundaries.allow_silent_mode:
            governed["myra"] = governed.get("myra", 0.0) + 0.2
            limit = min(2, toi.safety_boundaries.max_active_personas)
        elif toi.tone == ToneProfile.MINIMAL:
            limit = min(2, toi.safety_boundaries.max_active_personas)
        else:
            limit = toi.safety_boundaries.max_active_personas

        ranked = sorted(governed.items(), key=lambda item: item[1], reverse=True)
        selected = dict(ranked[:limit])
        total = sum(selected.values()) or 1.0
        normalized = {persona: value / total for persona, value in selected.items()}

        if len(normalized) > 1:
            top_persona, top_weight = max(normalized.items(), key=lambda item: item[1])
            if top_weight > 0.8:
                others = [persona for persona in normalized if persona != top_persona]
                if others:
                    shared = 0.2 / len(others)
                    normalized[top_persona] = 0.8
                    for persona in others:
                        normalized[persona] = shared

        return dict(sorted(normalized.items(), key=lambda item: item[1], reverse=True))
