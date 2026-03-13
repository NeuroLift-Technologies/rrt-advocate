"""
Stage 1 Entry - Agency-First Consent Prompt

The RRT Advocate MUST NOT deploy until the user explicitly consents.
This module provides the Stage 1 Entry Prompt that pauses and asks for consent
before activating the full RRT Advocate response.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Stage1EntryResult:
    """Result of Stage 1 consent flow"""
    consent_granted: bool
    user_response: Optional[str] = None
    session_id: Optional[str] = None


# Default Stage 1 Entry Prompt - low-demand, non-pushy, agency-respecting
STAGE1_ENTRY_PROMPT = """
I notice you might be having a rough moment. I'm here if you'd like support.

You don't have to respond. You can:
- Say "yes" or "I'd like help" to get gentle support
- Stay silent—that's okay too
- Say "not now" or "no" and I'll step back

No pressure. You're in charge here.
"""

# Minimal variant - lowest cognitive load
STAGE1_ENTRY_MINIMAL = """
Rough moment? I'm here if you want support. Say "yes" or "no"—or nothing. Your choice.
"""

# Supportive variant - warmer, more validating
STAGE1_ENTRY_SUPPORTIVE = """
It sounds like things might feel heavy right now. I'm the RRT Advocate, and I'm here to offer support when you're ready.

There's no right or wrong way to respond. If you'd like gentle support, just say so. If you'd prefer space, that's completely valid too. You know what you need best.
"""


class Stage1EntryHandler:
    """
    Handles the Stage 1 consent gate before RRT Advocate activation.
    
    NLT Ethos: Agency First - The system must pause and ask for consent
    before deploying the full RRT Advocate.
    """

    def __init__(self, tone_variant: str = "default"):
        """
        Args:
            tone_variant: "default" | "minimal" | "supportive"
        """
        self.tone_variant = tone_variant

    def get_entry_prompt(self) -> str:
        """Return the appropriate Stage 1 prompt based on TOI tone preference."""
        prompts = {
            "minimal": STAGE1_ENTRY_MINIMAL,
            "minimal_tone": STAGE1_ENTRY_MINIMAL,
            "default": STAGE1_ENTRY_PROMPT,
            "supportive": STAGE1_ENTRY_SUPPORTIVE,
            "supportive_default": STAGE1_ENTRY_PROMPT,
            "directive": STAGE1_ENTRY_PROMPT,
            "therapeutic_reflective": STAGE1_ENTRY_SUPPORTIVE,
        }
        return prompts.get(self.tone_variant, STAGE1_ENTRY_PROMPT).strip()

    def parse_consent(self, user_response: str) -> Stage1EntryResult:
        """
        Parse user response to determine if consent was granted.
        
        Uses non-judgmental, shame-resistant interpretation:
        - Affirmative: "yes", "ok", "sure", "help", "please", etc.
        - Decline: "no", "not now", "later", "stop", etc.
        - Ambiguous/silence: Treated as no consent (fail-safe)
        """
        if not user_response or not user_response.strip():
            return Stage1EntryResult(consent_granted=False, user_response=user_response)

        normalized = user_response.strip().lower()

        # Affirmative patterns - user wants support
        affirmative = [
            "yes", "yeah", "yep", "ok", "okay", "sure", "please", "help",
            "i'd like help", "i want help", "i need support", "support",
            "yes please", "go ahead", "continue", "show me"
        ]
        for a in affirmative:
            if a in normalized or normalized.startswith(a):
                return Stage1EntryResult(consent_granted=True, user_response=user_response)

        # Explicit decline
        decline = [
            "no", "nope", "not now", "later", "stop", "don't", "leave",
            "i'm fine", "i'm ok", "pass", "maybe later"
        ]
        for d in decline:
            if d in normalized or normalized.startswith(d):
                return Stage1EntryResult(consent_granted=False, user_response=user_response)

        # Default: no consent when ambiguous (agency-first, never assume)
        return Stage1EntryResult(consent_granted=False, user_response=user_response)
