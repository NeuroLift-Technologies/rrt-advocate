"""
Supervisor Interface - Stub
Full implementation in NeuroLift ecosystem integration phase.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class CrisisAssessment:
    """Minimal crisis assessment for supervisor notification."""
    crisis_level: str
    confidence_score: float
    context_factors: Dict[str, Any]
    timestamp: str


class SupervisorInterface:
    """
    Interface to NeuroLift Supervisor AI.
    Stub: methods no-op when no supervisor is configured.
    """

    async def handle_crisis(
        self,
        advocate_id: str,
        crisis_assessment: Any,
        user_id: str,
    ) -> None:
        """Handle crisis escalation from RRT Advocate."""
        pass

    async def emergency_escalation(
        self,
        advocate_id: str,
        crisis_assessment: Any,
        user_id: str,
    ) -> None:
        """Handle emergency-level crisis escalation."""
        pass

    async def notify_advocate_status(
        self,
        advocate_id: str,
        status: str,
        user_id: str,
    ) -> None:
        """Notify supervisor of advocate status changes."""
        pass
