"""
Phase 5 (Layer 4) Test Suite:
Validates Risk Scoring Fusion Meta-Model, SHAP Explainability & Reason Generation,
Evidence Canonical Hashing & Snapshot Tamper Verification,
Insert-Only Cryptographic Audit Hash Chain Tamper Tests,
and Binary Merkle Trees & Inclusion Proofs.
"""

import pytest

from services.fusion.audit import AuditChainManager
from services.fusion.evidence import EvidenceManager
from services.fusion.explainer import SHAPExplainer
from services.fusion.merkle import AnchorService, MerkleTree
from services.fusion.scorer import RiskScorer


def test_multimodal_risk_scorer_bands_and_confidence():
    scorer = RiskScorer(low_max=39.0, medium_max=69.0)

    # 1. High risk entity simulation
    high_res = scorer.score_entity(
        entity_type="post",
        entity_id="post_high_100",
        class_probs={"benign": 0.05, "suspicious": 0.15, "high_risk": 0.80},
        anomaly_score=0.85,
        neg_sentiment_prob=0.90,
        narrative_velocity=0.75,
        coordination_score=0.90
    )
    assert high_res["risk_score"] >= 70.0
    assert high_res["risk_band"] == "High"
    assert high_res["confidence_band"]["lower"] <= high_res["risk_score"] <= high_res["confidence_band"]["upper"]
    assert 0.50 <= high_res["confidence"] <= 0.99

    # 2. Benign entity simulation
    benign_res = scorer.score_entity(
        entity_type="post",
        entity_id="post_benign_200",
        class_probs={"benign": 0.95, "suspicious": 0.05, "high_risk": 0.0},
        anomaly_score=0.05,
        neg_sentiment_prob=0.10,
        narrative_velocity=0.0,
        coordination_score=0.0
    )
    assert benign_res["risk_score"] <= 39.0
    assert benign_res["risk_band"] == "Low"


def test_shap_explainer_feature_attribution_and_templates():
    explainer = SHAPExplainer()

    post = {
        "text": "URGENT ALERT: Bank run at NordicCapital! Withdraw your liquid assets before 4 PM freeze!",
        "platform": "telegram",
        "spam_score": 0.1,
        "engagement": {"likes": 200, "shares": 50, "replies": 10},
        "raw_payload": {"simulated_tag": "coordinated_burst"}
    }

    explanation = explainer.explain_post(post, risk_score=85.0)

    assert "top_positive_drivers" in explanation
    assert len(explanation["top_positive_drivers"]) > 0
    assert "plain_language_explanation" in explanation

    exp_text = explanation["plain_language_explanation"]
    assert "High risk score" in exp_text
    assert "driven by" in exp_text


def test_evidence_canonical_hashing_and_tamper_detection():
    # 1. Create canonical evidence item
    evidence = EvidenceManager.create_evidence_item(
        entity_type="post",
        entity_id="post_coord_0001",
        source_url="https://telegram.me/intel/coord_0001",
        content_snapshot="Systemic liquidity crisis hitting NordicCapital. Accounts frozen!",
        metadata={"channel": "intel_feed"}
    )

    assert len(evidence["sha256"]) == 64

    # 2. Verify untampered evidence
    is_valid, msg = EvidenceManager.verify_integrity(evidence)
    assert is_valid is True
    assert "Integrity verified" in msg

    # 3. TAMPER TEST: Modify content snapshot by even 1 character
    tampered_evidence = evidence.copy()
    tampered_evidence["content_snapshot"] = "Systemic liquidity crisis hitting NordicCapital. Accounts active!"

    is_valid_tampered, tamper_msg = EvidenceManager.verify_integrity(tampered_evidence)
    assert is_valid_tampered is False
    assert "TAMPERING DETECTED" in tamper_msg


def test_cryptographic_audit_hash_chain_and_tamper_detection():
    manager = AuditChainManager()

    # Append 4 sequential audit actions
    r1 = manager.append_entry("analyst_1", "view_post", "post", "p101")
    r2 = manager.append_entry("analyst_1", "flag_risk", "post", "p101", {"score": 88})
    r3 = manager.append_entry("reviewer_2", "approve_case", "case", "c505")
    r4 = manager.append_entry("analyst_1", "export_pdf", "case", "c505")

    chain = [r1, r2, r3, r4]

    # 1. Verify untampered chain
    valid, broken_id, msg = AuditChainManager.verify_chain(chain)
    assert valid is True
    assert broken_id is None
    assert "Audit chain valid" in msg

    # 2. TAMPER TEST 1: Direct modification of row payload
    tampered_chain_1 = [r.copy() for r in chain]
    tampered_chain_1[1]["payload"] = {"score": 30}  # Altered flagged score

    valid_t1, broken_id_t1, msg_t1 = AuditChainManager.verify_chain(tampered_chain_1)
    assert valid_t1 is False
    assert broken_id_t1 == 2
    assert "Row contents altered" in msg_t1

    # 3. TAMPER TEST 2: Deletion of intermediate row
    tampered_chain_2 = [chain[0], chain[2], chain[3]]  # Deleted row 2

    valid_t2, broken_id_t2, msg_t2 = AuditChainManager.verify_chain(tampered_chain_2)
    assert valid_t2 is False
    assert broken_id_t2 == 3
    assert "Broken prev_hash link" in msg_t2


def test_binary_merkle_tree_inclusion_proofs_and_verification():
    leaf_hashes = [
        "a" * 64,
        "b" * 64,
        "c" * 64,
        "d" * 64
    ]

    tree = MerkleTree(leaf_hashes)
    root = tree.root

    assert len(root) == 64
    assert root != leaf_hashes[0]

    # Generate and verify inclusion proof for leaf 1 ("b" * 64)
    target_idx = 1
    proof = tree.get_inclusion_proof(target_idx)
    assert len(proof) == 2  # tree depth for 4 leaves is 2

    is_proven = MerkleTree.verify_proof(leaf_hashes[target_idx], proof, root)
    assert is_proven is True

    # Tampered leaf proof verification must fail
    fake_leaf = "f" * 64
    is_fake_proven = MerkleTree.verify_proof(fake_leaf, proof, root)
    assert is_fake_proven is False


def test_anchor_service_v2_stub_raises():
    anchor = AnchorService()
    with pytest.raises(NotImplementedError) as exc:
        anchor.anchor_merkle_root("1" * 64, "case_123")
    assert "# TODO(v2)" in str(exc.value)
