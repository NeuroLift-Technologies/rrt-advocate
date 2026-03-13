"""
Consent Manager — Agency-First consent tracking.

The system must pause and ask for consent (Stage 1 Entry Prompt)
before deploying the full RRT Advocate.  This module tracks and
enforces that requirement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ConsentState(Enum):
    NOT_ASKED = "not_asked"
    PENDING = "pending"
    GRANTED = "granted"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"


@dataclass
class ConsentRecord:
    state: ConsentState = ConsentState.NOT_ASKED
    granted_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None


class ConsentManager:
    """
    Tracks per-session consent for the RRT Advocate to engage.

    The Advocate MUST NOT deploy crisis responses beyond Stage 0
    (passive observation) until consent is granted.
    """

    def __init__(self) -> None:
        self._record = ConsentRecord()

    @property
    def state(self) -> ConsentState:
        return self._record.state

    @property
    def is_granted(self) -> bool:
        return self._record.state == ConsentState.GRANTED

    def request_consent(self) -> str:
        """
        Move to PENDING and return the Stage 1 Entry Prompt text.
        """
        self._record.state = ConsentState.PENDING
        return (
            "I noticed you might be having a tough time. "
            "Would you like some support right now? "
            "You're in control — just say the word and I'm here. "
            "If not, that's completely okay too."
        )

    def grant(self) -> None:
        self._record.state = ConsentState.GRANTED
        self._record.granted_at = datetime.now()

    def decline(self) -> None:
        self._record.state = ConsentState.DECLINED
        self._record.declined_at = datetime.now()

    def withdraw(self) -> None:
        self._record.state = ConsentState.WITHDRAWN
        self._record.withdrawn_at = datetime.now()

    def reset(self) -> None:
        self._record = ConsentRecord()
