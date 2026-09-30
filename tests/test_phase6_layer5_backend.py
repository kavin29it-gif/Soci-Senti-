"""
Phase 6 (Layer 5 Backend) Test Suite:
Validates Case Management Lifecycle, Reviewer Approval Enforcement,
Investigation Timeline, ReportLab PDF Export, STR Draft Template,
Explainable Risk API, Cryptographic Audit & Evidence Endpoints, and Copilot v2 Stub.
"""

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.fusion.evidence import EvidenceManager


@pytest.fixture(scope="module")
def api_client():
    with TestClient(app) as c:
        yield c


def test_api_health_and_dashboard_overview(api_client):
    res_health = api_client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    res_dash = api_client.get("/dashboard/overview")
    assert res_dash.status_code == 200
    dash_data = res_dash.json()
    assert "kpis" in dash_data
    assert "volume_by_platform" in dash_data
    assert "sentiment_distribution" in dash_data
    assert "top_emerging_topics" in dash_data
    assert "top_risky_entities" in dash_data


def test_case_lifecycle_and_reviewer_approval_enforcement(api_client):
    # 1. Create a case
    create_payload = {
        "title": "Suspicious Flash Mob Formation #204",
        "description": "Cluster of 18 accounts coordinating flash mob near municipal utility.",
        "priority": "high",
        "created_by": "analyst@socisenti.local",
        "entity_type": "cluster",
        "entity_id": "cluster_flash_01"
    }
    res_create = api_client.post("/cases", json=create_payload)
    assert res_create.status_code == 200
    case_data = res_create.json()
    case_id = case_data["id"]
    assert case_data["status"] == "open"
    assert case_data["reviewer_approved"] is False

    # 2. Add an investigation note
    res_note = api_client.post(f"/cases/{case_id}/notes", json={"note": "Confirmed geolocation overlap."})
    assert res_note.status_code == 200
    assert res_note.json()["note"] == "Confirmed geolocation overlap."

    # 3. Transition to 'investigating' and 'review'
    res_inv = api_client.patch(f"/cases/{case_id}", json={"status": "investigating"})
    assert res_inv.status_code == 200
    assert res_inv.json()["status"] == "investigating"

    res_rev = api_client.patch(f"/cases/{case_id}", json={"status": "review"})
    assert res_rev.status_code == 200

    # 4. REVIEWER APPROVAL ENFORCEMENT: Attempting to close without approval must be rejected (403)
    res_fail_close = api_client.patch(f"/cases/{case_id}", json={"status": "closed_confirmed"})
    assert res_fail_close.status_code == 403
    assert "Reviewer approval is strictly required" in res_fail_close.json()["detail"]

    # 5. Reviewer approves the case
    res_app = api_client.post(f"/cases/{case_id}/approve")
    assert res_app.status_code == 200
    assert res_app.json()["case"]["reviewer_approved"] is True

    # 6. Now closure succeeds
    res_close = api_client.patch(f"/cases/{case_id}", json={"status": "closed_confirmed"})
    assert res_close.status_code == 200
    assert res_close.json()["status"] == "closed_confirmed"

    # 7. Check timeline has all recorded events
    res_timeline = api_client.get(f"/cases/{case_id}/timeline")
    assert res_timeline.status_code == 200
    timeline = res_timeline.json()["timeline"]
    assert len(timeline) >= 4
    event_names = [e["event"] for e in timeline]
    assert "case_created" in event_names
    assert "note_added" in event_names
    assert "reviewer_approved" in event_names
    assert "status_changed" in event_names


def test_pdf_dossier_and_str_draft_export(api_client):
    cases_res = api_client.get("/cases")
    cases = cases_res.json()["cases"]
    assert len(cases) > 0
    case_id = cases[0]["id"]

    # 1. Export PDF Dossier
    res_pdf = api_client.get(f"/cases/{case_id}/export/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    pdf_bytes = res_pdf.content
    assert pdf_bytes.startswith(b"%PDF-"), "Exported content must be a valid PDF file"
    assert len(pdf_bytes) > 2000, f"PDF file too small ({len(pdf_bytes)} bytes)"

    # 2. Export STR Draft Template
    res_str = api_client.get(f"/cases/{case_id}/export/str")
    assert res_str.status_code == 200
    str_data = res_str.json()
    assert str_data["template_type"] == "SUSPICIOUS_TRANSACTION_ACTIVITY_REPORT_DRAFT"
    assert "regulatory_disclaimer" in str_data
    assert "NOT an official filing" in str_data["regulatory_disclaimer"]
    assert len(str_data["report_fingerprint_sha256"]) == 64


def test_explainable_risk_endpoint(api_client):
    res_risk = api_client.get("/risk/post/post_sample_01")
    assert res_risk.status_code == 200
    data = res_risk.json()
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 100.0
    assert data["risk_band"] in ["Low", "Medium", "High"]
    assert "explanation" in data
    assert len(data["explanation"]) > 10
    assert "drivers" in data


def test_evidence_and_audit_endpoints(api_client):
    # 1. Audit Chain Verification
    res_audit = api_client.get("/audit/verify")
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert audit_data["valid"] is True
    assert audit_data["total_records"] > 0

    # 2. Evidence Fingerprint Verification
    ev_item = EvidenceManager.create_evidence_item(
        entity_type="post",
        entity_id="sample_p101",
        source_url="https://reddit.com/r/crypto/p101",
        content_snapshot="Guaranteed pump operation at midnight."
    )
    res_ev_valid = api_client.post("/evidence/verify", json=ev_item)
    assert res_ev_valid.status_code == 200
    assert res_ev_valid.json()["verified"] is True

    # Mutate snapshot -> verification must report failure
    tampered_ev = ev_item.copy()
    tampered_ev["content_snapshot"] = "Guaranteed benign discussion."
    res_ev_invalid = api_client.post("/evidence/verify", json=tampered_ev)
    assert res_ev_invalid.status_code == 200
    assert res_ev_invalid.json()["verified"] is False

    # 3. Merkle Inclusion Proof
    res_proof = api_client.get("/evidence/sample_p101/proof")
    assert res_proof.status_code == 200
    proof_data = res_proof.json()
    assert proof_data["verified"] is True
    assert len(proof_data["merkle_root"]) == 64
    assert len(proof_data["proof_path"]) > 0


def test_copilot_v2_stub_returns_501(api_client):
    res_copilot = api_client.post("/copilot/query")
    assert res_copilot.status_code == 501
    assert "# TODO(v2)" in res_copilot.json()["detail"]
