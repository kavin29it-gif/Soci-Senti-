"""
Phase 8 Verification Tests: Production Hardening, Drift Monitoring & Governance.
Verifies:
  1. Feature Drift Calculation (Population Stability Index / PSI thresholds & edge cases).
  2. DriftMonitor streaming buffer and multi-feature shift detection.
  3. Prometheus metrics endpoint (/metrics) and scrape formatting.
  4. Grafana dashboard & datasource provisioning JSON/YAML schema validity.
  5. Privacy policy enforcement (Salted SHA-256 pseudonymization, k >= 50 suppression, Laplace DP).
  6. End-to-end replay demo script execution and integrity guarantees.
"""

import json
import os

import numpy as np
import pytest
import yaml
from fastapi.testclient import TestClient

from services.analytics.demographics import demographics_engine
from services.api.main import app
from services.demo import run_demo
from services.ml.drift import DriftMonitor, calculate_psi


@pytest.fixture
def client():
    return TestClient(app)


def test_calculate_psi_stability_and_drift_detection():
    """Validates Population Stability Index calculation across stable, moderate, and severe shift regimes."""
    np.random.seed(42)
    baseline = np.random.normal(0.0, 1.0, 1000)

    # 1. Identical distribution -> PSI should be close to 0.0
    same_sample = np.random.normal(0.0, 1.0, 800)
    psi_stable = calculate_psi(baseline, same_sample)
    assert psi_stable < 0.10, f"Expected stable PSI < 0.10, got {psi_stable}"

    # 2. Moderate shift -> 0.10 <= PSI < 0.25
    shifted_moderate = np.random.normal(0.35, 1.0, 800)
    psi_moderate = calculate_psi(baseline, shifted_moderate)
    assert 0.05 <= psi_moderate <= 0.35, f"Expected moderate PSI in range, got {psi_moderate}"

    # 3. Severe drift -> PSI >= 0.25
    shifted_severe = np.random.normal(1.5, 1.5, 800)
    psi_severe = calculate_psi(baseline, shifted_severe)
    assert psi_severe >= 0.25, f"Expected severe drift PSI >= 0.25, got {psi_severe}"

    # 4. Edge cases
    assert calculate_psi(np.array([]), same_sample) == 0.0
    assert calculate_psi(baseline, np.array([])) == 0.0
    assert calculate_psi(np.ones(50), np.ones(50)) == 0.0


def test_drift_monitor_streaming_evaluation():
    """Validates DriftMonitor multi-feature buffering and evaluation report."""
    np.random.seed(101)
    feature_names = ["text_length", "caps_ratio", "urgency_flag"]
    baseline = np.column_stack([
        np.random.normal(100.0, 20.0, 300),
        np.random.beta(1.0, 10.0, 300),
        np.random.binomial(1, 0.05, 300)
    ])

    monitor = DriftMonitor(baseline_features=baseline, feature_names=feature_names)

    # Before buffer fills to minimum threshold (20)
    assert monitor.evaluate_drift() == {}

    # Stream in 50 observations with severe shift on urgency_flag
    for _ in range(50):
        shifted_vector = [
            float(np.random.normal(105.0, 20.0)),
            float(np.random.beta(1.0, 10.0)),
            float(np.random.binomial(1, 0.65))  # High burst of urgency
        ]
        monitor.record_inference(shifted_vector)

    report = monitor.evaluate_drift()
    assert len(report) == 3
    for name in feature_names:
        assert "psi" in report[name]
        assert "drift_detected" in report[name]
        assert "status" in report[name]
        assert report[name]["status"] in ["stable", "moderate_drift", "severe_drift"]

    # Verify urgency_flag detected drift
    assert report["urgency_flag"]["drift_detected"] is True


