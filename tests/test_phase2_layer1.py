"""
Phase 2 (Layer 1) Test Suite:
Validates Platform Connectors, Rate Limiting, Deduplication (Bloom, SimHash),
Spam Heuristics, NLP Normalization, Streaming Pipeline, and Historical Storage.
"""

import time
from datetime import datetime, timezone

import pytest

from services.ingestion.connectors.mock import MockConnector
from services.ingestion.connectors.reddit import RedditConnector
from services.ingestion.connectors.stubs import InstagramConnector, XConnector
from services.ingestion.models import Engagement, RawPost
from services.ingestion.rate_limiter import TokenBucketRateLimiter
from services.ingestion.streaming import stream_manager
from services.processing.consumer import ProcessingPipeline
from services.processing.dedup import Deduplicator, SimHash
from services.processing.nlp import NLPPipeline
from services.processing.settings import settings as proc_settings
from services.processing.spam import SpamFilter
from services.processing.store import PostStore


def test_token_bucket_rate_limiter():
    limiter = TokenBucketRateLimiter(rate=5.0, capacity=2.0)
    # First 2 tokens should be instantly available
    assert limiter.acquire("test", tokens=1.0, block=False) is True
    assert limiter.acquire("test", tokens=1.0, block=False) is True
    # Third token exceeds capacity without blocking
    assert limiter.acquire("test", tokens=1.0, block=False) is False


def test_mock_connector_yields_valid_raw_posts():
    connector = MockConnector(sample_dir="data/sample", replay_speed_factor=0.0)
    posts = list(connector.fetch(limit=25))
    assert len(posts) == 25
    for p in posts:
        assert isinstance(p, RawPost)
        assert len(p.author_id_hash) == 64
        assert p.text.strip() != ""
        assert p.platform in ["reddit", "youtube", "telegram", "mock"]


def test_v2_connector_stubs_raise_not_implemented():
    x_conn = XConnector()
    with pytest.raises(NotImplementedError) as exc_x:
        next(x_conn.fetch("crypto", limit=1))
    assert "# TODO(v2)" in str(exc_x.value)

    insta_conn = InstagramConnector()
    with pytest.raises(NotImplementedError) as exc_insta:
        next(insta_conn.fetch("explore", limit=1))
    assert "# TODO(v2)" in str(exc_insta.value)


def test_connectors_author_pseudonymization():
    reddit_conn = RedditConnector()
    hash1 = reddit_conn.hash_identifier("target_user_123")
    hash2 = reddit_conn.hash_identifier("target_user_123")
    hash3 = reddit_conn.hash_identifier("different_user_456")

    assert len(hash1) == 64
    assert hash1 == hash2, "Identical usernames must produce identical salted hashes"
    assert hash1 != hash3, "Different usernames must produce different hashes"
    assert "target_user" not in hash1, "Raw username must not leak into hash"


def test_simhash_near_duplicate_detection():
    text_base = "URGENT ALERT: Bank run reported at NordicCapital! Withdraw your deposits immediately!"
    text_variant = "URGENT ALERT: Bank run reported at NordicCapital! Withdraw your deposits quickly now!"
    text_different = "Testing out our new sourdough bread recipe with organic flour and sea salt."

    hash_base = SimHash.compute(text_base)
    hash_variant = SimHash.compute(text_variant)
    hash_diff = SimHash.compute(text_different)

    dist_near = SimHash.hamming_distance(hash_base, hash_variant)
    dist_diff = SimHash.hamming_distance(hash_base, hash_diff)

    assert dist_near <= 10, f"Near-duplicate text should have low hamming distance, got {dist_near}"
    assert dist_diff >= 20, f"Unrelated text should have large hamming distance, got {dist_diff}"


def test_bloom_filter_and_deduplicator():
    dedup = Deduplicator()
    platform = "reddit"
    post_id = "test_dup_001"

    assert dedup.is_exact_duplicate(platform, post_id) is False
    dedup.record_exact(platform, post_id)
    assert dedup.is_exact_duplicate(platform, post_id) is True


