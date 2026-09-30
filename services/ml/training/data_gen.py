"""
Synthetic Labeled Dataset Generator for Risk Classification.
Applies reproducible, seeded weak-supervision heuristics to generate training labels:
  0: benign
  1: suspicious
  2: high_risk
DISCLAIMER: Ground-truth risk labels are synthetic for MVP development and must be
retrained on verified compliance annotations in production.
"""

import json
import logging
import os
import random

from services.ml.features import THREAT_REGEX, URGENCY_REGEX, FeaturePipeline

logger = logging.getLogger(__name__)


def generate_weak_labels(sample_file: str = "data/sample/sample_posts.json", seed: int = 42) -> dict:
    """
    Applies weak supervision labeling functions to produce labeled training data.
    """
    random.seed(seed)
    if not os.path.exists(sample_file):
        raise FileNotFoundError(f"Sample data file not found: {sample_file}")

    with open(sample_file, "r", encoding="utf-8") as f:
        posts = json.load(f)

    labeled_data = []
    class_counts = {0: 0, 1: 0, 2: 0}

    for p in posts:
        text = p.get("text", "")
        raw_payload = p.get("raw_payload", {})
        tag = raw_payload.get("simulated_tag", "")
        spam_score = float(p.get("spam_score", 0.0))

        # Weak supervision rules
        if tag in ["coordinated_burst", "high_risk_narrative"] or THREAT_REGEX.search(text):
            label = 2  # high_risk
        elif tag == "spam_bot" or spam_score >= 0.40 or URGENCY_REGEX.search(text):
            label = 1  # suspicious
        else:
            label = 0  # benign

        # Extract numerical feature vector
        features = FeaturePipeline.transform_one(p)

        labeled_data.append({
            "post_id": p.get("post_id"),
            "platform": p.get("platform"),
            "text": text,
            "label": label,
            "label_name": ["benign", "suspicious", "high_risk"][label],
            "features": features
        })
        class_counts[label] += 1

    metadata = {
        "dataset_name": "socisenti_synthetic_risk_labels_v1",
        "description": "Seeded synthetic training dataset with weak supervision labeling.",
        "disclaimer": "Labels are synthetically assigned for MVP validation; do not use in live production without analyst review.",
        "seed": seed,
        "total_samples": len(labeled_data),
        "class_distribution": class_counts,
        "feature_count": len(FeaturePipeline.transform_one(posts[0]))
    }

    return {
        "metadata": metadata,
        "records": labeled_data
    }


def save_training_dataset(output_path: str = "data/training_dataset.json", sample_file: str = "data/sample/sample_posts.json"):
    data = generate_weak_labels(sample_file=sample_file)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Saved %d labeled training samples to %s", len(data["records"]), output_path)
    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dataset = save_training_dataset()
    print("Dataset generated successfully:")
    print(json.dumps(dataset["metadata"], indent=2))
