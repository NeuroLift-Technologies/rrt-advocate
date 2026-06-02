"""
Base Persona — Abstract foundation for all 5 OGs.
"""
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from toi.toi_models import ToneProfile


@dataclass
class PersonaContribution:
    """
    The output of a single persona's contribution to a blended response.

    Each persona generates a contribution weighted by its fusion score.
    The FusionEngine combines these into the final BlendedResponse.
    """
    persona_name: str
    weight: float
    response_fragment: str
    system_prompt_segment: str
    template_category: str  # "low_weight" | "high_weight" | "silent_mode"
    metadata: Dict[str, Any] = field(default_factory=dict)


class BasePersona(ABC):
    """
    Abstract base class for all RRT AIdvocAIte personas.

    Each persona must implement:
    - `build_system_prompt()`: Returns its segment of the LLM system prompt.
    - `get_template_response()`: Returns a fallback template when no LLM is available.
    """

    name: str
    full_name: str
    role: str
    silence_compatible: bool = False
    silent_mode_trigger: bool = False

    def __init__(self):
        self._template_responses: Dict[str, List[str]] = {}
        self._activation_signals: List[str] = []
        self._system_prompt_prefix: str = ""

    @abstractmethod
    def build_system_prompt(
        self,
        weight: float,
        tone_profile: ToneProfile,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build this persona's contribution to the LLM system prompt.

        Args:
            weight: This persona's current fusion weight (0.0–1.0).
            tone_profile: The active tone profile from the user's TOI.
            context: Optional session context.

        Returns:
            A system prompt segment for this persona.
        """
        ...

    def get_template_response(
        self,
        weight: float,
        silent_mode: bool = False,
    ) -> str:
        """
        Return a fallback template response when no LLM is configured.

        Selects from high_weight or low_weight pools based on the fusion weight.
        """
        if silent_mode and "silent_mode" in self._template_responses:
            pool = self._template_responses["silent_mode"]
        elif weight >= 0.4 and "high_weight" in self._template_responses:
            pool = self._template_responses["high_weight"]
        else:
            pool = self._template_responses.get("low_weight", ["I'm here."])
        return random.choice(pool)

    def generate_contribution(
        self,
        weight: float,
        tone_profile: ToneProfile,
        silent_mode: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> PersonaContribution:
        """
        Generate this persona's contribution to the blended response.

        Returns a PersonaContribution with both the system prompt segment
        and a template response (used when no LLM is available).
        """
        category = "silent_mode" if silent_mode else ("high_weight" if weight >= 0.4 else "low_weight")
        return PersonaContribution(
            persona_name=self.name,
            weight=weight,
            response_fragment=self.get_template_response(weight, silent_mode),
            system_prompt_segment=self.build_system_prompt(weight, tone_profile, context),
            template_category=category,
        )

    def matches_activation_signal(self, text: str) -> bool:
        """Return True if the input text contains any of this persona's activation signals."""
        text_lower = text.lower()
        return any(signal.lower() in text_lower for signal in self._activation_signals)
