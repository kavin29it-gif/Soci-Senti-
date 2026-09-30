"""
Privacy-Preserving Aggregate Demographic Inference Engine.
Enforces strict k-anonymity (k >= 50) and Laplace differential privacy.
CRITICAL COMPLIANCE CONSTRAINT: Individual protected demographic attributes are
NEVER inferred, persisted, or exported.
"""

import logging
import math
import random
from collections import defaultdict

logger = logging.getLogger(__name__)

# Coarse geographic interest regions
LANG_TO_REGION = {
    "en": "North America & International",
    "es": "Latin America & Iberia",
    "fr": "Western Europe & Francophonie",
    "de": "Central Europe",
}

INTEREST_CATEGORIES = {
    "Finance & Crypto": [r"\$?[A-Z]{3,5}", r"bank", r"crypto", r"liquidity", r"btc", r"eth", r"finance", r"trading"],
    "Technology & Engineering": [r"python", r"api", r"llm", r"kafka", r"database", r"code", r"docker", r"software"],
    "News & Current Affairs": [r"breaking", r"election", r"government", r"protest", r"mayor", r"minister", r"police"],
    "Lifestyle & Community": [r"hiking", r"sourdough", r"bread", r"autumn", r"run", r"coffee", r"recipe", r"game"]
}


class PrivacyPreservingDemographics:
    """Computes aggregated cohort-level demographic distributions with k-anonymity and differential privacy."""

    def __init__(self, k_threshold: int = 50, epsilon: float = 0.5):
        """
        Args:
            k_threshold: Minimum cohort observations required (k >= 50).
            epsilon: Differential privacy privacy budget for Laplace noise.
        """
        self.k_threshold = k_threshold
        self.epsilon = epsilon
        self.scale = 1.0 / max(0.01, epsilon)

    def _add_laplace_noise(self, value: float) -> float:
        """Draws noise from Laplace(0, 1/epsilon)."""
        u = random.uniform(-0.5, 0.5)
        # Inverse CDF of Laplace
        noise = -self.scale * math.copysign(1.0, u) * math.log(1.0 - 2.0 * abs(u) + 1e-9)
        return max(0.0, value + noise)

    def aggregate_cohort(self, posts: list[dict], cohort_name: str = "global") -> dict:
        """
        Aggregates coarse demographic distributions for a group of posts.
        Suppresses any cell with count < k_threshold and injects Laplace noise.
        """
        total_posts = len(posts)
        if total_posts < self.k_threshold:
            return {
                "cohort_name": cohort_name,
                "status": "suppressed",
                "reason": f"Cohort size {total_posts} is below privacy threshold k >= {self.k_threshold}",
                "k_threshold": self.k_threshold,
                "distributions": {}
            }

        region_counts = defaultdict(int)
        interest_counts = defaultdict(int)
        timezone_activity = {"morning (06-12)": 0, "afternoon (12-18)": 0, "evening (18-24)": 0, "night (00-06)": 0}

        for p in posts:
            # 1. Coarse linguistic region
            lang = p.get("lang") or p.get("lang_hint") or "en"
            region = LANG_TO_REGION.get(lang, "Other Global Regions")
            region_counts[region] += 1

            # 2. General interest category
            text = (p.get("text") or "").lower()
            matched_cat = "General Discussion"
            for cat, keywords in INTEREST_CATEGORIES.items():
                if any(kw in text for kw in keywords):
                    matched_cat = cat
                    break
            interest_counts[matched_cat] += 1

            # 3. Coarse activity bucket
            created_at = p.get("created_at")
            hour = 12
            if hasattr(created_at, "hour"):
                hour = created_at.hour
            elif isinstance(created_at, str) and "T" in created_at:
                try:
                    hour = int(created_at.split("T")[1].split(":")[0])
                except (IndexError, ValueError):
                    hour = 12

            if 6 <= hour < 12:
                timezone_activity["morning (06-12)"] += 1
            elif 12 <= hour < 18:
                timezone_activity["afternoon (12-18)"] += 1
            elif 18 <= hour < 24:
                timezone_activity["evening (18-24)"] += 1
            else:
                timezone_activity["night (00-06)"] += 1

        # Apply Cell Suppression (< k) and Laplace Differential Privacy Noise
        sanitized_regions = {}
        for r, count in region_counts.items():
            if count >= self.k_threshold:
                sanitized_regions[r] = round(self._add_laplace_noise(count), 1)
            else:
                sanitized_regions[r] = "suppressed (< k)"

        sanitized_interests = {}
        for cat, count in interest_counts.items():
            if count >= self.k_threshold:
                sanitized_interests[cat] = round(self._add_laplace_noise(count), 1)
            else:
                sanitized_interests[cat] = "suppressed (< k)"

        sanitized_activity = {}
        for bucket, count in timezone_activity.items():
            if count >= self.k_threshold:
                sanitized_activity[bucket] = round(self._add_laplace_noise(count), 1)
            else:
                sanitized_activity[bucket] = "suppressed (< k)"

        return {
            "cohort_name": cohort_name,
            "status": "published",
            "total_observed": total_posts,
            "k_threshold": self.k_threshold,
            "differential_privacy_epsilon": self.epsilon,
            "distributions": {
                "regions": sanitized_regions,
                "interests": sanitized_interests,
                "temporal_activity": sanitized_activity
            }
        }


demographics_engine = PrivacyPreservingDemographics()
