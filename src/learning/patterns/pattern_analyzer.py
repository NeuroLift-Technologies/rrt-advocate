"""
Pattern Analyzer
Local-first session pattern tracking for adaptive support.

Stores all data locally in JSON format. No cloud sync.
Privacy-first: raw message content is never stored — only aggregated metrics.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """
    Tracks crisis patterns and intervention effectiveness across sessions.

    All data is stored locally in a JSON file per user.
    Privacy guarantee: only aggregated metrics are stored, never raw text.
    """

    def __init__(
        self,
        user_id: str,
        storage_dir: str = "data/patterns",
    ):
        self.user_id = user_id
        self.storage_dir = storage_dir
        self._patterns: Dict[str, Any] = self._load_patterns()

    def _get_storage_path(self) -> str:
        return os.path.join(self.storage_dir, f"{self.user_id}_patterns.json")

    def _load_patterns(self) -> Dict[str, Any]:
        path = self._get_storage_path()
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load patterns for %s: %s", self.user_id, e)
        return {
            "user_id": self.user_id,
            "session_count": 0,
            "total_crisis_events": 0,
            "crisis_level_distribution": {},
            "most_common_distress_inputs": {},
            "most_effective_interventions": {},
            "persona_usage_distribution": {},
            "sessions": [],
        }

    async def update_patterns(self, assessment: Any):
        """
        Update stored patterns with data from a new crisis assessment.

        Args:
            assessment: CrisisAssessment from the assessor.
        """
        level = getattr(getattr(assessment, "crisis_level", None), "value", "unknown")
        dist = self._patterns.setdefault("crisis_level_distribution", {})
        dist[level] = dist.get(level, 0) + 1
        self._patterns["total_crisis_events"] += 1

    async def save_patterns(self):
        """Persist the current patterns to local storage."""
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
            path = self._get_storage_path()
            self._patterns["last_saved"] = datetime.now().isoformat()
            with open(path, "w") as f:
                json.dump(self._patterns, f, indent=2)
            logger.info("Patterns saved for user %s", self.user_id)
        except IOError as e:
            logger.error("Failed to save patterns for %s: %s", self.user_id, e)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "session_count": self._patterns.get("session_count", 0),
            "total_crisis_events": self._patterns.get("total_crisis_events", 0),
            "crisis_level_distribution": self._patterns.get("crisis_level_distribution", {}),
        }