def test_spam_filter_heuristics():
    spam_filter = SpamFilter(threshold=0.70)

    # Obvious spam sample
    spam_sample = "MAKE $5000 DAILY WORK FROM HOME! FREE MONEY! Visit: http://bit.ly/scam-4827 #EasyCash $$$"
    is_spam, score, reason = spam_filter.is_spam(spam_sample)
    assert is_spam is True
    assert score >= 0.70
    assert "spam" in reason.lower() or "urls" in reason.lower()

    # Legitimate benign sample
    clean_sample = "Just published our research paper on explainable AI and SHAP values for risk detection."
    is_spam_clean, clean_score, clean_reason = spam_filter.is_spam(clean_sample)
    assert is_spam_clean is False
    assert clean_score < 0.50


def test_nlp_pipeline_extraction():
    text = "Breaking news: Coordinated pump on $AURA token reported in Zurich by @WhaleAlert! #CryptoPump"
    result = NLPPipeline.process(text)

    assert result["lang"] == "en"
    assert "breaking" in result["tokens"]
    assert "pump" in result["tokens"]
    assert "CryptoPump" in result["hashtags"]
    assert "WhaleAlert" in result["mentions"]

    labels = [e["label"] for e in result["entities"]]
    assert "CRYPTO" in labels
    assert "GPE" in labels


def test_pipeline_drops_exact_duplicates_and_dead_letter_spam(tmp_path):
    test_db = str(tmp_path / "test_pipeline.db")
    store = PostStore(db_path=test_db)
    pipe = ProcessingPipeline(store=store, spam_threshold=0.70)
    stream_manager.clear()

    raw_normal = RawPost(
        platform="reddit",
        post_id="post_unique_101",
        author_id_hash="a" * 64,
        text="Normal community question about machine learning deployment.",
        created_at=datetime.now(timezone.utc),
        engagement=Engagement(likes=10, shares=2, replies=1)
    )

    raw_duplicate = RawPost(
        platform="reddit",
        post_id="post_unique_101", # same ID
        author_id_hash="a" * 64,
        text="Normal community question about machine learning deployment.",
        created_at=datetime.now(timezone.utc),
        engagement=Engagement(likes=10, shares=2, replies=1)
    )

    raw_spam = RawPost(
        platform="telegram",
        post_id="post_spam_202",
        author_id_hash="b" * 64,
        text="MAKE $5000 WORK FROM HOME CLICK HERE http://bit.ly/spam-999 #EasyCash $$$ !",
        created_at=datetime.now(timezone.utc),
        engagement=Engagement(likes=0, shares=0, replies=0)
    )

    # 1. Process normal post -> clean
    clean_res = pipe.process_raw_post(raw_normal)
    assert clean_res is not None

    # 2. Process duplicate -> should be dropped (None)
    dup_res = pipe.process_raw_post(raw_duplicate)
    assert dup_res is None

    # 3. Process spam -> should be dropped (None) and sent to dead.letter
    spam_res = pipe.process_raw_post(raw_spam)
    assert spam_res is None
    dead_letters = stream_manager.get_messages(proc_settings.dead_letter_topic)
    assert len(dead_letters) >= 1
    assert dead_letters[-1]["post_id"] == "post_spam_202"

    pipe.flush()
    assert store.count_posts() == 1


def test_historical_store_query_performance(tmp_path):
    test_db = str(tmp_path / "perf.db")
    store = PostStore(db_path=test_db)
    connector = MockConnector(sample_dir="data/sample", replay_speed_factor=0.0)
    pipe = ProcessingPipeline(store=store)

    # Ingest 500 posts
    for raw in connector.fetch(limit=500):
        pipe.process_raw_post(raw)
    pipe.flush()

    assert store.count_posts() > 0

    # Query benchmark (< 300ms)
    t0 = time.time()
    results = store.query_posts_by_time_range(
        start_time="2020-01-01T00:00:00",
        end_time="2030-01-01T00:00:00",
        limit=100
    )
    elapsed_ms = (time.time() - t0) * 1000

    assert len(results) > 0
    assert elapsed_ms < 300.0, f"Query took {elapsed_ms:.2f} ms, expected < 300 ms"
