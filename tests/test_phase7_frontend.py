"""
Phase 7 Verification Tests: Analyst Dashboard (React 18 + Vite + Tailwind CSS) & Analytical Endpoints.
Verifies:
  - Frontend production build artifacts exist and are non-empty.
  - Gateway mounts and serves frontend static assets at root (/ and /assets).
  - Network graph endpoint (/analytics/network) returns nodes, links, and coordinated clusters.
  - Topics and emerging narrative endpoint (/analytics/topics) returns c-TF-IDF keyword clusters.
  - Model health endpoint (/ml/health) returns feature drift (PSI) and analyst precision metrics.
"""

import os

import pytest
from fastapi.testclient import TestClient

from services.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_frontend_production_build_artifacts():
    """Verifies that Vite generated the production bundle in frontend/dist."""
    dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
    assert os.path.exists(dist_dir), "frontend/dist does not exist! Run 'npm run build' inside frontend/"

    index_html = os.path.join(dist_dir, "index.html")
    assert os.path.exists(index_html), "frontend/dist/index.html is missing"

    with open(index_html, "r", encoding="utf-8") as f:
        content = f.read()
    assert "SociSenti" in content
    assert "<div id=\"root\"></div>" in content

    assets_dir = os.path.join(dist_dir, "assets")
    assert os.path.exists(assets_dir), "frontend/dist/assets is missing"
    asset_files = os.listdir(assets_dir)
    assert any(f.endswith(".js") for f in asset_files), "No JS bundle found in dist/assets"
    assert any(f.endswith(".css") for f in asset_files), "No CSS stylesheet found in dist/assets"


def test_gateway_serves_frontend_spa(client):
    """Verifies that FastAPI gateway serves the SPA at the root URL."""
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "SociSenti" in res.text


def test_analytics_network_endpoint(client):
    """Verifies that /analytics/network returns nodes, links, and clusters."""
    res = client.get("/analytics/network?limit=50")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "links" in data
    assert "coordinated_clusters" in data
    assert "community_count" in data


def test_analytics_topics_endpoint(client):
    """Verifies that /analytics/topics returns clusters with c-TF-IDF keywords."""
    res = client.get("/analytics/topics?limit=50")
    assert res.status_code == 200
    data = res.json()
    assert "topics" in data
    assert "total_posts_analyzed" in data
    if data["topics"]:
        top = data["topics"][0]
        assert "topic_label" in top
        assert "growth_velocity" in top
        assert "top_keywords" in top


def test_ml_health_drift_endpoint(client):
    """Verifies that /ml/health returns PSI drift metrics and feedback."""
    res = client.get("/ml/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "overall_psi" in data
    assert "feature_drifts" in data
    assert isinstance(data["feature_drifts"], list)
    assert "holdout_accuracy" in data
    assert data["holdout_accuracy"] > 0.90
