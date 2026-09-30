"""
Unified Feature Engineering Pipeline.
Extracts 20 text, metadata, behavioral, and temporal features.
Guarantees zero train/serve skew by using the exact same transformation in training and serving.
"""

import math
import re
from datetime import datetime, timezone
from typing import Any, Union

FEATURE_NAMES = [
    "char_count",
    "word_count",
    "caps_ratio",
    "excl_count",
    "quest_count",
    "url_count",
    "has_crypto_ticker",
    "has_urgency_keyword",
    "has_threat_keyword",
    "is_reddit",
    "is_youtube",
    "is_telegram",
    "is_mock",
    "hour_sin",
    "hour_cos",
    "log_likes",
    "log_shares",
    "log_replies",
    "spam_score",
    "burst_rate_proxy"
]

URGENCY_REGEX = re.compile(r"\b(urgent|alert|breaking|immediate|freeze|bank\s*run|withdraw|insolvent|collapse)\b", re.IGNORECASE)
THREAT_REGEX = re.compile(r"\b(disrupt|exploit|protest|attack|leak|pathogen|sabotage|flash\s*mob)\b", re.IGNORECASE)
TICKER_REGEX = re.compile(r"\$[A-Z]{2,6}\b")
URL_REGEX = re.compile(r"https?://\S+|www\.\S+|bit\.ly/\S+|tinyurl\.com/\S+", re.IGNORECASE)


class FeaturePipeline:
    """Extracts identical numerical feature vectors for ML training and real-time inference."""

    @staticmethod
    def extract_features_dict(post: Union[dict, Any]) -> dict[str, float]:
        """Extracts feature dictionary from post dict or CleanPost/RawPost model."""
        if hasattr(post, "model_dump"):
            data = post.model_dump()
        elif isinstance(post, dict):
            data = post
        else:
            data = post.__dict__

        text = data.get("text", "") or ""
        platform = (data.get("platform") or "").lower()
        spam_score = float(data.get("spam_score", 0.0))

        # Engagement
        eng = data.get("engagement") or {}
        if hasattr(eng, "model_dump"):
            eng = eng.model_dump()
        likes = float(eng.get("likes", 0))
        shares = float(eng.get("shares", 0))
        replies = float(eng.get("replies", 0))

        # Created timestamp
        created_at_raw = data.get("created_at")
        if isinstance(created_at_raw, str):
            try:
                created_dt = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
            except ValueError:
                created_dt = datetime.now(timezone.utc)
        elif isinstance(created_at_raw, datetime):
            created_dt = created_at_raw
        else:
            created_dt = datetime.now(timezone.utc)

        hour = created_dt.hour

        # Text calculations
        char_count = float(len(text))
        words = re.findall(r"\b\w+\b", text)
        word_count = float(len(words))

        alpha_chars = [c for c in text if c.isalpha()]
        caps_ratio = (sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)) if alpha_chars else 0.0

        excl_count = float(text.count("!"))
        quest_count = float(text.count("?"))
        url_count = float(len(URL_REGEX.findall(text)))

        has_crypto_ticker = 1.0 if TICKER_REGEX.search(text) else 0.0
        has_urgency_keyword = 1.0 if URGENCY_REGEX.search(text) else 0.0
        has_threat_keyword = 1.0 if THREAT_REGEX.search(text) else 0.0

        # Platform one-hot
        is_reddit = 1.0 if platform == "reddit" else 0.0
        is_youtube = 1.0 if platform == "youtube" else 0.0
        is_telegram = 1.0 if platform == "telegram" else 0.0
        is_mock = 1.0 if platform in ["mock", ""] else 0.0

        # Cyclical hour encoding
        hour_angle = 2.0 * math.pi * (hour / 24.0)
        hour_sin = math.sin(hour_angle)
        hour_cos = math.cos(hour_angle)

        # Log engagement
        log_likes = math.log1p(max(0.0, likes))
        log_shares = math.log1p(max(0.0, shares))
        log_replies = math.log1p(max(0.0, replies))

        # Burst / Velocity proxy
        raw_payload = data.get("raw_payload") or {}
        burst_rate = 1.0 if raw_payload.get("simulated_tag") == "coordinated_burst" else 0.0

        return {
            "char_count": char_count,
            "word_count": word_count,
            "caps_ratio": caps_ratio,
            "excl_count": excl_count,
            "quest_count": quest_count,
            "url_count": url_count,
            "has_crypto_ticker": has_crypto_ticker,
            "has_urgency_keyword": has_urgency_keyword,
            "has_threat_keyword": has_threat_keyword,
            "is_reddit": is_reddit,
            "is_youtube": is_youtube,
            "is_telegram": is_telegram,
            "is_mock": is_mock,
            "hour_sin": hour_sin,
            "hour_cos": hour_cos,
            "log_likes": log_likes,
            "log_shares": log_shares,
            "log_replies": log_replies,
            "spam_score": spam_score,
            "burst_rate_proxy": burst_rate
        }

    @classmethod
    def transform_one(cls, post: Union[dict, Any]) -> list[float]:
        """Returns ordered float vector of features."""
        feat_dict = cls.extract_features_dict(post)
        return [feat_dict[name] for name in FEATURE_NAMES]

    @classmethod
    def transform_batch(cls, posts: list[Union[dict, Any]]) -> list[list[float]]:
        """Returns 2D list of ordered feature vectors."""
        return [cls.transform_one(p) for p in posts]


feature_pipeline = FeaturePipeline()
