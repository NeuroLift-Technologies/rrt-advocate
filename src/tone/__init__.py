"""
Tone Profiles Module - RRT AIdvocAIte
Configurable tone profiles as dictated by user's TOI (Terms of Interaction).

Provides modular prompt engineering for 4 distinct tones:
- Supportive Default: Warm, validating
- Minimal Tone: Extremely concise, lowest cognitive load
- Directive Tone: Clear, action-oriented (Sol/Kai)
- Therapeutic/Reflective: Empathetic mirroring, soft Socratic (Ash/Echo)
"""

from .tone_profiles import ToneProfile, get_tone_profile
from .prompt_builder import PromptBuilder

__all__ = [
    "ToneProfile",
    "get_tone_profile",
    "PromptBuilder",
]
