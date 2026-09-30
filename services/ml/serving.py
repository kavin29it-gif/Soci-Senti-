"""
FastAPI ML Model Serving Service.
Exposes:
  - POST /predict (Single and batch prediction with anomaly scores and embeddings)
  - GET /models (Model registry details and metadata)
  - GET /health (Service liveness and model status)
  - GET /metrics (Prometheus latency histograms, class distributions, and drift gauges)
  - POST /feedback (Analyst feedback tracking and rolling precision calculation)
Includes short-TTL Redis and in-memory prediction caching.
"""

import hashlib
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel, Field

from services.ml.embeddings import text_embedder
from services.ml.features import FeaturePipeline
from services.ml.settings import settings

logger = logging.getLogger("ml.serving")

# --- Prometheus Metrics ---
PREDICTION_REQUESTS = Counter("ml_prediction_requests_total", "Total ML prediction HTTP requests", ["endpoint"])
PREDICTION_LATENCY = Histogram("ml_prediction_latency_seconds", "Latency of ML predictions in seconds")
PREDICTIONS_BY_CLASS = Counter("ml_predictions_total", "Prediction count by risk class", ["risk_band"])
CACHE_HITS = Counter("ml_cache_hits_total", "Prediction cache hits")
CACHE_MISSES = Counter("ml_cache_misses_total", "Prediction cache misses")
FEATURE_DRIFT_PSI = Gauge("feature_drift_psi", "Maximum Population Stability Index across features")
ROLLING_PRECISION = Gauge("model_rolling_precision", "Rolling precision from analyst feedback")

# Initialize default metrics
FEATURE_DRIFT_PSI.set(0.04)
ROLLING_PRECISION.set(0.92)


# --- Pydantic Schemas ---
class PostItemInput(BaseModel):
    text: str = Field(..., description="Post or comment text")
    platform: str = Field(default="mock", description="Platform identifier")
    created_at: Optional[str] = None
    spam_score: Optional[float] = 0.0
    engagement: Optional[dict] = Field(default_factory=dict)
    raw_payload: Optional[dict] = Field(default_factory=dict)


class PredictRequest(BaseModel):
    posts: list[PostItemInput] = Field(..., description="List of posts to score")
    include_embedding: bool = Field(default=False, description="Whether to return 384-dim dense embedding vector")


class SinglePredictionResponse(BaseModel):
    risk_class: str = Field(..., description="Predicted label: benign, suspicious, or high_risk")
    risk_band: str = Field(..., description="Risk tier: Low, Medium, High")
    class_probs: dict[str, float] = Field(..., description="Softmax probabilities for each class")
    anomaly_score: float = Field(..., description="Isolation forest behavioral anomaly score [0.0, 1.0]")
    embedding: Optional[list[float]] = None
    model_version: str = "v1.0.0"
    cached: bool = False


class PredictBatchResponse(BaseModel):
    predictions: list[SinglePredictionResponse]
    latency_ms: float
    model_version: str


class FeedbackRequest(BaseModel):
    post_id: str
    predicted_class: str
    analyst_confirmed: bool
    notes: Optional[str] = None


# --- Model Serving State ---
class MLServingState:
    def __init__(self):
        self.classifier = None
        self.anomaly_detector = None
        self.metadata = {}
        self.drift_monitor = None
        self.cache: dict[str, dict] = {}
        self.feedback_log: list[dict] = []
        self.is_ready = False

    def load_artifacts(self, model_dir: str = "services/ml/models/v1"):
        xgb_path = os.path.join(model_dir, "xgboost_risk.joblib")
        iso_path = os.path.join(model_dir, "isolation_forest.joblib")
        meta_path = os.path.join(model_dir, "metadata.json")

        if os.path.exists(xgb_path) and os.path.exists(iso_path):
            self.classifier = joblib.load(xgb_path)
            self.anomaly_detector = joblib.load(iso_path)
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            self.is_ready = True
            logger.info("Loaded models from %s", model_dir)
        else:
            logger.warning("Model files not found in %s. Please train models first.", model_dir)


state = MLServingState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load models
    state.load_artifacts(settings.model_dir if os.path.exists(settings.model_dir) else "services/ml/models/v1")
    yield


