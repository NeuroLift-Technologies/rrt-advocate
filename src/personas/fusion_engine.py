"""
Persona Fusion Engine
RRT AIdvocAIte — Protective Layer of the Solidarity Framework

The mathematical core of the Protective Layer. Translates the user's specific
flavor of neurodivergent distress into a dynamic blend of the 5 OG personas,
weighted by the distress input type, crisis level, and TOI configuration.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple

from toi.toi_models import TOIConfig, ToneProfile
from .base_persona import BasePersona, PersonaContribution
from .ash import AshPersona
from .sol import SolPersona
from .echo import EchoPersona
from .kai import KaiPersona
from .myra import MyraPersona

logger = logging.getLogger(__name__)


class DistressInput(Enum):
    """
    Stage 2 Dialogue Tree inputs.
    Maps the user's self-reported distress type to persona blend weights.
    """
    EVERYTHING_HURTS_MELTDOWN = "everything_hurts_meltdown"
    CANT_DO_BASIC_TASKS = "cant_do_basic_tasks"
    CANT_STOP_SELF_BLAME = "cant_stop_self_blame"
    STUCK_IN_HYPERFOCUS_LOOP = "stuck_in_hyperfocus_loop"
    DONT_KNOW_SHUT_DOWN = "dont_know_shut_down"


@dataclass
class PersonaWeights:
    """
    Dynamic fusion weights for the 5 OG personas.
    All weights are floats in [0.0, 1.0] and must be normalized to sum to 1.0
    before use. A weight of 0.0 means the persona is silent in this blend.
    """
    ash: float = 0.2
    sol: float = 0.2
    echo: float = 0.2
    kai: float = 0.2
    myra: float = 0.2

    def normalize(self) -> "PersonaWeights":
        """Normalize weights to sum to 1.0."""
        total = self.ash + self.sol + self.echo + self.kai + self.myra
        if total <= 0.0:
            return PersonaWeights()
        factor = 1.0 / total
        return PersonaWeights(
            ash=round(self.ash * factor, 4),
            sol=round(self.sol * factor, 4),
            echo=round(self.echo * factor, 4),
            kai=round(self.kai * factor, 4),
            myra=round(self.myra * factor, 4),
        )

    def as_dict(self) -> Dict[str, float]:
        return {
            "ash": self.ash,
            "sol": self.sol,
            "echo": self.echo,
            "kai": self.kai,
            "myra": self.myra,
        }

    def dominant_persona(self) -> Tuple[str, float]:
        """Return the name and weight of the highest-weighted persona."""
        weights = self.as_dict()
        name = max(weights, key=lambda k: weights[k])
        return name, weights[name]

    def active_personas(self, threshold: float = 0.05) -> List[str]:
        """Return names of all personas with weight above the threshold."""
        return [name for name, w in self.as_dict().items() if w >= threshold]


# ============================================================================
# Stage 2 Distress Input → Persona Weight Map
# Handoff specification: each input maps to a canonical starting weight vector.
# ============================================================================

DISTRESS_WEIGHT_MAP: Dict[DistressInput, PersonaWeights] = {
    # "Everything hurts / Meltdown" → Heavily weight Ash + Myra
    DistressInput.EVERYTHING_HURTS_MELTDOWN: PersonaWeights(
        ash=0.45, myra=0.40, echo=0.10, sol=0.05, kai=0.00
    ),
    # "Can't do basic tasks" → Heavily weight Sol
    DistressInput.CANT_DO_BASIC_TASKS: PersonaWeights(
        sol=0.65, ash=0.20, myra=0.10, echo=0.05, kai=0.00
    ),
    # "Can't stop self-blame" → Heavily weight Echo
    DistressInput.CANT_STOP_SELF_BLAME: PersonaWeights(
        echo=0.55, ash=0.25, myra=0.15, sol=0.05, kai=0.00
    ),
    # "Stuck in hyperfocus/loop" → Heavily weight Kai
    DistressInput.STUCK_IN_HYPERFOCUS_LOOP: PersonaWeights(
        kai=0.65, sol=0.20, echo=0.10, ash=0.05, myra=0.00
    ),
    # "Don't know / Shut down" → Heavily weight Myra → triggers Silent Mode
    DistressInput.DONT_KNOW_SHUT_DOWN: PersonaWeights(
        myra=0.80, ash=0.15, echo=0.05, sol=0.00, kai=0.00
    ),
}


@dataclass
class EngineContext:
    """
    Runtime context passed to the FusionEngine for weight computation.
    Carries distress input, crisis level, session data, and user message.
    """
    user_message: str = ""
    distress_input: Optional[DistressInput] = None
    crisis_level_score: float = 0.0  # 0.0 (green) → 1.0 (black)
    silent_mode_active: bool = False
    session_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BlendedResponse:
    """
    The final output of the FusionEngine.

    Contains the blended system prompt for LLM use, a fallback template
    response for no-LLM operation, and the active persona weights used.
    """
    system_prompt: str
    template_response: str
    persona_weights: PersonaWeights
    dominant_persona: str
    active_personas: List[str]
    silent_mode_triggered: bool
    contributions: List[PersonaContribution] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FusionEngine:
    """
    Persona Fusion Engine.

    Translates distress inputs into dynamic persona blends and generates
    the LLM system prompt and fallback responses. Local-first by design —
    no external API calls are made in this layer.
    """

    # Crisis level score ranges → weight adjustment multiplier for Myra (anchor)
    _CRISIS_MYRA_BOOST = {
        (0.0, 0.2): 0.0,   # GREEN: no boost
        (0.2, 0.4): 0.05,  # YELLOW: slight Myra presence
        (0.4, 0.7): 0.10,  # ORANGE: moderate Myra anchor
        (0.7, 0.9): 0.15,  # RED: strong Myra anchor
        (0.9, 1.0): 0.20,  # BLACK: maximum Myra anchor
    }

    def __init__(self):
        self._personas: Dict[str, BasePersona] = {
            "ash": AshPersona(),
            "sol": SolPersona(),
            "echo": EchoPersona(),
            "kai": KaiPersona(),
            "myra": MyraPersona(),
        }

    def compute_weights(
        self,
        context: EngineContext,
        toi_config: TOIConfig,
    ) -> PersonaWeights:
        """
        Compute the persona blend weights for this interaction.

        Algorithm:
        1. Start from the canonical DISTRESS_WEIGHT_MAP entry (or uniform).
        2. Apply crisis-level Myra anchor boost.
        3. Apply TOI persona preferences and exclusions.
        4. Normalize to sum to 1.0.

        Args:
            context: The runtime EngineContext with distress input and crisis score.
            toi_config: The user's TOI configuration.

        Returns:
            Normalized PersonaWeights for this interaction.
        """
        # Step 1: Base weights from distress input
        if context.distress_input and context.distress_input in DISTRESS_WEIGHT_MAP:
            base = DISTRESS_WEIGHT_MAP[context.distress_input]
            weights = PersonaWeights(
                ash=base.ash,
                sol=base.sol,
                echo=base.echo,
                kai=base.kai,
                myra=base.myra,
            )
        else:
            # No explicit distress input — infer from crisis level
            weights = self._infer_weights_from_crisis(context.crisis_level_score)

        # Step 2: Crisis-level Myra anchor boost (co-regulation during high distress)
        myra_boost = self._get_myra_boost(context.crisis_level_score)
        if myra_boost > 0:
            weights.myra = min(1.0, weights.myra + myra_boost)

        # Step 3: Apply TOI persona preferences
        weights = self._apply_toi_preferences(weights, toi_config)

        # Step 4: Apply TOI persona exclusions (zero out excluded personas)
        weights = self._apply_toi_exclusions(weights, toi_config)

        # Normalize and return
        normalized = weights.normalize()
        logger.debug(
            "FusionEngine weights computed: %s (distress=%s, crisis_score=%.2f)",
            normalized.as_dict(),
            context.distress_input.value if context.distress_input else "none",
            context.crisis_level_score,
        )
        return normalized

    def _infer_weights_from_crisis(self, crisis_score: float) -> PersonaWeights:
        """Infer base weights when no explicit distress input is provided."""
        if crisis_score < 0.2:
            return PersonaWeights(ash=0.2, sol=0.2, echo=0.2, kai=0.2, myra=0.2)
        elif crisis_score < 0.4:
            return PersonaWeights(ash=0.3, sol=0.2, echo=0.2, kai=0.1, myra=0.2)
        elif crisis_score < 0.7:
            return PersonaWeights(ash=0.35, sol=0.15, echo=0.15, kai=0.05, myra=0.30)
        else:
            # High crisis: Ash + Myra anchor
            return PersonaWeights(ash=0.35, sol=0.05, echo=0.10, kai=0.00, myra=0.50)

    def _get_myra_boost(self, crisis_score: float) -> float:
        for (low, high), boost in self._CRISIS_MYRA_BOOST.items():
            if low <= crisis_score < high:
                return boost
        return 0.20  # Maximum boost at the very top

    def _apply_toi_preferences(
        self, weights: PersonaWeights, toi_config: TOIConfig
    ) -> PersonaWeights:
        """Boost preferred personas by 25%."""
        weights_dict = weights.as_dict()
        for persona_name in toi_config.preferred_personas:
            pname = persona_name.lower()
            if pname in weights_dict:
                weights_dict[pname] = min(1.0, weights_dict[pname] * 1.25)
        return PersonaWeights(**weights_dict)

    def _apply_toi_exclusions(
        self, weights: PersonaWeights, toi_config: TOIConfig
    ) -> PersonaWeights:
        """Zero out excluded personas."""
        weights_dict = weights.as_dict()
        for persona_name in toi_config.excluded_personas:
            pname = persona_name.lower()
            if pname in weights_dict:
                weights_dict[pname] = 0.0
        return PersonaWeights(**weights_dict)

    def blend_response(
        self,
        context: EngineContext,
        weights: PersonaWeights,
        toi_config: TOIConfig,
    ) -> BlendedResponse:
        """
        Generate the blended response from the computed persona weights.

        Produces:
        1. A unified LLM system prompt blending all active persona instructions.
        2. A fallback template response for no-LLM operation.
        3. Metadata for OTOI compliance tracking.

        Args:
            context: Runtime context including user message and session state.
            weights: Pre-computed, normalized PersonaWeights.
            toi_config: The user's TOI configuration.

        Returns:
            BlendedResponse with system prompt, template, and metadata.
        """
        silent_mode = context.silent_mode_active or toi_config.requires_silent_mode()

        # Check if this distress input triggers Silent Mode
        if context.distress_input == DistressInput.DONT_KNOW_SHUT_DOWN:
            silent_mode = True

        dominant_name, dominant_weight = weights.dominant_persona()
        active = weights.active_personas(threshold=0.05)

        # Generate contributions from each active persona
        contributions = []
        for persona_name in active:
            persona = self._personas.get(persona_name)
            if persona is None:
                continue
            contribution = persona.generate_contribution(
                weight=getattr(weights, persona_name),
                tone_profile=toi_config.tone_profile,
                silent_mode=silent_mode,
                context={"silent_mode_active": silent_mode, **context.session_context},
            )
            contributions.append(contribution)

        # Build the blended system prompt
        system_prompt = self._build_blended_system_prompt(
            contributions, weights, toi_config, silent_mode
        )

        # Build the fallback template response
        template_response = self._build_template_response(
            contributions, dominant_name, weights, silent_mode
        )

        return BlendedResponse(
            system_prompt=system_prompt,
            template_response=template_response,
            persona_weights=weights,
            dominant_persona=dominant_name,
            active_personas=active,
            silent_mode_triggered=silent_mode,
            contributions=contributions,
            metadata={
                "distress_input": context.distress_input.value if context.distress_input else None,
                "crisis_score": context.crisis_level_score,
                "tone_profile": toi_config.tone_profile.value,
            },
        )

    def _build_blended_system_prompt(
        self,
        contributions: List[PersonaContribution],
        weights: PersonaWeights,
        toi_config: TOIConfig,
        silent_mode: bool,
    ) -> str:
        """Build the unified LLM system prompt from all active persona contributions."""
        parts = []

        # OTOI preamble: establishes the governance contract
        parts.append(
            "You are the RRT AIdvocAIte — a composite presence formed from multiple "
            "personas, governed by the user's Terms of Interaction (TOI). "
            "The following persona instructions are weighted by urgency and relevance. "
            "You must honor all of them simultaneously, with the dominant persona "
            "leading the tone and content."
        )

        # Add each persona's prompt segment, weighted by contribution
        for contribution in contributions:
            if contribution.weight >= 0.05 and contribution.system_prompt_segment:
                prefix = f"\n[{contribution.persona_name.upper()} — weight: {contribution.weight:.2f}]\n"
                parts.append(prefix + contribution.system_prompt_segment)

        # TOI tone profile directive
        tone_directive = self._get_tone_directive(toi_config.tone_profile)
        parts.append(f"\n[TOI Tone Directive]\n{tone_directive}")

        # Anti-forced-productivity guard
        if not toi_config.allow_task_loops:
            parts.append(
                "\n[TOI Guard: NO TASK LOOPS] "
                "Do not push the user into a productivity loop. "
                "If they are showing burnout signals, rest is the only valid 'task'."
            )

        # Silent mode override
        if silent_mode:
            parts.append(
                "\n[SILENT MODE ACTIVE] "
                "Respond with minimal text only. No tasks, no timers, no urgency. "
                "Maximum 1-2 sentences. Pure presence."
            )

        return "\n".join(parts)

    def _build_template_response(
        self,
        contributions: List[PersonaContribution],
        dominant_name: str,
        weights: PersonaWeights,
        silent_mode: bool,
    ) -> str:
        """
        Build a fallback response from persona templates.
        Used when no LLM is configured — returns the dominant persona's template.
        """
        if silent_mode:
            myra = self._personas.get("myra")
            if myra:
                return myra.get_template_response(weights.myra, silent_mode=True)
            return "Here."

        dominant = self._personas.get(dominant_name)
        if dominant:
            return dominant.get_template_response(
                getattr(weights, dominant_name), silent_mode=False
            )

        return "I'm here with you."

    def _get_tone_directive(self, tone_profile: ToneProfile) -> str:
        directives = {
            ToneProfile.SUPPORTIVE_DEFAULT: (
                "Speak warmly and validate feelings before offering any content. "
                "Never start with advice."
            ),
            ToneProfile.MINIMAL: (
                "Use the absolute minimum number of words. 1-3 sentences max. "
                "No explanations. No qualifications."
            ),
            ToneProfile.DIRECTIVE: (
                "Be direct. Lead with the action. Eliminate ambiguity. "
                "One path, not multiple options."
            ),
            ToneProfile.THERAPEUTIC_REFLECTIVE: (
                "Mirror. Reflect. Ask soft questions. Create space. "
                "Never prescribe. Never push toward solutions."
            ),
        }
        return directives.get(tone_profile, directives[ToneProfile.SUPPORTIVE_DEFAULT])

    def infer_distress_input_from_text(self, text: str) -> Optional[DistressInput]:
        """
        Heuristically infer the DistressInput category from free-form text.
        Used as a fallback when the user doesn't select from the Stage 2 menu.
        """
        text_lower = text.lower()
        for persona_name, persona in self._personas.items():
            if persona.matches_activation_signal(text_lower):
                signal_to_distress = {
                    "ash": DistressInput.EVERYTHING_HURTS_MELTDOWN,
                    "sol": DistressInput.CANT_DO_BASIC_TASKS,
                    "echo": DistressInput.CANT_STOP_SELF_BLAME,
                    "kai": DistressInput.STUCK_IN_HYPERFOCUS_LOOP,
                    "myra": DistressInput.DONT_KNOW_SHUT_DOWN,
                }
                inferred = signal_to_distress.get(persona_name)
                if inferred:
                    logger.debug(
                        "Inferred distress input '%s' from persona signal match on '%s'",
                        inferred.value, persona_name,
                    )
                    return inferred
        return None
