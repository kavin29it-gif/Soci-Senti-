"""
Model Training & Registry Pipeline.
Trains:
  1. XGBoost Multi-Class Classifier (benign, suspicious, high_risk)
  2. Scikit-Learn Isolation Forest (behavioral anomaly scoring)
Evaluates real metrics and saves artifacts + metadata.json to the model registry.
"""

import json
import logging
import os
from datetime import datetime, timezone

import joblib
import numpy as np
import xgboost as xgb
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

from services.ml.features import FEATURE_NAMES
from services.ml.training.data_gen import save_training_dataset

logger = logging.getLogger(__name__)


def train_models(
    dataset_file: str = "data/training_dataset.json",
    model_output_dir: str = "services/ml/models/v1"
) -> dict:
    """
    Trains XGBoost and Isolation Forest models on the synthetic labeled dataset.
    """
    if not os.path.exists(dataset_file):
        logger.info("Training dataset not found. Generating fresh dataset from sample...")
        save_training_dataset(output_path=dataset_file)

    with open(dataset_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = data["records"]
    X = np.array([r["features"] for r in records], dtype=np.float32)
    y = np.array([r["label"] for r in records], dtype=np.int32)

    logger.info("Loaded %d training records with %d features.", len(X), X.shape[1])

    # Train / Test split (80 / 20 stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # 1. Train XGBoost Classifier
    logger.info("Training XGBoost risk classifier...")
    clf = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        objective="multi:softprob",
        num_class=3,
        random_state=42,
        eval_metric="mlogloss"
    )
    clf.fit(X_train, y_train)

    # Evaluate XGBoost
    y_pred = clf.predict(X_test)
    acc = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
    report = classification_report(y_test, y_pred, output_dict=True)

    logger.info("XGBoost Test Accuracy: %.4f | Macro F1: %.4f", acc, macro_f1)

    # 2. Train Isolation Forest Anomaly Detector
    logger.info("Training Isolation Forest behavioral anomaly detector...")
    iso = IsolationForest(
        n_estimators=100,
        contamination=0.15,
        random_state=42
    )
    iso.fit(X_train)

    # 3. Save Model Artifacts
    os.makedirs(model_output_dir, exist_ok=True)
    xgb_path = os.path.join(model_output_dir, "xgboost_risk.joblib")
    iso_path = os.path.join(model_output_dir, "isolation_forest.joblib")

    joblib.dump(clf, xgb_path)
    joblib.dump(iso, iso_path)
    logger.info("Saved model artifacts to %s", model_output_dir)

    # 4. Generate Registry metadata.json
    metadata = {
        "model_version": "v1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": "git-head-socisenti-v1",
        "dataset_name": data["metadata"]["dataset_name"],
        "total_samples": len(records),
        "feature_names": FEATURE_NAMES,
        "feature_count": len(FEATURE_NAMES),
        "target_classes": {
            0: "benign",
            1: "suspicious",
            2: "high_risk"
        },
        "metrics": {
            "test_accuracy": round(acc, 4),
            "macro_f1": round(macro_f1, 4),
            "classification_report": report
        },
        "artifacts": {
            "classifier": "xgboost_risk.joblib",
            "anomaly_detector": "isolation_forest.joblib"
        },
        "disclaimer": "Models trained on synthetic weak-supervision data for MVP demonstration."
    }

    meta_path = os.path.join(model_output_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Model registry metadata saved to %s", meta_path)
    return metadata


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    meta = train_models()
    print("Training completed successfully:")
    print(json.dumps(meta["metrics"], indent=2))