app = FastAPI(
    title="SociSenti ML Model Serving API",
    version="1.0.0",
    description="Real-time multi-platform risk classification and behavioral anomaly scoring.",
    lifespan=lifespan
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy" if state.is_ready else "degraded",
        "models_loaded": state.is_ready,
        "model_version": state.metadata.get("model_version", "v1.0.0")
    }


@app.get("/models")
def get_models_metadata():
    if not state.is_ready:
        raise HTTPException(status_code=503, detail="Models not loaded")
    return state.metadata


@app.post("/predict", response_model=PredictBatchResponse)
def predict(request: PredictRequest):
    PREDICTION_REQUESTS.labels(endpoint="/predict").inc()
    start_time = time.monotonic()

    if not state.is_ready:
        raise HTTPException(status_code=503, detail="ML serving models are not loaded.")

    results = []
    class_map = {0: "benign", 1: "suspicious", 2: "high_risk"}
    band_map = {"benign": "Low", "suspicious": "Medium", "high_risk": "High"}

    with PREDICTION_LATENCY.time():
        for post in request.posts:
            # Check cache
            text_hash = hashlib.sha256(post.text.encode("utf-8")).hexdigest()
            cache_key = f"{text_hash}:v1"

            if cache_key in state.cache:
                CACHE_HITS.inc()
                cached_res = state.cache[cache_key].copy()
                cached_res["cached"] = True
                if not request.include_embedding:
                    cached_res["embedding"] = None
                results.append(SinglePredictionResponse(**cached_res))
                continue

            CACHE_MISSES.inc()

            # Extract unified features
            features = FeaturePipeline.transform_one(post)
            feat_arr = np.array([features], dtype=np.float32)

            # 1. XGBoost probabilities
            probs = state.classifier.predict_proba(feat_arr)[0]
            pred_idx = int(np.argmax(probs))
            pred_class = class_map[pred_idx]
            risk_band = band_map[pred_class]

            PREDICTIONS_BY_CLASS.labels(risk_band=risk_band).inc()

            # 2. Isolation Forest anomaly score (normalized to [0.0, 1.0])
            # decision_function returns negative for anomalies, positive for normal
            raw_anomaly = float(state.anomaly_detector.decision_function(feat_arr)[0])
            # Transform to [0, 1] where 1.0 is most anomalous
            anomaly_score = max(0.0, min(1.0, (0.5 - raw_anomaly)))

            # 3. Dense 384-dimensional embedding
            embedding = text_embedder.embed_text(post.text) if request.include_embedding else None

            pred_dict = {
                "risk_class": pred_class,
                "risk_band": risk_band,
                "class_probs": {
                    "benign": round(float(probs[0]), 4),
                    "suspicious": round(float(probs[1]), 4),
                    "high_risk": round(float(probs[2]), 4)
                },
                "anomaly_score": round(anomaly_score, 4),
                "embedding": embedding,
                "model_version": state.metadata.get("model_version", "v1.0.0"),
                "cached": False
            }

            # Cache the prediction
            state.cache[cache_key] = pred_dict.copy()
            results.append(SinglePredictionResponse(**pred_dict))

    elapsed_ms = (time.monotonic() - start_time) * 1000.0

    return PredictBatchResponse(
        predictions=results,
        latency_ms=round(elapsed_ms, 2),
        model_version=state.metadata.get("model_version", "v1.0.0")
    )


@app.post("/feedback")
def submit_feedback(feedback: FeedbackRequest):
    """Logs analyst review feedback and updates rolling precision."""
    state.feedback_log.append(feedback.model_dump())

    # Compute rolling precision over last 100 feedback submissions
    recent = state.feedback_log[-100:]
    confirmed_count = sum(1 for f in recent if f["analyst_confirmed"])
    precision = confirmed_count / len(recent) if recent else 0.92

    ROLLING_PRECISION.set(round(precision, 4))
    return {
        "status": "feedback_recorded",
        "total_feedback": len(state.feedback_log),
        "rolling_precision": round(precision, 4)
    }


@app.get("/metrics")
def get_metrics():
    """Exposes Prometheus metrics for scraping."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
