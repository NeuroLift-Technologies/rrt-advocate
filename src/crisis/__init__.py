"""
Crisis Detection Engine (CDE) - 3-Layer Local-First Pipeline
Part of the RRT AIdvocAIte (Protective Layer) of the HAIEF Solidarity Framework.

All processing is local-first. No user data is sent to cloud by default.
"""

from .cde_pipeline import CDEPipeline
from .detectors.layer1_keyword import Layer1KeywordAnalyzer
from .detectors.layer2_sentiment import Layer2SentimentAnalyzer
from .detectors.layer3_behavioral import Layer3BehavioralAnalyzer

__all__ = [
    "CDEPipeline",
    "Layer1KeywordAnalyzer",
    "Layer2SentimentAnalyzer",
    "Layer3BehavioralAnalyzer",
]
