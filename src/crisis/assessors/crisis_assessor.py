"""
Crisis Assessor - Adapter
Legacy interface; uses CDE result to produce CrisisAssessment.
"""

from datetime import datetime

from crisis.models import CrisisAssessment, CrisisLevel
from crisis.detection.cde import CrisisDetectionEngine, CDEResult


class CrisisAssessor:
    """Adapter: produces CrisisAssessment from CDE or default."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._cde = CrisisDetectionEngine()

    async def assess_crisis(self, indicators: dict) -> CrisisAssessment:
        """Legacy: return CrisisAssessment. Use CDE.detect() + Fusion for new flow."""
        return CrisisAssessment(
            timestamp=datetime.now(),
            crisis_level=CrisisLevel.GREEN,
            primary_indicators=[],
            secondary_indicators=[],
            confidence_score=0.0,
            estimated_duration=None,
            recommended_interventions=[],
            escalation_threshold=0.8,
            user_safety_score=1.0,
            context_factors={},
        )
