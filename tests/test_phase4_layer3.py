"""
Phase 4 (Layer 3) Test Suite:
Validates Sentiment & Emotion Engine (RoBERTa fallback, z-score shift detection),
Privacy-Preserving Aggregate Demographics (k >= 50, Laplace noise, NO per-user PII persisted),
Trend & Narrative Detection (c-TF-IDF, growth velocity, forecasting),
and Network & Influence Analysis (NetworkX, PageRank, Louvain communities, GraphSAGE v2 stub).
"""

import json

import pytest

from services.analytics.demographics import PrivacyPreservingDemographics
from services.analytics.network import GraphSAGEEmbedder, NetworkAnalysisEngine
from services.analytics.run import run_analytics_pipeline
from services.analytics.sentiment import SentimentEmotionEngine
from services.analytics.trends import TrendNarrativeEngine
from services.ingestion.streaming import stream_manager
from services.processing.store import post_store


def test_sentiment_and_emotion_classification():
    engine = SentimentEmotionEngine()

    # Positive sample
    pos_res = engine.analyze("Amazing victory! Brilliant achievement and wonderful progress.")
    assert pos_res["sentiment"]["label"] == "pos"
    assert pos_res["sentiment"]["pos"] > pos_res["sentiment"]["neg"]
    assert pos_res["emotion"]["dominant"] in ["joy", "surprise"]

    # Negative panic sample
    neg_res = engine.analyze("Catastrophic bank run and liquidity collapse! Panic and terror at the branch!")
    assert neg_res["sentiment"]["label"] == "neg"
    assert neg_res["sentiment"]["neg"] > neg_res["sentiment"]["pos"]
    assert neg_res["emotion"]["dominant"] in ["fear", "anger", "sadness"]

    # Sarcasm heuristic sample
    sarcasm_res = engine.analyze('"Great" job causing a complete market crash! Wonderful work!')
    assert sarcasm_res["sarcasm_flag"] is True


def test_sentiment_timeline_shift_detection():
    engine = SentimentEmotionEngine()
    topic = "crypto_market"

    # Feed normal positive/neutral baseline (15 scores around +0.4)
    for _ in range(15):
        engine.detect_sentiment_shift(topic, 0.40)

    # Sudden severe negative drop (anomaly)
    shift_result = engine.detect_sentiment_shift(topic, -0.90)
    assert shift_result["shift_detected"] is True
    assert shift_result["z_score"] <= -2.0
    assert shift_result["status"] == "alert_sudden_negative_shift"


def test_privacy_preserving_demographics_k_anonymity_and_suppression():
    engine = PrivacyPreservingDemographics(k_threshold=50, epsilon=0.5)

    # Cohort with 20 posts (< 50) must be suppressed
    small_cohort = [{"lang": "en", "text": "Normal post"} for _ in range(20)]
    small_res = engine.aggregate_cohort(small_cohort, cohort_name="small_group")
    assert small_res["status"] == "suppressed"
    assert "below privacy threshold" in small_res["reason"]
    assert small_res["distributions"] == {}

    # Cohort with 80 posts (>= 50) must be published
    large_cohort = [{"lang": "en", "text": "Technology and code software", "created_at": "2026-09-30T10:00:00"} for _ in range(80)]
    large_res = engine.aggregate_cohort(large_cohort, cohort_name="large_group")
    assert large_res["status"] == "published"
    assert "distributions" in large_res
    assert large_res["k_threshold"] == 50


def test_strict_privacy_rule_no_per_user_demographic_persisted():
    """
    CRITICAL PRIVACY TEST:
    Asserts that neither authors nor posts table schema in the database store
    contains individual demographic fields (e.g. age, gender, race, religion, sexual_orientation).
    """
    import sqlite3
    with sqlite3.connect(post_store.db_path) as conn:
        cursor = conn.cursor()

        # Check posts columns
        cursor.execute("PRAGMA table_info(posts)")
        post_cols = [row[1].lower() for row in cursor.fetchall()]

        # Check authors columns
        cursor.execute("PRAGMA table_info(authors)")
        author_cols = [row[1].lower() for row in cursor.fetchall()]

    forbidden_pii_fields = [
        "age", "gender", "race", "ethnicity", "religion", "sexual_orientation",
        "political_affiliation", "disability", "health", "biometrics"
    ]

    for field in forbidden_pii_fields:
        assert field not in post_cols, f"Forbidden demographic field '{field}' found in posts schema!"
        assert field not in author_cols, f"Forbidden demographic field '{field}' found in authors schema!"


def test_trend_and_narrative_detection():
    engine = TrendNarrativeEngine(num_topics=4)
    with open("data/sample/sample_posts.json", "r", encoding="utf-8") as f:
        sample_posts = json.load(f)[:200]

    topics = engine.fit_transform(sample_posts)
    assert len(topics) >= 2
    for t in topics:
        assert "topic_id" in t
        assert "label" in t
        assert len(t["top_keywords"]) > 0
        assert t["post_count"] > 0
        assert len(t["forecast_volume"]) == 3
        assert isinstance(t["is_emerging"], bool)


def test_network_analysis_engine_and_coordinated_clusters():
    engine = NetworkAnalysisEngine()
    with open("data/sample/sample_posts.json", "r", encoding="utf-8") as f:
        sample_posts = json.load(f)[:300]

    graph, analysis = engine.build_interaction_graph(sample_posts)
    assert graph.number_of_nodes() > 0
    assert analysis["node_count"] == graph.number_of_nodes()
    assert len(analysis["top_influencers"]) > 0

    # Ensure PageRank scores are valid
    top_score = analysis["top_influencers"][0]["influence_score"]
    assert top_score >= 0.0

    # Coordinated cluster detection
    assert "coordinated_clusters" in analysis
    assert "coordinated_cluster_count" in analysis


def test_graphsage_stub_raises_not_implemented():
    sage = GraphSAGEEmbedder()
    import networkx as nx
    G = nx.Graph()
    G.add_edge("user_1", "user_2")

    with pytest.raises(NotImplementedError) as exc:
        sage.embed_nodes(G)
    assert "# TODO(v2)" in str(exc.value)


def test_analytics_runner_pipeline():
    stream_manager.clear()
    results = run_analytics_pipeline(limit=100)

    assert results["analyzed_posts"] == 100
    assert "sentiment_summary" in results
    assert "demographics" in results
    assert "topics" in results
    assert "network" in results

    # Verify published to analysis.results Kafka topic
    messages = stream_manager.get_messages("analysis.results")
    assert len(messages) >= 1
    assert messages[-1]["analyzed_posts"] == 100
