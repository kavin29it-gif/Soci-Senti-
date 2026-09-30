"""Analytical Engines Package."""

from services.analytics.demographics import PrivacyPreservingDemographics, demographics_engine
from services.analytics.network import GraphEmbedder, GraphSAGEEmbedder, NetworkAnalysisEngine, network_engine
from services.analytics.sentiment import SentimentEmotionEngine, sentiment_engine
from services.analytics.trends import TrendNarrativeEngine, trend_engine

__all__ = [
    "SentimentEmotionEngine",
    "sentiment_engine",
    "PrivacyPreservingDemographics",
    "demographics_engine",
    "TrendNarrativeEngine",
    "trend_engine",
    "NetworkAnalysisEngine",
    "network_engine",
    "GraphEmbedder",
    "GraphSAGEEmbedder"
]
