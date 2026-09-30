"""
Phase 1 Foundation Test Suite:
Validates repository layout, configuration files, SQL migrations,
docker-compose definition, Prometheus/Grafana configs, and sample dataset integrity.
"""

import json
import os

import yaml

from services.api.settings import settings as api_settings
from services.fusion.settings import settings as fusion_settings
from services.ingestion.models import RawPost
from services.ingestion.settings import settings as ingestion_settings
from services.ml.settings import settings as ml_settings
from services.processing.settings import settings as processing_settings


def test_sample_dataset_exists_and_exceeds_threshold():
    sample_file = os.path.join("data", "sample", "sample_posts.json")
    assert os.path.exists(sample_file), "Sample dataset file must exist at data/sample/sample_posts.json"

    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list), "Sample dataset must be a JSON array"
    assert len(data) >= 5000, f"Expected at least 5000 records, got {len(data)}"


def test_sample_dataset_schema_and_author_hashing():
    sample_file = os.path.join("data", "sample", "sample_posts.json")
    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    platforms = set()
    tags = set()

    # Test a representative sample of records through Pydantic validation
    for item in data[:500]:
        post = RawPost.model_validate(item)
        assert len(post.author_id_hash) == 64, "author_id_hash must be a 64-char SHA-256 string"
        assert post.author_id_hash.isalnum(), "author_id_hash must be hexadecimal"
        assert post.text.strip(), "Post text must not be empty"
        assert post.engagement.likes >= 0, "Likes must be non-negative"
        platforms.add(post.platform)
        if "simulated_tag" in post.raw_payload:
            tags.add(post.raw_payload["simulated_tag"])

    # Ensure coverage of required platforms
    assert "reddit" in platforms, "Sample data must include reddit posts"
    assert "youtube" in platforms, "Sample data must include youtube comments"
    assert "telegram" in platforms, "Sample data must include telegram messages"

    # Ensure coverage of varied narrative patterns
    assert "coordinated_burst" in tags, "Sample data must include coordinated burst clusters"
    assert "high_risk_narrative" in tags, "Sample data must include high risk narratives"
    assert "spam_bot" in tags, "Sample data must include spam bot posts"
    assert "benign_chatter" in tags, "Sample data must include benign conversations"


def test_sql_migrations_completeness():
    migration_file = os.path.join("supabase", "migrations", "20240101000000_initial_schema.sql")
    assert os.path.exists(migration_file), "Initial SQL migration file must exist"

    with open(migration_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    required_tables = [
        "profiles",
        "authors",
        "posts",
        "post_features",
        "analysis_results",
        "risk_scores",
        "cases",
        "case_items",
        "case_notes",
        "evidence_items",
        "audit_log",
        "merkle_roots"
    ]
    for table in required_tables:
        assert f"CREATE TABLE IF NOT EXISTS public.{table}" in sql_content, f"Migration missing table: {table}"

    # Verify vector extension & HNSW / pgvector
    assert 'CREATE EXTENSION IF NOT EXISTS "vector"' in sql_content
    assert "vector(384)" in sql_content
    assert "idx_post_features_embedding" in sql_content

    # Verify audit log insert-only trigger
    assert "block_audit_log_mutation" in sql_content
    assert "REVOKE UPDATE, DELETE" in sql_content

    # Verify materialized views
    assert "CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_hourly_post_volume" in sql_content
    assert "CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_hourly_sentiment" in sql_content

    # Verify RLS policies
    assert "ENABLE ROW LEVEL SECURITY" in sql_content
    assert "CREATE POLICY" in sql_content


def test_supabase_seed_file():
    seed_file = os.path.join("supabase", "seed.sql")
    assert os.path.exists(seed_file), "Seed file must exist at supabase/seed.sql"
    with open(seed_file, "r", encoding="utf-8") as f:
        seed_content = f.read()
    assert "INSERT INTO public.profiles" in seed_content
    assert "INSERT INTO public.cases" in seed_content


def test_docker_compose_valid_yaml():
    compose_file = "docker-compose.yml"
    assert os.path.exists(compose_file), "docker-compose.yml must exist"
    with open(compose_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "services" in config
    services = config["services"]
    assert "kafka" in services, "docker-compose must define kafka"
    assert "redis" in services, "docker-compose must define redis"
    assert "prometheus" in services, "docker-compose must define prometheus"
    assert "grafana" in services, "docker-compose must define grafana"
    assert "ml_serving" in services, "docker-compose must define ml_serving"
    assert "api" in services, "docker-compose must define api"


def test_monitoring_configurations():
    prom_file = os.path.join("monitoring", "prometheus.yml")
    assert os.path.exists(prom_file)
    with open(prom_file, "r", encoding="utf-8") as f:
        prom_config = yaml.safe_load(f)
    assert "scrape_configs" in prom_config

    grafana_dash = os.path.join("monitoring", "grafana", "provisioning", "dashboards", "platform_overview.json")
    assert os.path.exists(grafana_dash)
    with open(grafana_dash, "r", encoding="utf-8") as f:
        dash_config = json.load(f)
    assert dash_config.get("title") == "Platform Overview & ML Health"


def test_environment_and_service_settings():
    assert os.path.exists(".env.example")
    assert os.path.exists(".env")

    # Check that each service settings object is instantiated without error
    assert ingestion_settings.author_hash_salt
    assert processing_settings.clean_posts_topic == "clean.posts"
    assert ml_settings.port == 8001
    assert api_settings.port == 8000
    assert fusion_settings.low_band_max == 39.0