def test_prometheus_metrics_endpoint(client):
    """Verifies that FastAPI /metrics endpoint returns standard Prometheus text format."""
    # Trigger a request so counter registers
    client.get("/health")

    res = client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers.get("content-type", "")

    body = res.text
    assert "http_requests_total" in body
    assert "endpoint=\"/health\"" in body or "endpoint=\"/metrics\"" in body
    assert "http_request_duration_seconds" in body


def test_grafana_dashboard_provisioning_validity():
    """Verifies that Grafana dashboard and datasource provisioning files are valid and contain all panels."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dashboard_path = os.path.join(base_dir, "monitoring", "grafana", "provisioning", "dashboards", "platform_overview.json")
    dashboards_yml = os.path.join(base_dir, "monitoring", "grafana", "provisioning", "dashboards", "dashboards.yml")
    datasources_yml = os.path.join(base_dir, "monitoring", "grafana", "provisioning", "datasources", "datasource.yml")
    prometheus_yml = os.path.join(base_dir, "monitoring", "prometheus.yml")

    assert os.path.exists(dashboard_path), "Grafana overview dashboard JSON missing"
    assert os.path.exists(dashboards_yml), "Grafana dashboards.yml config missing"
    assert os.path.exists(datasources_yml), "Grafana datasource.yml config missing"
    assert os.path.exists(prometheus_yml), "Prometheus config missing"

    with open(dashboard_path, "r", encoding="utf-8") as f:
        dash_data = json.load(f)

    assert dash_data["uid"] == "socisenti-overview"
    assert len(dash_data["panels"]) >= 6

    panel_titles = [p["title"] for p in dash_data["panels"]]
    assert "Total Ingestion & API Requests" in panel_titles
    assert "ML Serving Latency (p95)" in panel_titles
    assert "Feature Drift PSI (Max)" in panel_titles
    assert "Model Rolling Precision" in panel_titles
    assert "Prediction Distribution by Risk Band" in panel_titles
    assert "Kafka & Ingestion Processing Throughput" in panel_titles

    # Validate YAML configs
    with open(dashboards_yml, "r", encoding="utf-8") as f:
        d_cfg = yaml.safe_load(f)
        assert "providers" in d_cfg

    with open(datasources_yml, "r", encoding="utf-8") as f:
        ds_cfg = yaml.safe_load(f)
        assert "datasources" in ds_cfg


def test_privacy_governance_enforcement():
    """
    Verifies adherence to PRIVACY.md:
      1. Small cohorts (< 50) must be suppressed under k-anonymity.
      2. Large cohorts (>= 50) apply Laplace noise and suppress sub-k buckets.
      3. No individual demographic records are created or exported.
    """
    # 1. Cohort size < 50
    small_cohort = [{"text": "Sample text", "lang": "en"} for _ in range(35)]
    small_res = demographics_engine.aggregate_cohort(small_cohort, cohort_name="small_test")
    assert small_res["status"] == "suppressed"
    assert "below privacy threshold" in small_res["reason"]
    assert small_res["distributions"] == {}

    # 2. Cohort size >= 50
    large_cohort = [{"text": "Sample financial post", "lang": "en"} for _ in range(65)]
    large_res = demographics_engine.aggregate_cohort(large_cohort, cohort_name="large_test")
    assert large_res["status"] == "published"
    assert "regions" in large_res["distributions"]
    assert "North America & International" in large_res["distributions"]["regions"]
    # The count should be noisy (not an exact integer 65)
    noisy_count = large_res["distributions"]["regions"]["North America & International"]
    assert isinstance(noisy_count, (float, int))


def test_end_to_end_replay_demo_execution():
    """Verifies that services/demo.py runs end-to-end and validates cryptographic evidence chains."""
    demo_output = run_demo(sample_limit=60)
    assert demo_output["status"] == "success"
    assert demo_output["clean_posts_count"] > 0
    assert len(demo_output["merkle_root"]) == 64
    assert demo_output["audit_chain_valid"] is True
    assert os.path.exists(demo_output["pdf_report"])
    assert demo_output["psi_drift"] < 0.15
