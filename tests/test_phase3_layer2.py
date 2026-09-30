"""
Phase 3 (Layer 2) Test Suite:
Validates FeaturePipeline (zero train/serve skew), Weak Supervision Data Generation,
XGBoost & IsolationForest Model Registry, Dense Embeddings (384-dim),
FastAPI Model Serving (/predict, /models, /health, /metrics, /feedback),
and Feature Drift PSI Monitoring.
"""

import json
import os

import numpy as np
import pytest
from fastapi.testclient import TestClient

from services.ml.drift import DriftMonitor, calculate_psi
from services.ml.embeddings import TextEmbedder
from services.ml.features import FEATURE_NAMES, FeaturePipeline
from services.ml.serving import app, state


@pytest.fixture(scope="module")
def client():
    state.load_artifacts("services/ml/models/v1")
    with TestClient(app) as c:
        yield c


def test_feature_pipeline_dimensions_and_consistency():
    post_a = {
        "text": "URGENT ALERT: Immediate bank run at NordicCapital! Withdraw now #BankRun",
        "platform": "telegram",
        "spam_score": 0.1,
        "engagement": {"likes": 50, "shares": 20, "replies": 5},
        "raw_payload": {"simulated_tag": "coordinated_burst"}
    }

    feats_dict = FeaturePipeline.extract_features_dict(post_a)
    assert len(feats_dict) == len(FEATURE_NAMES)
    assert feats_dict["is_telegram"] == 1.0
    assert feats_dict["is_reddit"] == 0.0
    assert feats_dict["has_urgency_keyword"] == 1.0
    assert feats_dict["burst_rate_proxy"] == 1.0

    vector = FeaturePipeline.transform_one(post_a)
    assert len(vector) == len(FEATURE_NAMES)
    assert isinstance(vector[0], float)

    batch_vectors = FeaturePipeline.transform_batch([post_a, post_a])
    assert len(batch_vectors) == 2
    assert batch_vectors[0] == batch_vectors[1]


def test_model_registry_artifacts_exist():
    model_dir = os.path.join("services", "ml", "models", "v1")
    xgb_path = os.path.join(model_dir, "xgboost_risk.joblib")
    iso_path = os.path.join(model_dir, "isolation_forest.joblib")
    meta_path = os.path.join(model_dir, "metadata.json")

    assert os.path.exists(xgb_path), "XGBoost model artifact must exist"
    assert os.path.exists(iso_path), "Isolation Forest artifact must exist"
    assert os.path.exists(meta_path), "Model metadata.json must exist"

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["model_version"] == "v1.0.0"
    assert "metrics" in meta
    assert "disclaimer" in meta


def test_dense_embeddings_384_dimensions():
    embedder = TextEmbedder()
    vec = embedder.embed_text("Coordinated social media manipulation detection.")

    assert len(vec) == 384
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-3, f"Embedding must be L2 normalized to unit length, got {norm}"

    # Related vs unrelated similarity test
    vec_related = embedder.embed_text("Coordinated influence operations on social networks.")
    vec_unrelated = embedder.embed_text("Homemade sourdough bread recipe with active starter.")

    sim_related = TextEmbedder.cosine_similarity(vec, vec_related)
    sim_unrelated = TextEmbedder.cosine_similarity(vec, vec_unrelated)

    assert sim_related > sim_unrelated, f"Expected {sim_related} > {sim_unrelated}"


def test_fastapi_serving_health_and_models(client):
    res_health = client.get("/health")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["status"] == "healthy"
    assert data_health["models_loaded"] is True

    res_models = client.get("/models")
    assert res_models.status_code == 200
    data_models = res_models.json()
    assert data_models["model_version"] == "v1.0.0"


def test_fastapi_serving_predict_and_caching(client):
    payload = {
        "posts": [
            {
                "text": "URGENT ALERT: Bank run at NordicCapital! Withdraw all liquid assets before freeze!",
                "platform": "telegram",
                "spam_score": 0.05,
                "engagement": {"likes": 120, "shares": 45, "replies": 12},
                "raw_payload": {"simulated_tag": "coordinated_burst"}
            },
            {
                "text": "Just completed my morning 5k run around the city reservoir. Perfect autumn weather.",
                "platform": "reddit",
                "spam_score": 0.0,
                "engagement": {"likes": 15, "shares": 0, "replies": 2}
            }
        ],
        "include_embedding": True
    }

    # First call (uncached)
    res = client.post("/predict", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert len(data["predictions"]) == 2
    pred_high = data["predictions"][0]
    pred_benign = data["predictions"][1]

    assert pred_high["risk_class"] in ["suspicious", "high_risk"]
    assert pred_high["risk_band"] in ["Medium", "High"]
    assert pred_high["anomaly_score"] >= 0.0
    assert len(pred_high["embedding"]) == 384
    assert pred_high["cached"] is False

    assert pred_benign["risk_class"] == "benign"
    assert pred_benign["risk_band"] == "Low"

    # Second call for same post should be cached
    res_cached = client.post("/predict", json={"posts": [payload["posts"][0]], "include_embedding": False})
    assert res_cached.status_code == 200
    cached_data = res_cached.json()
    assert cached_data["predictions"][0]["cached"] is True


def test_fastapi_feedback_and_metrics(client):
    feedback_payload = {
        "post_id": "post_test_999",
        "predicted_class": "high_risk",
        "analyst_confirmed": True,
        "notes": "Verified coordinated bot activity"
    }

    res_fb = client.post("/feedback", json=feedback_payload)
    assert res_fb.status_code == 200
    fb_data = res_fb.json()
    assert fb_data["status"] == "feedback_recorded"
    assert fb_data["rolling_precision"] > 0.80

    res_metrics = client.get("/metrics")
    assert res_metrics.status_code == 200
    metrics_text = res_metrics.text
    assert "ml_prediction_requests_total" in metrics_text
    assert "ml_predictions_total" in metrics_text
    assert "model_rolling_precision" in metrics_text


def test_feature_drift_psi_calculation():
    np.random.seed(42)
    baseline = np.random.normal(loc=10.0, scale=2.0, size=1000)
    same_dist = np.random.normal(loc=10.0, scale=2.0, size=500)
    shifted_dist = np.random.normal(loc=16.0, scale=3.0, size=500)

    psi_same = calculate_psi(baseline, same_dist)
    psi_shifted = calculate_psi(baseline, shifted_dist)

    assert psi_same < 0.10, f"Expected stable PSI < 0.10, got {psi_same}"
    assert psi_shifted >= 0.25, f"Expected severe drift PSI >= 0.25, got {psi_shifted}"

    # DriftMonitor class test
    base_matrix = np.column_stack([baseline, baseline * 0.5])
    monitor = DriftMonitor(baseline_features=base_matrix, feature_names=["f1", "f2"])

    for _ in range(30):
        monitor.record_inference([16.0, 8.0])

    report = monitor.evaluate_drift()
    assert "f1" in report
    assert report["f1"]["drift_detected"] is True
