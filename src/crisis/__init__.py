"""
Crisis Detection Engine (CDE)
3-layer local-first pipeline:
  Layer 1: Keyword/Semantic Field Analysis
  Layer 2: Sentiment & Emotional Tone Analysis
  Layer 3: Behavioral Pattern Analysis
"""

from .detection.cde import CrisisDetectionEngine, CDEResult

__all__ = ["CrisisDetectionEngine", "CDEResult"]
