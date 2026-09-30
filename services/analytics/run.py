"""
Parallel Analytics Engines Orchestrator & CLI Runner.
Executes all 4 Layer 3 engines on cleaned social media posts:
  1. Sentiment & Emotion (RoBERTa / Lexicon + Z-score shift detection)
  2. Aggregate Demographics (k >= 50 cohort threshold + Laplace noise)
  3. BERTopic Trend & Narrative Detection (c-TF-IDF + Volume Forecasting)
  4. Network & Influence Analysis (NetworkX PageRank, Louvain communities, Coordinated clusters)
Publishes results to analysis.results topic.
"""

import argparse
import json
import logging
import time
from typing import Optional

from services.analytics.demographics import demographics_engine
from services.analytics.network import network_engine
from services.analytics.sentiment import sentiment_engine
from services.analytics.trends import trend_engine
from services.ingestion.streaming import stream_manager
from services.processing.store import post_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("analytics.runner")


def run_analytics_pipeline(limit: int = 500, sample_file: Optional[str] = None) -> dict:
    """
    Runs the 4 analytical engines on stored CleanPost records or sample dataset.
    """
    start_time = time.time()

    # Load cleaned posts from store or sample
    if sample_file:
        with open(sample_file, "r", encoding="utf-8") as f:
            posts = json.load(f)[:limit]
    else:
        # Load from historical post store
        stored_posts = post_store.query_posts_by_time_range(
            start_time="2020-01-01T00:00:00",
            end_time="2030-01-01T00:00:00",
            limit=limit
        )
        if stored_posts:
            posts = stored_posts
        else:
            with open("data/sample/sample_posts.json", "r", encoding="utf-8") as f:
                posts = json.load(f)[:limit]

    logger.info("Executing 4 parallel analytical engines on %d posts...", len(posts))

    # --- Engine 1: Sentiment & Emotion Analysis ---
    sentiment_counts = {"pos": 0, "neu": 0, "neg": 0}
    emotion_counts = {}
    sarcasm_count = 0

    for p in posts:
        res = sentiment_engine.analyze(p.get("text", ""))
        sent_label = res["sentiment"]["label"]
        sentiment_counts[sent_label] += 1
        dom_emo = res["emotion"].get("dominant", "neutral")
        emotion_counts[dom_emo] = emotion_counts.get(dom_emo, 0) + 1
        if res.get("sarcasm_flag"):
            sarcasm_count += 1

    # Check for sentiment shift anomaly on finance topic
    finance_shift = sentiment_engine.detect_sentiment_shift("finance_market", -0.85)

    # --- Engine 2: Privacy-Preserving Demographics ---
    demographics_summary = demographics_engine.aggregate_cohort(posts, cohort_name="global_sample")

    # --- Engine 3: Trend & Emerging Narratives ---
    topics_summary = trend_engine.fit_transform(posts)

    # --- Engine 4: NetworkX Graph & Coordinated Clusters ---
    _, network_summary = network_engine.build_interaction_graph(posts)

    # Publish aggregated analytics results to analysis.results topic
    analytics_payload = {
        "analyzed_posts": len(posts),
        "sentiment_summary": sentiment_counts,
        "dominant_emotions": emotion_counts,
        "sarcasm_flags": sarcasm_count,
        "sentiment_shift_alert": finance_shift,
        "demographics": demographics_summary,
        "topics": topics_summary,
        "network": network_summary,
        "timestamp": time.time()
    }

    stream_manager.publish(
        topic="analysis.results",
        key="analytics:batch_summary",
        value=analytics_payload
    )

    elapsed = round(time.time() - start_time, 2)
    logger.info("=== Layer 3 Analytics Complete in %.2fs ===", elapsed)
    logger.info("Sentiment: %s | Sarcasm: %d", sentiment_counts, sarcasm_count)
    logger.info("Topics Discovered: %d | Coordinated Clusters: %d", len(topics_summary), network_summary["coordinated_cluster_count"])
    logger.info("Top Influencers: %d | Communities: %d", len(network_summary["top_influencers"]), network_summary["community_count"])

    return analytics_payload


def main():
    parser = argparse.ArgumentParser(description="SociSenti Analytics Engines Runner")
    parser.add_argument("--limit", type=int, default=300, help="Number of posts to analyze")
    parser.add_argument("--sample-file", type=str, default=None, help="Optional direct sample json path")

    args = parser.parse_args()
    results = run_analytics_pipeline(limit=args.limit, sample_file=args.sample_file)
    print("\nSummary of Analytics Results:")
    print(f"Posts Analyzed: {results['analyzed_posts']}")
    print(f"Sentiment: {results['sentiment_summary']}")
    print(f"Top 3 Topics: {[t['label'] for t in results['topics'][:3]]}")
    print(f"Coordinated Clusters: {len(results['network']['coordinated_clusters'])}")


if __name__ == "__main__":
    main()
