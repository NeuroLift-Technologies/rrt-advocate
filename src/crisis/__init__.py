"""
Crisis Detection Engine (CDE) — local-first, 3-layer pipeline.

Layer 1: Keyword / Semantic Field Analysis
Layer 2: Sentiment & Emotional Tone Analysis
Layer 3: Behavioural Pattern Analysis
"""

from src.crisis.engine import CrisisDetectionEngine

__all__ = ["CrisisDetectionEngine"]
