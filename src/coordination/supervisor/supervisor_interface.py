"""
Supervisor Interface
Coordination layer for NeuroLift Supervisor AI integration.

Provides the interface contract for external supervisor AI systems
to interact with the RRT AIdvocAIte. Implements a local no-op default
that logs all events locally (privacy-first).
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SupervisorInterface(ABC):
    """Abstract interface for Supervisor AI coordination."""

    @abstractmethod
    async def notify_advocate_status(
        self, advocate_id: str, status: str, user_id: str
    ) -> None:
        """Notify the supervisor of advocate status changes."""
        ...

    @abstractmethod
    async def handle_crisis(
        self, advocate_id: str, crisis_assessment: Any, user_id: str
    ) -> None:
        """Notify the supervisor of a detected crisis."""
        ...

    @abstractmethod
    async def emergency_escalation(
        self, advocate_id: str, crisis_assessment: Any, user_id: str
    ) -> None:
        """Trigger emergency escalation protocols."""
        ...


class LocalSupervisor(SupervisorInterface):
    """
    Local no-op supervisor that logs all events locally.

    Default implementation when no external supervisor is configured.
    Privacy-first: no data leaves the device.
    """

    async def notify_advocate_status(
        self, advocate_id: str, status: str, user_id: str
    ) -> None:
        logger.info("[LocalSupervisor] %s: advocate=%s status=%s", user_id, advocate_id, status)

    async def handle_crisis(
        self, advocate_id: str, crisis_assessment: Any, user_id: str
    ) -> None:
        level = getattr(getattr(crisis_assessment, "crisis_level", None), "value", "unknown")
        logger.warning(
            "[LocalSupervisor] Crisis: user=%s advocate=%s level=%s confidence=%.2f",
            user_id,
            advocate_id,
            level,
            getattr(crisis_assessment, "confidence_score", 0.0),
        )

    async def emergency_escalation(
        self, advocate_id: str, crisis_assessment: Any, user_id: str
    ) -> None:
        logger.critical(
            "[LocalSupervisor] EMERGENCY ESCALATION: user=%s advocate=%s",
            user_id,
            advocate_id,
        )
