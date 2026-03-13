"""
Crisis Detector - Adapter to new CDE
Legacy interface; delegates to CrisisDetectionEngine.
"""

from pathlib import Path
from typing import List

# Use CDE from same package tree
try:
    from crisis.detection.cde import CrisisDetectionEngine, CDEResult
except ImportError:
    try:
        from ..detection.cde import CrisisDetectionEngine, CDEResult
    except ImportError:
        CrisisDetectionEngine = None  # type: ignore
        CDEResult = None  # type: ignore


class CrisisDetector:
    """Adapter: wraps CDE for legacy CrisisDetector interface."""

    def __init__(self, config_path: str = "config/crisis_thresholds.yaml"):
        self.config_path = config_path
        self._cde = CrisisDetectionEngine() if CrisisDetectionEngine else None

    async def detect_crisis_indicators(self) -> dict:
        """Legacy: return minimal indicators. Use CDE.detect() for full pipeline."""
        return {"indicators": [], "cde_available": True}
