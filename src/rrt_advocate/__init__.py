"""``rrt_advocate`` - Python port of the RRT Advocate **Crisis Detection Engine
(CDE)**: a 3-layer, local-first crisis detection and assessment pipeline from
the NeuroLift HAIEF Solidarity Framework.

This package is a faithful port of ``@neurolift-technologies/rrt-advocate`` (the
TypeScript CDE), preserving every layer weight, threshold, and confidence
formula. **Crisis thresholds are safety-critical** - the bundled
``config/crisis_thresholds.yaml`` is a vendored copy of the canonical file and
must stay in sync with it.

Scope: this package ports the **detection & assessment engine** only. The
persona/dialogue/intervention *response* layers remain canonical elsewhere.

⚠️ PROTOTYPE - NOT A SAFETY SYSTEM. This is an experimental crisis-detection
library with stubbed/placeholder intervention layers. It is **NOT medical
advice, NOT a crisis service**, and performs **no real-time monitoring**. It
**can miss real crisis signals** - do not rely on it as a safety net or as the
sole safety mechanism. Provided **AS-IS, without warranty**. If you or someone
else needs help now: in the US, call or text **988** (Suicide & Crisis
Lifeline) or chat https://988lifeline.org; in an emergency call **911**. Outside
the US: https://findahelpline.com.

Example::

    from rrt_advocate import CrisisEngine, CrisisLevel

    engine = CrisisEngine("user-123")
    assessment = engine.assess("I can't cope, everything is too much")
    if assessment.crisis_level is not CrisisLevel.GREEN:
        ...  # route to appropriate support
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from .behavioral_layer import BehavioralLayer
from .crisis_assessor import CrisisAssessor
from .crisis_detector import CrisisDetector, CrisisIndicators
from .keyword_layer import KeywordLayer
from .sentiment_layer import PolarityAnalyzer, SentimentLayer, _AUTO
from .types import (
    BehavioralAnalysisResult,
    BehavioralMetrics,
    ComplexityTrend,
    CrisisAssessment,
    CrisisLevel,
    KeywordAnalysisResult,
    KeywordMatch,
    KeywordSemanticField,
    SentimentAnalysisResult,
    SentimentReading,
    SentimentTrend,
)

__version__ = "0.1.1"


class CrisisEngine:
    """Convenience facade that wires the :class:`CrisisDetector` and
    :class:`CrisisAssessor` together, mirroring the canonical Python
    ``RRTAdvocate.assess_current_state`` path: detect indicators, then assess.

    This is the detection/assessment surface only - it does not generate
    persona-blended responses or interventions.
    """

    def __init__(
        self,
        user_id: str,
        config_path: Optional[str] = None,
        sentiment_analyzer: object = _AUTO,
    ) -> None:
        """:param user_id: Stable, pseudonymous user identifier.
        :param config_path: Path to a ``crisis_thresholds.yaml``. Defaults to the
            bundled copy.
        :param sentiment_analyzer: Optional VADER-compatible analyzer for Layer 2.
            When omitted, Layer 2 auto-detects ``vaderSentiment`` and otherwise uses
            its heuristic fallback. Pass ``None`` to force the heuristic fallback.
        """
        self._detector = CrisisDetector(sentiment_analyzer=sentiment_analyzer)
        self._assessor = CrisisAssessor(user_id, config_path)

    def detect(
        self, message: str = "", timestamp: Optional[datetime] = None
    ) -> CrisisIndicators:
        """Run the full 3-layer detection on a message and return raw indicators."""
        return self._detector.detect_crisis_indicators(message, timestamp)

    def assess(
        self, message: str = "", timestamp: Optional[datetime] = None
    ) -> CrisisAssessment:
        """Detect and assess a single message, returning a :class:`CrisisAssessment`."""
        indicators = self._detector.detect_crisis_indicators(message, timestamp)
        return self._assessor.assess_crisis(indicators)

    def reset_session(self) -> None:
        """Reset per-session detector state (sentiment window + behavioral history)."""
        self._detector.reset_session()


__all__ = [
    # Pipeline facade.
    "CrisisEngine",
    # Layers and pipeline.
    "KeywordLayer",
    "SentimentLayer",
    "PolarityAnalyzer",
    "BehavioralLayer",
    "CrisisDetector",
    "CrisisIndicators",
    "CrisisAssessor",
    # Types and enums.
    "KeywordSemanticField",
    "CrisisLevel",
    "KeywordMatch",
    "KeywordAnalysisResult",
    "SentimentReading",
    "SentimentTrend",
    "SentimentAnalysisResult",
    "ComplexityTrend",
    "BehavioralAnalysisResult",
    "BehavioralMetrics",
    "CrisisAssessment",
]
