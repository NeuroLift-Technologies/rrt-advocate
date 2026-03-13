"""Shared crisis models."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class CrisisLevel(Enum):
    """Crisis severity levels for response coordination."""
    GREEN = "stable"
    YELLOW = "elevated"
    ORANGE = "high"
    RED = "critical"
    BLACK = "emergency"


@dataclass
class CrisisAssessment:
    """Comprehensive crisis assessment data structure."""
    timestamp: datetime
    crisis_level: CrisisLevel
    primary_indicators: List[str]
    secondary_indicators: List[str]
    confidence_score: float
    estimated_duration: Optional[timedelta]
    recommended_interventions: List[str]
    escalation_threshold: float
    user_safety_score: float
    context_factors: Dict[str, Any] = field(default_factory=dict)
