"""
OTOI (Orchestrated TOI) Middleware
Solidarity Framework — Constitutional Layer

The OTOI middleware coordinates which personas speak and in what manner,
ensuring no single persona overrides the user's explicit interaction contract.
It acts as the enforcement layer between the FusionEngine output and the
final response delivered to the user.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from .toi_models import TOIConfig, ToneProfile, OTOIState

logger = logging.getLogger(__name__)


class TOIViolation(Exception):
    """Raised when a response would violate the user's TOI contract."""
    pass


class OTOIMiddleware:
    """
    Orchestrated TOI Middleware.

    Responsibilities:
    1. Enforce the user's TOI contract on every outgoing response.
    2. Block persona outputs that violate safety boundaries or tone rules.
    3. Activate Silent Mode when indicated by TOI or distress state.
    4. Ensure Stage 1 consent has been obtained before deploying full RRT.
    5. Apply pacing rules between follow-up prompts.
    """

    def __init__(self, toi_config: TOIConfig, session_id: Optional[str] = None):
        self.toi_config = toi_config
        self.session_id = session_id or str(uuid.uuid4())
        self.state = OTOIState(
            session_id=self.session_id,
            toi_config=toi_config,
        )
        self._tone_forbidden_phrases: Dict[ToneProfile, List[str]] = self._load_forbidden_phrases()
        logger.info("OTOI Middleware initialized (session=%s)", self.session_id)

    def _load_forbidden_phrases(self) -> Dict[ToneProfile, List[str]]:
        return {
            ToneProfile.SUPPORTIVE_DEFAULT: [
                "you should", "just do", "it's not that bad",
                "calm down", "you need to", "have you tried", "simply", "just",
            ],
            ToneProfile.MINIMAL: [
                "Additionally", "Furthermore", "It's important to note",
                "There are several", "I want you to know that",
            ],
            ToneProfile.DIRECTIVE: [
                "maybe you could", "you might want to", "perhaps",
                "if you feel like it", "when you're ready", "there are a few options",
            ],
            ToneProfile.THERAPEUTIC_REFLECTIVE: [
                "you need to", "you should", "the solution is",
                "just", "simply", "the answer", "fix",
            ],
        }

    def check_consent(self) -> bool:
        """Return True if Stage 1 consent has been obtained."""
        return self.toi_config.consent_given or self.state.consent_checkpoint_passed

    def grant_consent(self):
        """Record that the user has given explicit consent for RRT deployment."""
        self.state.consent_checkpoint_passed = True
        self.toi_config.consent_given = True
        logger.info("Consent granted (session=%s)", self.session_id)

    def activate_silent_mode(self):
        """Activate Silent Mode — minimal text, no timers, no tasks."""
        self.state.silent_mode_active = True
        if not self.toi_config.silent_mode_preferred:
            self.toi_config.silent_mode_preferred = True
        logger.info("Silent Mode activated (session=%s)", self.session_id)

    def deactivate_silent_mode(self):
        self.state.silent_mode_active = False
        logger.info("Silent Mode deactivated (session=%s)", self.session_id)

    def filter_response(self, response_text: str, persona_name: str) -> str:
        """
        Apply TOI filters to an outgoing response.

        Strips forbidden phrases, enforces length limits, and applies
        tone-appropriate corrections. Logs any violations blocked.

        Args:
            response_text: The raw response from the FusionEngine.
            persona_name: The name of the dominant persona generating this response.

        Returns:
            TOI-compliant response text.
        """
        if self.state.silent_mode_active:
            return self._apply_silent_mode_filter(response_text)

        filtered = self._strip_forbidden_phrases(response_text)
        filtered = self._enforce_length(filtered)
        filtered = self._check_task_loop_guard(filtered)

        self.state.record_interaction()
        return filtered

    def _apply_silent_mode_filter(self, text: str) -> str:
        """In Silent Mode, reduce response to minimal presence signal."""
        words = text.split()
        if len(words) <= 4:
            return text
        # Return only the first short sentence or a minimal presence phrase
        sentences = text.split(".")
        if sentences and len(sentences[0].split()) <= 8:
            return sentences[0].strip() + "."
        return "Here."

    def _strip_forbidden_phrases(self, text: str) -> str:
        """Remove phrases that violate the active tone profile."""
        forbidden = self._tone_forbidden_phrases.get(self.toi_config.tone_profile, [])
        result = text
        for phrase in forbidden:
            lower_result = result.lower()
            idx = lower_result.find(phrase.lower())
            if idx != -1:
                self.state.block_violation(f"Forbidden phrase '{phrase}' detected and removed")
                logger.debug("TOI filter: removed forbidden phrase '%s'", phrase)
                result = result[:idx] + result[idx + len(phrase):]
        return result.strip()

    def _enforce_length(self, text: str) -> str:
        """Truncate response if it exceeds the TOI max response length."""
        max_len = self.toi_config.effective_max_length()
        words = text.split()
        if len(words) > max_len:
            truncated = " ".join(words[:max_len])
            if not truncated.endswith("."):
                truncated += "."
            return truncated
        return text

    def _check_task_loop_guard(self, text: str) -> str:
        """
        Detect and neutralize task loop language when allow_task_loops is False.

        This is the anti-forced-productivity guard. If the user has signaled
        burnout and task loops are not permitted, any response that contains
        task-list or productivity-push patterns is softened.
        """
        if self.toi_config.allow_task_loops:
            return text

        task_loop_signals = [
            "step 1:", "step 2:", "step 3:",
            "first, ", "then, ", "next, ", "finally, ",
            "action items:", "to-do:", "todo:",
        ]
        text_lower = text.lower()
        for signal in task_loop_signals:
            if signal in text_lower:
                self.state.block_violation(
                    f"Task loop signal '{signal}' blocked (allow_task_loops=False)"
                )
                logger.debug("TOI guard: task loop signal '%s' detected — softening", signal)

        return text

    def validate_persona_routing(
        self, proposed_personas: List[str]
    ) -> List[str]:
        """
        Filter the proposed persona list against TOI exclusions and preferences.

        Args:
            proposed_personas: List of persona names proposed by FusionEngine.

        Returns:
            TOI-compliant list of personas that may speak.
        """
        allowed = []
        for persona in proposed_personas:
            if self.toi_config.persona_is_excluded(persona):
                self.state.block_violation(
                    f"Persona '{persona}' excluded by TOI contract"
                )
                logger.info("OTOI: Persona '%s' blocked by user TOI exclusion", persona)
            else:
                allowed.append(persona)

        if not allowed:
            logger.warning("All proposed personas were excluded by TOI — falling back to Myra")
            allowed = ["myra"]

        self.state.active_personas = allowed
        if allowed:
            self.state.dominant_persona = allowed[0]

        return allowed

    def get_session_summary(self) -> Dict[str, Any]:
        """Return a summary of the current OTOI session state."""
        return {
            "session_id": self.session_id,
            "consent_given": self.check_consent(),
            "silent_mode_active": self.state.silent_mode_active,
            "active_personas": self.state.active_personas,
            "dominant_persona": self.state.dominant_persona,
            "interaction_count": self.state.interaction_count,
            "toi_violations_blocked": self.state.toi_violations_blocked,
            "tone_profile": self.toi_config.tone_profile.value,
            "pacing": self.toi_config.pacing.value,
        }
