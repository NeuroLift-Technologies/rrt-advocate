"""Local-first engines for TOI governance, detection, fusion, and dialogue."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import math
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import yaml

from .models import (
    CDELayerScore,
    CrisisDetectionResult,
    CrisisLevel,
    DialogueStage,
    DistressSignal,
    PersonaBlend,
    ResponsePlan,
    TOIConfig,
    ToneProfile,
    SafetyBoundaries,
    SilentModeConfig,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RRT_CONFIG_PATH = REPOSITORY_ROOT / "config" / "crisis_thresholds.yaml"
DEFAULT_TOI_CONFIG_PATH = REPOSITORY_ROOT / "config" / "toi_defaults.yaml"
PERSONA_ORDER = ("ash", "sol", "echo", "kai", "myra")

PERSONA_GUIDANCE = {
    "ash": {
        "role": "Validates burnout, diffuses shame, and protects rest.",
        "line": "You are not failing; strain changes what is possible right now.",
    },
    "sol": {
        "role": "Scaffolds executive function into tiny practical steps.",
        "line": "We can shrink this to one concrete, low-friction action.",
    },
    "echo": {
        "role": "Mirrors internal monologue and softens cognitive distortions.",
        "line": "The harsh story is loud right now, but it is not the whole picture.",
    },
    "kai": {
        "role": "Redirects loops and hyperfocus into safer channels.",
        "line": "We can redirect the loop instead of wrestling it head-on.",
    },
    "myra": {
        "role": "Provides relational safety, co-regulation, and silent-mode anchoring.",
        "line": "I am staying steady with you and keeping this low-demand.",
    },
}

DISTRESS_ACTIONS = {
    DistressSignal.MELTDOWN: [
        "Lower demand for the next minute: sit, lean, or lie down if that helps.",
        "Pick one grounding anchor: feet on the floor, cold water, or pressure in your hands.",
    ],
    DistressSignal.TASK_PARALYSIS: [
        "Choose the smallest physical start: open it, place it in front of you, or write one word.",
        "Ignore the full task; name only the next visible action.",
    ],
    DistressSignal.SELF_BLAME: [
        "Separate facts from the attack voice in one short sentence.",
        "Try: 'I am overloaded, not lazy.'",
    ],
    DistressSignal.HYPERFOCUS_LOOP: [
        "Move the loop outside your head: write one line about what has you hooked.",
        "Set a redirect target that is adjacent, not opposite.",
    ],
    DistressSignal.SHUTDOWN: [
        "No timer. No checklist. Pick one comfort cue: water, blanket, or quiet.",
        "You can answer with one word, an emoji, or not at all.",
    ],
}


def load_yaml_config(path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML configuration file into a dictionary."""
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _normalize_weights(raw_weights: Dict[str, float]) -> Dict[str, float]:
    weights = {persona: max(0.0, raw_weights.get(persona, 0.0)) for persona in PERSONA_ORDER}
    total = sum(weights.values())
    if total <= 0:
        return {persona: (1.0 if persona == "myra" else 0.0) for persona in PERSONA_ORDER}
    return {persona: round(weight / total, 4) for persona, weight in weights.items()}


def _coerce_tone(value: Optional[str]) -> ToneProfile:
    if value is None:
        return ToneProfile.SUPPORTIVE_DEFAULT
    normalized = value.strip().lower()
    for tone in ToneProfile:
        if tone.value == normalized:
            return tone
    return ToneProfile.SUPPORTIVE_DEFAULT


