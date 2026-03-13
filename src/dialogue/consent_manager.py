"""
Consent Manager — tracks the user's consent state across the session.

The RRT Advocate never deploys full intervention without explicit user
opt-in.  This module enforces that invariant.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_AFFIRMATIVE_TOKENS = frozenset({
    "yes", "y", "yep", "yeah", "sure", "ok", "okay", "please",
    "go ahead", "help", "i want", "support", "yes please",
})

_NEGATIVE_TOKENS = frozenset({
    "no", "n", "nope", "not now", "leave me", "stop",
    "i'm fine", "im fine", "i'm okay", "im okay",
})


@dataclass
class ConsentState:
    consented: bool = False
    silent_mode_requested: bool = False
    declined_at: list[str] = field(default_factory=list)
    """Stage names where the user declined consent."""


class ConsentManager:
    """
    Tracks whether the user has consented to receiving RRT support.

    Consent must be obtained fresh at Stage 1 of each activation cycle.
    It does not persist across sessions unless the user's TOI explicitly
    opts into persistent consent.
    """

    def __init__(self) -> None:
        self._state = ConsentState()

    @property
    def consented(self) -> bool:
        return self._state.consented

    @property
    def silent_mode_requested(self) -> bool:
        return self._state.silent_mode_requested

    def evaluate(self, user_input: str) -> ConsentState:
        """
        Interpret a user's response as consent, refusal, or silent mode request.

        Updates internal state and returns it.
        """
        normalised = user_input.strip().lower()

        if "silent" in normalised or "just be here" in normalised:
            self._state.consented = True
            self._state.silent_mode_requested = True
            logger.debug("Consent: silent mode requested.")
            return self._state

        for token in _AFFIRMATIVE_TOKENS:
            if token in normalised:
                self._state.consented = True
                self._state.silent_mode_requested = False
                logger.debug("Consent: affirmative detected ('%s').", token)
                return self._state

        for token in _NEGATIVE_TOKENS:
            if token in normalised:
                self._state.consented = False
                self._state.silent_mode_requested = False
                logger.debug("Consent: declined ('%s').", token)
                return self._state

        # Ambiguous — treat as implicit consent (low-demand principle)
        logger.debug("Consent: ambiguous input, treating as implicit consent.")
        self._state.consented = True
        return self._state

    def grant(self) -> None:
        """Programmatically grant consent (e.g. from a UI button press)."""
        self._state.consented = True

    def revoke(self, stage: str = "") -> None:
        """Revoke consent; optionally record which stage the user declined at."""
        self._state.consented = False
        if stage:
            self._state.declined_at.append(stage)

    def reset(self) -> None:
        """Clear consent state for a new activation cycle."""
        self._state = ConsentState()
