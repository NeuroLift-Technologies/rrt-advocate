"""
TOI and OTOI governance middleware.
"""

from __future__ import annotations

from typing import Dict

from .models import OTOIPolicy, TOIConfig


class TOIOTOIGovernanceWrapper:
    """
    Enforces user TOI and applies OTOI persona coordination constraints.
    """

    def __init__(self, toi_config: TOIConfig, otoi_policy: OTOIPolicy | None = None):
        self.toi_config = toi_config
        self.otoi_policy = otoi_policy or OTOIPolicy()

    def requires_stage_1_consent(self) -> bool:
        return bool(
            self.toi_config.safety_boundaries.get(
                "require_consent_before_activation",
                True,
            )
        )

    def sanitize_user_text(self, user_text: str) -> str:
        # Low-demand normalization only; avoids changing user intent.
        return " ".join(user_text.strip().split())

    def enforce_persona_contract(self, raw_weights: Dict[str, float]) -> Dict[str, float]:
        """
        Ensure no single persona dominates against OTOI policy while
        preserving the user's requested support profile.
        """
        if not raw_weights:
            return {}

        normalized = _normalize({name: max(0.0, value) for name, value in raw_weights.items()})
        bounded = _cap_and_redistribute(normalized, self.otoi_policy.max_persona_weight)

        active_count = sum(1 for value in bounded.values() if value > 0.01)
        if active_count >= self.otoi_policy.min_active_personas:
            return bounded

        # If only one persona is active after clipping, re-balance by activating
        # the top secondary persona at a small but meaningful share.
        sorted_items = sorted(bounded.items(), key=lambda item: item[1], reverse=True)
        if len(sorted_items) >= 2 and sorted_items[1][1] == 0:
            primary_name, primary_weight = sorted_items[0]
            secondary_name, _ = sorted_items[1]
            adjusted = dict(bounded)
            transfer = min(0.15, primary_weight / 2)
            adjusted[primary_name] = max(0.0, primary_weight - transfer)
            adjusted[secondary_name] = transfer
            return _normalize(adjusted)

        return bounded

    def enforce_safety_boundaries(self, response_text: str) -> str:
        disallowed = self.toi_config.safety_boundaries.get("disallowed_response_patterns", [])
        safe_text = response_text
        for pattern in disallowed:
            if pattern and pattern in safe_text:
                safe_text = safe_text.replace(pattern, "[removed-per-toi]")
        return safe_text


def _normalize(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        return {key: 0.0 for key in weights}
    return {key: value / total for key, value in weights.items()}


def _cap_and_redistribute(weights: Dict[str, float], max_weight: float) -> Dict[str, float]:
    """
    Keep each weight <= max_weight while preserving relative shares.
    """
    # If the cap is mathematically impossible, fall back to an even distribution cap.
    if weights and (max_weight * len(weights) < 1.0):
        max_weight = 1.0 / len(weights)

    current = dict(weights)
    capped: Dict[str, float] = {}
    uncapped = set(current.keys())
    remaining = 1.0

    while uncapped:
        over_limit = [name for name in uncapped if current[name] > max_weight]
        if not over_limit:
            total_uncapped = sum(current[name] for name in uncapped)
            if total_uncapped <= 0:
                share = remaining / len(uncapped)
                for name in uncapped:
                    capped[name] = share
            else:
                for name in uncapped:
                    capped[name] = remaining * (current[name] / total_uncapped)
            break

        for name in over_limit:
            capped[name] = max_weight
            remaining -= max_weight
            uncapped.remove(name)

        if not uncapped:
            break

        total_uncapped = sum(current[name] for name in uncapped)
        if total_uncapped <= 0:
            even_share = remaining / len(uncapped)
            for name in uncapped:
                current[name] = even_share
        else:
            for name in uncapped:
                current[name] = remaining * (current[name] / total_uncapped)

    return _normalize({name: max(0.0, value) for name, value in capped.items()})