def _jaccard_similarity(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"\b[\w']+\b", left.lower()))
    right_tokens = set(re.findall(r"\b[\w']+\b", right.lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _simple_polarity(text: str, negative_terms: Sequence[str], positive_terms: Sequence[str]) -> float:
    lowered = text.lower()
    negative_count = sum(lowered.count(term) for term in negative_terms)
    positive_count = sum(lowered.count(term) for term in positive_terms)
    total = negative_count + positive_count
    if total == 0:
        return 0.0
    return (positive_count - negative_count) / total


def _crisis_level_for_score(score: float, bands: Dict[str, Sequence[float]]) -> CrisisLevel:
    normalized = _clamp(score)
    for level_name, threshold_range in bands.items():
        lower, upper = threshold_range
        if lower <= normalized <= upper:
            return CrisisLevel[level_name.upper()]
    return CrisisLevel.BLACK if normalized > 0.88 else CrisisLevel.GREEN


class TOIParser:
    """Parse a TOI contract from YAML or an in-memory dictionary."""

    def __init__(self, default_path: Union[str, Path] = DEFAULT_TOI_CONFIG_PATH):
        self.default_path = Path(default_path)

    def load(self, source: Optional[Union[str, Path, Dict[str, Any]]] = None) -> TOIConfig:
        raw = self._load_raw(source)
        toi = raw.get("toi", raw)
        safety = toi.get("safety_boundaries", {})
        silent_mode = toi.get("silent_mode", {})
        return TOIConfig(
            tone=_coerce_tone(toi.get("tone")),
            pacing=toi.get("pacing", "gentle"),
            cognitive_scaffolding=toi.get("cognitive_scaffolding", "layered"),
            preferred_personas=list(toi.get("preferred_personas", [])),
            blocked_personas=list(toi.get("blocked_personas", [])),
            silent_mode=SilentModeConfig(
                enabled=bool(silent_mode.get("enabled", True)),
                no_timers=bool(silent_mode.get("no_timers", True)),
                calm_visuals=bool(silent_mode.get("calm_visuals", True)),
                minimal_text=bool(silent_mode.get("minimal_text", True)),
            ),
            safety_boundaries=SafetyBoundaries(
                require_stage1_consent=bool(safety.get("require_stage1_consent", True)),
                allow_directive_tone=bool(safety.get("allow_directive_tone", True)),
                allow_reflective_questions=bool(safety.get("allow_reflective_questions", True)),
                protect_from_productivity_pressure=bool(
                    safety.get("protect_from_productivity_pressure", True)
                ),
                allow_external_escalation=bool(safety.get("allow_external_escalation", False)),
                max_single_persona_weight=float(safety.get("max_single_persona_weight", 0.58)),
            ),
        )

    def _load_raw(self, source: Optional[Union[str, Path, Dict[str, Any]]]) -> Dict[str, Any]:
        if source is None:
            return load_yaml_config(self.default_path)
        if isinstance(source, dict):
            return source
        return load_yaml_config(source)


class OTOIGovernor:
    """Apply TOI/OTOI constraints to persona and tone orchestration."""

    def apply(
        self,
        raw_weights: Dict[str, float],
        toi: TOIConfig,
        suggested_tone: ToneProfile,
        distress_signal: Optional[DistressSignal],
    ) -> PersonaBlend:
        weights = {persona: max(0.0, raw_weights.get(persona, 0.0)) for persona in PERSONA_ORDER}
        rationale: List[str] = []

        for persona in toi.blocked_personas:
            if persona in weights:
                weights[persona] = 0.0
                rationale.append(f"TOI blocked {persona}, so its weight was removed.")

        for persona in toi.preferred_personas:
            if persona in weights:
                weights[persona] += 0.03
                rationale.append(f"TOI preference boosted {persona}.")

        if (
            toi.safety_boundaries.protect_from_productivity_pressure
            and distress_signal in {DistressSignal.MELTDOWN, DistressSignal.SHUTDOWN}
        ):
            weights["sol"] *= 0.55
            weights["kai"] *= 0.55
            rationale.append("Burnout guardrails reduced productivity-forward personas.")

        silent_mode = bool(toi.silent_mode.enabled and distress_signal == DistressSignal.SHUTDOWN)
        if silent_mode:
            weights["myra"] = max(weights["myra"], 0.55)
            rationale.append("Silent Mode keeps Myra dominant and removes timer pressure.")

        weights = self._cap_single_persona(weights, toi.safety_boundaries.max_single_persona_weight)
        weights = _normalize_weights(weights)

        tone = toi.tone or suggested_tone
        if tone == ToneProfile.DIRECTIVE and not toi.safety_boundaries.allow_directive_tone:
            tone = ToneProfile.MINIMAL if toi.silent_mode.minimal_text else ToneProfile.SUPPORTIVE_DEFAULT
            rationale.append("Directive tone was blocked by TOI safety boundaries.")
        elif tone == ToneProfile.THERAPEUTIC_REFLECTIVE and not toi.safety_boundaries.allow_reflective_questions:
            tone = ToneProfile.SUPPORTIVE_DEFAULT
            rationale.append("Reflective questioning was blocked by TOI safety boundaries.")

        dominant_personas = [
            persona for persona, _ in sorted(weights.items(), key=lambda item: item[1], reverse=True)[:3]
        ]
        return PersonaBlend(
            weights=weights,
            dominant_personas=dominant_personas,
            tone_profile=tone,
            silent_mode=silent_mode,
            rationale=rationale,
        )

    def _cap_single_persona(self, weights: Dict[str, float], max_weight: float) -> Dict[str, float]:
        max_weight = _clamp(max_weight, minimum=0.2, maximum=0.8)
        adjusted = dict(weights)
        overflow = 0.0
        under_cap_personas: List[str] = []

        for persona, weight in adjusted.items():
            if weight > max_weight:
                overflow += weight - max_weight
                adjusted[persona] = max_weight
            else:
                under_cap_personas.append(persona)

        if overflow > 0 and under_cap_personas:
            redistribution = overflow / len(under_cap_personas)
            for persona in under_cap_personas:
                adjusted[persona] += redistribution
        return adjusted


class LocalFirstCrisisDetectionEngine:
    """Three-layer local pipeline for distress detection."""

    def __init__(self, config: Dict[str, Any]):
        protective_layer = config.get("protective_layer", {})
        self.config = protective_layer
        self.cde_config = protective_layer.get("cde", {})
        self.risk_bands = protective_layer.get("risk_bands", {})

    def analyze(
        self,
        message: str,
        history: Optional[Sequence[str]] = None,
        response_latency_seconds: Optional[float] = None,
    ) -> CrisisDetectionResult:
        history = list(history or [])
        semantic_layer, category_counts = self._semantic_analysis(message)
        sentiment_layer = self._sentiment_analysis(message, history)
        behavioral_layer = self._behavioral_analysis(message, history, response_latency_seconds)

        layer_weights = self.cde_config.get(
            "layer_weights",
            {"semantic": 0.45, "sentiment": 0.35, "behavioral": 0.20},
        )
        overall_score = _clamp(
            semantic_layer.score * layer_weights.get("semantic", 0.45)
            + sentiment_layer.score * layer_weights.get("sentiment", 0.35)
            + behavioral_layer.score * layer_weights.get("behavioral", 0.20)
        )

        safety_keywords = self._detect_safety_keywords(message)
        if safety_keywords:
            overall_score = max(overall_score, 0.92)

        crisis_level = _crisis_level_for_score(overall_score, self.risk_bands)
        dominant_distress = self._infer_distress_signal(
            category_counts=category_counts,
            message=message,
            behavioral_score=behavioral_layer.score,
        )
        primary_indicators = list(dict.fromkeys(semantic_layer.indicators + safety_keywords))[:6]
        secondary_indicators = list(
            dict.fromkeys(sentiment_layer.indicators + behavioral_layer.indicators)
        )[:6]

        return CrisisDetectionResult(
            timestamp=datetime.now(),
            crisis_level=crisis_level,
            overall_score=overall_score,
            layer_scores=[semantic_layer, sentiment_layer, behavioral_layer],
            primary_indicators=primary_indicators,
            secondary_indicators=secondary_indicators,
            semantic_categories=list(category_counts.keys()),
            dominant_distress=dominant_distress,
            sentiment_shift=sentiment_layer.details.get("polarity_drop", 0.0),
            behavioral_risk=behavioral_layer.score,
            safety_keywords=safety_keywords,
            local_only=True,
        )

    def _semantic_analysis(self, message: str) -> Tuple[CDELayerScore, Dict[str, int]]:
        lowered = message.lower()
        fields = self.cde_config.get("semantic_fields", {})
        category_counts: Dict[str, int] = {}
        indicators: List[str] = []

        for category, phrases in fields.items():
            match_count = 0
            for phrase in phrases:
                if phrase.lower() in lowered:
                    match_count += 1
                    indicators.append(f"{category}:{phrase}")
            if match_count:
                category_counts[category] = match_count

        weighted_hits = sum(min(1.0, count / 2.0) for count in category_counts.values())
        score = _clamp(weighted_hits / max(1, len(fields) / 2))
        return (
            CDELayerScore(
                layer_name="semantic",
                score=score,
                indicators=indicators,
                details={"category_counts": dict(category_counts)},
            ),
            category_counts,
        )

    def _sentiment_analysis(self, message: str, history: Sequence[str]) -> CDELayerScore:
        lexicon = self.cde_config.get("sentiment_lexicon", {})
        negative_terms = lexicon.get("negative", [])
        positive_terms = lexicon.get("positive", [])
        intensifiers = lexicon.get("intensifiers", [])

        lowered = message.lower()
        negative_count = sum(lowered.count(term) for term in negative_terms)
        positive_count = sum(lowered.count(term) for term in positive_terms)
        intensity_count = sum(lowered.count(term) for term in intensifiers)
        current_polarity = _simple_polarity(lowered, negative_terms, positive_terms)
        prior_polarities = [
            _simple_polarity(prior.lower(), negative_terms, positive_terms)
            for prior in history[-3:]
        ]
        history_baseline = sum(prior_polarities) / len(prior_polarities) if prior_polarities else 0.0
        polarity_drop = max(0.0, history_baseline - current_polarity)
        score = _clamp(
            (negative_count * 0.14)
            + (intensity_count * 0.06)
            + max(0.0, -current_polarity) * 0.5
            + polarity_drop * 0.4
        )

        indicators = []
        if negative_count:
            indicators.append(f"negative_terms:{negative_count}")
        if intensity_count:
            indicators.append(f"intensifiers:{intensity_count}")
        if polarity_drop:
            indicators.append(f"polarity_drop:{polarity_drop:.2f}")

        return CDELayerScore(
            layer_name="sentiment",
            score=score,
            indicators=indicators,
            details={
                "negative_count": negative_count,
                "positive_count": positive_count,
                "polarity": current_polarity,
                "polarity_drop": round(polarity_drop, 4),
            },
        )

    def _behavioral_analysis(
        self,
        message: str,
        history: Sequence[str],
        response_latency_seconds: Optional[float],
    ) -> CDELayerScore:
        thresholds = self.cde_config.get("behavioral_thresholds", {})
        latency_thresholds = thresholds.get("latency_seconds", {})

        word_count = len(re.findall(r"\b[\w']+\b", message))
        low_complexity_threshold = int(thresholds.get("low_complexity_word_count", 4))
        shutdown_threshold = int(thresholds.get("shutdown_word_count", 3))
        low_complexity_score = 1.0 if word_count <= low_complexity_threshold else max(0.0, 0.35 - word_count * 0.01)
        shutdown_score = 0.4 if word_count <= shutdown_threshold else 0.0

        latency_score = 0.0
        if response_latency_seconds is not None:
            if response_latency_seconds >= latency_thresholds.get("red", math.inf):
                latency_score = 1.0
            elif response_latency_seconds >= latency_thresholds.get("orange", math.inf):
                latency_score = 0.75
            elif response_latency_seconds >= latency_thresholds.get("yellow", math.inf):
                latency_score = 0.45

        looping_ratio = 0.0
        if history:
            looping_ratio = max(_jaccard_similarity(message, previous) for previous in history[-2:])
        looping_threshold = float(thresholds.get("looping_similarity_ratio", 0.72))
        looping_score = 1.0 if looping_ratio >= looping_threshold else max(0.0, looping_ratio * 0.6)

        score = _clamp(
            latency_score * 0.45 + looping_score * 0.3 + low_complexity_score * 0.15 + shutdown_score * 0.1
        )
        indicators = []
        if latency_score:
            indicators.append(f"latency:{response_latency_seconds}s")
        if looping_score:
            indicators.append(f"looping_similarity:{looping_ratio:.2f}")
        if low_complexity_score >= 0.3:
            indicators.append(f"low_complexity_words:{word_count}")

        return CDELayerScore(
            layer_name="behavioral",
            score=score,
            indicators=indicators,
            details={
                "response_latency_seconds": response_latency_seconds,
                "word_count": word_count,
                "looping_similarity": round(looping_ratio, 4),
            },
        )

    def _infer_distress_signal(
        self,
        category_counts: Dict[str, int],
        message: str,
        behavioral_score: float,
    ) -> Optional[DistressSignal]:
        lowered = message.lower()
        explicit_signal = DistressSignal.from_input(message)
        if explicit_signal:
            return explicit_signal
        if "meltdown" in lowered or "everything hurts" in lowered:
            return DistressSignal.MELTDOWN
        if "hyperfocus" in lowered or "loop" in lowered or category_counts.get("hyperfocus_loop"):
            return DistressSignal.HYPERFOCUS_LOOP
        if category_counts.get("negative_self_talk"):
            return DistressSignal.SELF_BLAME
        if category_counts.get("task_avoidance"):
            return DistressSignal.TASK_PARALYSIS
        if behavioral_score >= 0.55 and len(lowered.split()) <= 5:
            return DistressSignal.SHUTDOWN
        if category_counts.get("overwhelm"):
            return DistressSignal.MELTDOWN
        return None

    def _detect_safety_keywords(self, message: str) -> List[str]:
        lowered = message.lower()
        matched = []
        for phrase in self.cde_config.get("immediate_safety_keywords", []):
            if phrase.lower() in lowered:
                matched.append(phrase)
        return matched


class PersonaFusionEngine:
    """Dynamic fusion engine that blends the five OG personas."""

    def __init__(self, config: Dict[str, Any], governor: Optional[OTOIGovernor] = None):
        protective_layer = config.get("protective_layer", {})
        self.config = protective_layer
        self.dialogue_tree = protective_layer.get("dialogue_tree", {})
        self.adjustments = protective_layer.get("persona_adjustments", {})
        self.governor = governor or OTOIGovernor()

    def build_blend(
        self,
        distress_signal: Optional[DistressSignal],
        detection: CrisisDetectionResult,
        toi: TOIConfig,
    ) -> PersonaBlend:
        resolved_signal = distress_signal or detection.dominant_distress or DistressSignal.SHUTDOWN
        signal_config = self.dialogue_tree.get("stage_2_options", {}).get(resolved_signal.value, {})
        weights = dict(signal_config.get("weights", {}))
        rationale = [f"Stage-2 mapping selected {resolved_signal.value}."]

        for category in detection.semantic_categories:
            delta = self.adjustments.get("semantic_fields", {}).get(category, {})
            for persona, increment in delta.items():
                weights[persona] = weights.get(persona, 0.0) + increment
            if delta:
                rationale.append(f"Semantic field '{category}' adjusted persona weights.")

        if detection.sentiment_shift >= 0.35:
            for persona, increment in self.adjustments.get("high_sentiment_drop", {}).items():
                weights[persona] = weights.get(persona, 0.0) + increment
            rationale.append("Sentiment drop increased co-regulation and shame-resistant support.")

        if detection.behavioral_risk >= 0.45:
            for persona, increment in self.adjustments.get("high_behavioral_risk", {}).items():
                weights[persona] = weights.get(persona, 0.0) + increment
            rationale.append("Behavioral risk increased grounding and scaffolding support.")

        if detection.crisis_level in {CrisisLevel.RED, CrisisLevel.BLACK}:
            weights["ash"] = weights.get("ash", 0.0) + 0.04
            weights["myra"] = weights.get("myra", 0.0) + 0.06
            rationale.append("Critical distress reinforced Ash/Myra protective coverage.")

        suggested_tone = _coerce_tone(signal_config.get("tone_bias"))
        blend = self.governor.apply(weights, toi, suggested_tone, resolved_signal)
        blend.rationale = rationale + blend.rationale
        return blend


class TieredActivationDialogueTree:
    """Stage-based planner that keeps consent and agency ahead of intervention."""

    def __init__(self, config: Dict[str, Any]):
        protective_layer = config.get("protective_layer", {})
        self.config = protective_layer
        self.dialogue_tree = protective_layer.get("dialogue_tree", {})
        self.tone_profiles = protective_layer.get("tone_profiles", {})

    def build_plan(
        self,
        toi: TOIConfig,
        detection: CrisisDetectionResult,
        blend: Optional[PersonaBlend],
        consent_granted: bool,
        distress_signal: Optional[DistressSignal],
    ) -> ResponsePlan:
        consent_required = toi.safety_boundaries.require_stage1_consent
        if consent_required and not consent_granted:
            return ResponsePlan(
                stage=DialogueStage.STAGE_1_CONSENT,
                next_stage=DialogueStage.STAGE_2_SIGNAL_SELECTION,
                consent_required=True,
                consent_granted=False,
                user_message=self.dialogue_tree.get(
                    "stage_1_entry_prompt",
                    "I can switch into low-demand RRT AIdvocAIte mode. Want that now?",
                ),
                options=["Yes, keep it low-demand", "Not now"],
                system_prompt="Await explicit consent before activating the protective layer.",
                toi=toi,
                detection=detection,
                blend=None,
                ui_hints=self._ui_hints(toi, None),
            )

        if distress_signal is None:
            options = [
                option["label"]
                for option in self.dialogue_tree.get("stage_2_options", {}).values()
            ]
            return ResponsePlan(
                stage=DialogueStage.STAGE_2_SIGNAL_SELECTION,
                next_stage=DialogueStage.STAGE_3_SUPPORT,
                consent_required=consent_required,
                consent_granted=consent_granted,
                user_message=self.dialogue_tree.get(
                    "stage_2_prompt",
                    "Which of these fits best right now?",
                ),
                options=options,
                system_prompt="Prompt the user to choose a distress flavor before composing support.",
                toi=toi,
                detection=detection,
                blend=None,
                ui_hints=self._ui_hints(toi, None),
            )

        assert blend is not None
        support_message = self._compose_user_message(
            toi=toi,
            detection=detection,
            distress_signal=distress_signal,
            blend=blend,
        )
        stage = DialogueStage.STAGE_3_SUPPORT
        next_stage = DialogueStage.STAGE_4_STABILIZATION
        if detection.crisis_level in {CrisisLevel.RED, CrisisLevel.BLACK} and detection.safety_keywords:
            stage = DialogueStage.STAGE_5_ESCALATION
            next_stage = None
            support_message = (
                f"{support_message}\n\n"
                f"{self.dialogue_tree.get('stage_5_consent_to_escalate', 'Do you want help reaching extra support right now?')}"
            )

        options = [
            "Stay low-demand",
            "Give me one next step",
            "Pause here",
        ]
        if stage == DialogueStage.STAGE_5_ESCALATION and toi.safety_boundaries.allow_external_escalation:
            options = ["Yes, help me escalate", "No, stay here with me"]

        return ResponsePlan(
            stage=stage,
            next_stage=next_stage,
            consent_required=consent_required,
            consent_granted=consent_granted,
            user_message=support_message,
            options=options,
            system_prompt=self._compose_system_prompt(toi, detection, distress_signal, blend),
            toi=toi,
            detection=detection,
            blend=blend,
            ui_hints=self._ui_hints(toi, blend),
        )

    def _compose_system_prompt(
        self,
        toi: TOIConfig,
        detection: CrisisDetectionResult,
        distress_signal: DistressSignal,
        blend: PersonaBlend,
    ) -> str:
        tone_config = self.tone_profiles.get(blend.tone_profile.value, {})
        dominant_guidance = [
            f"{persona.upper()}: {PERSONA_GUIDANCE[persona]['role']}"
            for persona in blend.dominant_personas[:2]
        ]
        prompt_parts = [
            "RRT AIdvocAIte protective-layer prompt:",
            f"- Respect TOI tone={toi.tone.value}, pacing={toi.pacing}, scaffolding={toi.cognitive_scaffolding}.",
            f"- Crisis level={detection.crisis_level.value}, distress={distress_signal.value}.",
            f"- Silent mode={'on' if blend.silent_mode else 'off'}.",
            f"- Tone instructions: {' '.join(tone_config.get('instructions', []))}",
            "- Persona orchestration:",
            *[f"  - {line}" for line in dominant_guidance],
            "- Avoid shame, productivity pressure, and any response that violates TOI safety boundaries.",
        ]
        return "\n".join(prompt_parts)

    def _compose_user_message(
        self,
        toi: TOIConfig,
        detection: CrisisDetectionResult,
        distress_signal: DistressSignal,
        blend: PersonaBlend,
    ) -> str:
        lead_personas = blend.dominant_personas[:2]
        lead_lines = [PERSONA_GUIDANCE[persona]["line"] for persona in lead_personas]
        actions = DISTRESS_ACTIONS.get(distress_signal, DISTRESS_ACTIONS[DistressSignal.SHUTDOWN])

        if blend.silent_mode or blend.tone_profile == ToneProfile.MINIMAL:
            return f"{lead_lines[0]} {actions[0]}"

        if blend.tone_profile == ToneProfile.DIRECTIVE:
            return (
                f"{lead_lines[0]}\n"
                f"1. {actions[0]}\n"
                f"2. {actions[1]}"
            )

        if blend.tone_profile == ToneProfile.THERAPEUTIC_REFLECTIVE:
            question = ""
            if toi.safety_boundaries.allow_reflective_questions:
                question = " What feels 2% safer right now?"
            return f"{lead_lines[0]} {lead_lines[1]} {actions[0]}{question}"

        return f"{lead_lines[0]} {lead_lines[1]} {actions[0]}"

    def _ui_hints(self, toi: TOIConfig, blend: Optional[PersonaBlend]) -> Dict[str, Any]:
        silent_mode = bool(blend.silent_mode) if blend else False
        show_timers = not (silent_mode and toi.silent_mode.no_timers)
        return {
            "calm_visuals": bool(silent_mode and toi.silent_mode.calm_visuals),
            "show_timers": show_timers,
            "minimal_text": bool(silent_mode and toi.silent_mode.minimal_text),
        }
