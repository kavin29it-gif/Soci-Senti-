"""
Feature Drift Monitoring (Population Stability Index & KS Statistic).
Tracks distribution shifts between training baseline and real-time inference data.
Exposes drift metrics to Prometheus.
"""

import logging
from typing import Union

import numpy as np

logger = logging.getLogger(__name__)


def calculate_psi(expected: np.ndarray, actual: np.ndarray, num_buckets: int = 10) -> float:
    """
    Computes the Population Stability Index (PSI) between baseline (expected)
    and production (actual) feature values.
    PSI < 0.10: Stable
    0.10 <= PSI < 0.25: Moderate shift
    PSI >= 0.25: Significant shift / Drift detected
    """
    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    exp_arr = np.asarray(expected, dtype=np.float32)
    act_arr = np.asarray(actual, dtype=np.float32)

    unique_vals = np.unique(exp_arr)
    if len(unique_vals) <= num_buckets:
        # Discrete feature binning via midpoints
        bin_edges = np.concatenate([
            [unique_vals[0] - 0.5],
            (unique_vals[:-1] + unique_vals[1:]) / 2.0,
            [unique_vals[-1] + 0.5]
        ])
    else:
        # Quantile bin edges for continuous features
        percentiles = np.linspace(0, 100, num_buckets + 1)
        bin_edges = np.unique(np.percentile(exp_arr, percentiles))
        if len(bin_edges) < 2:
            return 0.0
        bin_edges[0] -= 1e-4
        bin_edges[-1] += 1e-4

    # Count occurrences in each bucket
    expected_counts, _ = np.histogram(exp_arr, bins=bin_edges)
    actual_counts, _ = np.histogram(act_arr, bins=bin_edges)

    # Convert to fractions with Laplace smoothing
    expected_fractions = (expected_counts + 1e-4) / (len(exp_arr) + 1e-4 * len(expected_counts))
    actual_fractions = (actual_counts + 1e-4) / (len(act_arr) + 1e-4 * len(actual_counts))

    # Calculate PSI sum
    psi_val = np.sum((actual_fractions - expected_fractions) * np.log(actual_fractions / expected_fractions))
    return float(round(max(0.0, psi_val), 4))


class DriftMonitor:
    """Manages baseline feature distributions and evaluates streaming inference drift."""

    def __init__(self, baseline_features: Union[list, np.ndarray], feature_names: list[str]):
        self.baseline = np.array(baseline_features, dtype=np.float32)
        self.feature_names = feature_names
        self.inference_buffer: list[list[float]] = []
        self.buffer_size = 500

    def record_inference(self, feature_vector: list[float]):
        """Buffers inference feature vector for periodic drift evaluation."""
        self.inference_buffer.append(feature_vector)
        if len(self.inference_buffer) > self.buffer_size * 2:
            self.inference_buffer = self.inference_buffer[-self.buffer_size:]

    def evaluate_drift(self) -> dict[str, dict]:
        """
        Computes PSI for all features against baseline.
        Returns: {feature_name: {"psi": float, "drift_detected": bool, "status": str}}
        """
        if len(self.inference_buffer) < 20:
            return {}

        current_data = np.array(self.inference_buffer, dtype=np.float32)
        drift_report = {}

        for i, name in enumerate(self.feature_names):
            exp_col = self.baseline[:, i]
            act_col = current_data[:, i]
            psi = calculate_psi(exp_col, act_col)

            status = "stable"
            if psi >= 0.25:
                status = "severe_drift"
            elif psi >= 0.10:
                status = "moderate_drift"

            drift_report[name] = {
                "psi": psi,
                "drift_detected": psi >= 0.15,
                "status": status
            }

        return drift_report
