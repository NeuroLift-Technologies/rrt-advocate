"""
TOI Parser — middleware that validates and enforces the user's Terms of
Interaction on every outbound response.

The parser sits between the Persona Fusion Engine's raw output and the
final message delivered to the user.  It truncates, reformats, or blocks
content that violates the active TOI contract.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from .toi_config import (
    TOIConfig,
    TonePreference,
    PacingPreference,
    CognitiveScaffoldingLevel,
    SafetyBoundary,
)

logger = logging.getLogger(__name__)


@dataclass
class TOIFilterResult:
    """Outcome of filtering a response through the TOI."""
    original_text: str
    filtered_text: str
    modifications: List[str]
    blocked: bool = False
    block_reason: Optional[str] = None


class TOIParser:
    """
    Stateless middleware that enforces the active TOI on response content.
    """

    PRODUCTIVITY_KEYWORDS = frozenset({
        "productive", "productivity", "hustle", "grind", "optimize your time",
        "you should be", "just do it", "try harder", "push through",
        "no excuses", "be more efficient", "time is wasting",
    })

    TIMER_KEYWORDS = frozenset({
        "set a timer", "start a timer", "countdown", "pomodoro",
        "time yourself", "stopwatch",
    })

    TASK_LIST_KEYWORDS = frozenset({
        "to-do list", "todo list", "task list", "checklist",
        "action items", "step-by-step plan",
    })

    ADVICE_STARTERS = (
        "you should", "you need to", "you must", "you have to",
        "why don't you", "why not just",
    )

    def __init__(self, toi: TOIConfig) -> None:
        self.toi = toi

    def filter_response(self, text: str) -> TOIFilterResult:
        modifications: List[str] = []
        filtered = text

        if self.toi.boundary_active(SafetyBoundary.NO_PRODUCTIVITY_FRAMING):
            filtered, mod = self._strip_phrases(filtered, self.PRODUCTIVITY_KEYWORDS)
            if mod:
                modifications.append("removed_productivity_framing")

        if self.toi.boundary_active(SafetyBoundary.NO_TIMERS):
            filtered, mod = self._strip_phrases(filtered, self.TIMER_KEYWORDS)
            if mod:
                modifications.append("removed_timer_references")

        if self.toi.boundary_active(SafetyBoundary.NO_TASK_LISTS):
            filtered, mod = self._strip_phrases(filtered, self.TASK_LIST_KEYWORDS)
            if mod:
                modifications.append("removed_task_list_references")

        if self.toi.boundary_active(SafetyBoundary.NO_UNSOLICITED_ADVICE):
            filtered, mod = self._soften_advice(filtered)
            if mod:
                modifications.append("softened_unsolicited_advice")

        if self.toi.boundary_active(SafetyBoundary.SILENT_MODE_ONLY):
            return TOIFilterResult(
                original_text=text,
                filtered_text="",
                modifications=["silent_mode_active"],
                blocked=True,
                block_reason="User TOI requests silent mode only",
            )

        if self.toi.max_message_length and len(filtered) > self.toi.max_message_length:
            filtered = filtered[: self.toi.max_message_length].rsplit(" ", 1)[0] + "…"
            modifications.append("truncated_to_max_length")

        return TOIFilterResult(
            original_text=text,
            filtered_text=filtered.strip(),
            modifications=modifications,
        )

    def validate_persona_access(self, persona_id: str) -> bool:
        return self.toi.persona_allowed(persona_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_phrases(text: str, phrases: frozenset) -> tuple[str, bool]:
        modified = False
        lower = text.lower()
        for phrase in phrases:
            if phrase in lower:
                idx = lower.find(phrase)
                text = text[:idx] + text[idx + len(phrase):]
                lower = text.lower()
                modified = True
        return text, modified

    @staticmethod
    def _soften_advice(text: str) -> tuple[str, bool]:
        modified = False
        lower = text.lower()
        replacements = {
            "you should": "one option might be to",
            "you need to": "it could help to",
            "you must": "when you feel ready, you could",
            "you have to": "something that sometimes helps is to",
            "why don't you": "if it feels right, you might",
            "why not just": "whenever you're ready, perhaps",
        }
        for old, new in replacements.items():
            if old in lower:
                start = lower.find(old)
                text = text[:start] + new + text[start + len(old):]
                lower = text.lower()
                modified = True
        return text, modified
