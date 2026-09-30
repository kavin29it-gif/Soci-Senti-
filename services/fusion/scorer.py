"""
Multimodal Risk Scoring & Fusion Meta-Model.
Fuses classifier probabilities, behavioral anomaly scores, sentiment,
narrative velocity, and network coordination signals into a calibrated 0-100 risk score
with confidence intervals and risk bands (Low, Medium, High).
"""

import logging

from services.fusion.settings import settings

logger = logging.getLogger(__name__)


class RiskScorer:
    """Fuses multi-engine signals into an explainable 0-100 risk score."""

    def __init__(
        self,
        low_max: float = settings.low_band_max,
        medium_max: float = settings.medium_band_max
    ):
        self.low_max = low_max
        self.medium_max = medium_max

    def score_entity(
        self,
        entity_type: str,
        entity_id: str,
        class_probs: dict[str, float],
        anomaly_score: float = 0.0,
        neg_sentiment_prob: float = 0.0,
        narrative_velocity: float = 0.0,
        coordination_score: float = 0.0,
        influence_score: float = 0.0
    ) -> dict:
        """
        Computes calibrated risk score (0-100) and confidence band.
        """
        p_high = float(class_probs.get("high_risk", 0.0))
        p_susp = float(class_probs.get("suspicious", 0.0))
        p_benign = float(class_probs.get("benign", 1.0))

        # Calibrated weighted fusion equation
        # High risk prob (35%), suspicious prob (15%), anomaly (20%), coordination (15%), negative sentiment (10%), velocity (5%)
        raw_score = (
            (p_high * 40.0) +
            (p_susp * 18.0) +
            (min(1.0, anomaly_score) * 18.0) +
            (min(1.0, coordination_score) * 14.0) +
            (min(1.0, neg_sentiment_prob) * 6.0) +
            (min(1.0, narrative_velocity) * 4.0)
        )

        risk_score = round(max(0.0, min(100.0, raw_score)), 1)

        # Risk band mapping
        if risk_score <= self.low_max:
            risk_band = "Low"
        elif risk_score <= self.medium_max:
            risk_band = "Medium"
        else:
            risk_band = "High"

        # Quantile / Variance Confidence Band Estimation
        # Uncertainty is proportional to class entropy / disagreement between signals
        max_prob = max(p_high, p_susp, p_benign)
        uncertainty = 1.0 - max_prob  # 0.0 (high certainty) to 0.67 (high uncertainty)
        std_dev = 4.0 + (12.0 * uncertainty)

        confidence = round(max(0.50, min(0.99, 1.0 - (uncertainty * 0.6))), 2)
        ci_lower = max(0.0, round(risk_score - (1.96 * std_dev), 1))
        ci_upper = min(100.0, round(risk_score + (1.96 * std_dev), 1))

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "risk_score": risk_score,
            "risk_band": risk_band,
            "confidence": confidence,
            "confidence_band": {
                "lower": ci_lower,
                "upper": ci_upper,
                "std_dev": round(std_dev, 2)
            },
            "signals": {
                "p_high_risk": p_high,
                "p_suspicious": p_susp,
                "anomaly_score": anomaly_score,
                "coordination_score": coordination_score,
                "neg_sentiment_prob": neg_sentiment_prob,
                "narrative_velocity": narrative_velocity
            },
            "model_version": "fusion-v1.0"
        }


risk_scorer = RiskScorer()
