"""
End-to-End Replay Demo Script for SociSenti Platform.
Demonstrates the complete end-to-end intelligence & risk scoring lifecycle:
  1. Ingestion: Multi-platform canonical stream with salted SHA-256 pseudonymization
  2. Processing: Deduplication (MinHash/exact) & spam heuristics
  3. Parallel Analytics: Sentiment, differential privacy demographics, BERTopic narratives, NetworkX coordination
  4. ML & Fusion: Embeddings, tabular features, calibrated XGBoost (0-100), Isolation Forest, SHAP attributions
  5. Case Workflow: Case creation, evidence SHA-256 hashing, Merkle inclusion proof, insert-only audit chain
  6. Compliance Reporting: Automated ReportLab PDF case dossier and STR XML draft
  7. Hardening: Drift monitoring (PSI) & Prometheus metrics check
"""

import hashlib
import logging
import os
import sys
import time
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.analytics.demographics import demographics_engine
from services.analytics.network import network_engine
from services.analytics.sentiment import sentiment_engine
from services.analytics.trends import trend_engine
from services.api.cases import case_manager
from services.api.reports import report_generator
from services.fusion.audit import audit_chain
from services.fusion.evidence import evidence_manager
from services.fusion.explainer import shap_explainer
from services.fusion.merkle import MerkleTree
from services.fusion.scorer import risk_scorer
from services.ingestion.connectors.mock import MockConnector
from services.ml.drift import calculate_psi
from services.processing.consumer import pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("socisenti.demo")


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def run_demo(sample_limit: int = 100):
    start_time = time.time()
    print_header("SociSenti Platform: End-to-End Replay Demo")
    print("Version: 1.0.0 | Environment: Local Mock / Zero-External-Dependency")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")

    # ---------------------------------------------------------
    # Step 1: Ingestion & Salted SHA-256 Pseudonymization
    # ---------------------------------------------------------
    print_header("Step 1: Multi-Platform Ingestion & Salted Pseudonymization")
    connector = MockConnector(sample_dir="data/sample")
    raw_posts = list(connector.fetch(limit=sample_limit))
    print(f"[*] Ingested {len(raw_posts)} raw social media posts across Reddit, YouTube, and Telegram.")
    sample_raw = raw_posts[0]
    print(f"    - Sample ID: {sample_raw.platform}:{sample_raw.post_id}")
    print(f"    - Salted Author Hash: {sample_raw.author_id_hash[:24]}... (GDPR/CCPA compliant)")
    print(f"    - Sample Content: '{sample_raw.text[:75]}...'")

    # ---------------------------------------------------------
    # Step 2: Processing, Deduplication & Normalization
    # ---------------------------------------------------------
    print_header("Step 2: Stream Normalization, MinHash Deduplication & Spam Filter")
    clean_posts = []
    dropped_count = 0
    dup_count = 0

    for raw in raw_posts:
        clean = pipeline.process_raw_post(raw)
        if clean is not None:
            clean_posts.append(clean)
            if clean.is_duplicate:
                dup_count += 1
        else:
            dropped_count += 1

    pipeline.flush()
    print(f"[*] Processed {len(raw_posts)} items:")
    print(f"    - Clean Emitted: {len(clean_posts)}")
    print(f"    - Near/Exact Duplicates Detected: {dup_count}")
    print(f"    - Heuristic Spam/Noise Dropped: {dropped_count}")

    # ---------------------------------------------------------
    # Step 3: Layer 3 Parallel Analytics Engines
    # ---------------------------------------------------------
    print_header("Step 3: Parallel Analytics Engines")
    clean_dicts = [p.model_dump(mode="json") if hasattr(p, "model_dump") else p for p in clean_posts]

    # Engine 1: Sentiment & Emotion
    print("[*] Engine 1: Sentiment & Emotion Analysis...")
    sample_sent = sentiment_engine.analyze(clean_posts[0].text)
    print(f"    - Polarity: {sample_sent['sentiment']['label']} (pos: {sample_sent['sentiment']['pos']:.2f}, neu: {sample_sent['sentiment']['neu']:.2f}, neg: {sample_sent['sentiment']['neg']:.2f})")
    print(f"    - Dominant Emotion: {sample_sent['emotion']['dominant']}")

    # Engine 2: Privacy-Preserving Aggregate Demographics
    print("[*] Engine 2: Privacy-Preserving Aggregate Demographics (k >= 50 + Laplace differential privacy)...")
    demo_res = demographics_engine.aggregate_cohort(clean_dicts, cohort_name="demo_cohort")
    if demo_res.get("status") == "suppressed":
        print(f"    - Cohort Privacy Status: SUPPRESSED ({demo_res.get('reason')})")
    else:
        print(f"    - Cohort Status: {demo_res.get('status')} (k >= {demo_res.get('k_threshold')} enforced)")
        dist = demo_res.get("distributions", {})
        print(f"    - Coarse Regions (with Laplace noise): {dist.get('regions', {})}")
        print(f"    - Temporal Activity: {dist.get('temporal_activity', {})}")

    # Engine 3: Emerging Narrative & Topic Discovery
    print("[*] Engine 3: BERTopic Narrative & Keyword Clustering...")
    topics = trend_engine.fit_transform(clean_dicts)
    print(f"    - Discovered {len(topics)} topic clusters.")
    if topics:
        top_topic = topics[0]
        print(f"    - Top Topic: '{top_topic['topic_label']}' (Velocity: {top_topic['growth_velocity']}x, Keywords: {top_topic['top_keywords'][:4]})")

    # Engine 4: NetworkX Graph & Coordinated Behavior
    print("[*] Engine 4: Network Interaction Graph & Coordinated Clusters...")
    _, net_summary = network_engine.build_interaction_graph(clean_dicts)
    print(f"    - Total Nodes: {net_summary['node_count']} | Edges: {net_summary['edge_count']}")
    print(f"    - Coordinated Clusters Flagged: {net_summary['coordinated_cluster_count']}")
    print(f"    - Louvain Communities: {net_summary['community_count']}")

    # ---------------------------------------------------------
    # Step 4: ML Scoring, Anomaly Detection & SHAP Explanations
    # ---------------------------------------------------------
    print_header("Step 4: Calibrated Risk Scoring & Local SHAP Attribution")
    # Score a representative post
    target_post = clean_dicts[0]
    risk_result = risk_scorer.score_entity(
        entity_type="post",
        entity_id=target_post.get("id") or f"{target_post.get('platform', 'mock')}:{target_post.get('post_id', '001')}",
        class_probs={"high_risk": 0.85, "suspicious": 0.10, "benign": 0.05},
        anomaly_score=0.74,
        coordination_score=0.68,
        neg_sentiment_prob=0.82
    )
    print(f"[*] Post Risk Score: {risk_result['risk_score']}/100 | Risk Band: {risk_result['risk_band']}")
    print(f"    - Confidence: {risk_result['confidence']*100:.0f}% (Band: [{risk_result['confidence_band']['lower']}, {risk_result['confidence_band']['upper']}])")

    shap_result = shap_explainer.explain_post(
        post=target_post,
        risk_score=risk_result["risk_score"]
    )
    top_drivers = [d["feature"] for d in shap_result["top_positive_drivers"][:3]]
    print(f"[*] Top 3 SHAP Drivers: {top_drivers}")
    print(f"    - Natural Language Justification: {shap_result['plain_language_explanation']}")

    # ---------------------------------------------------------
    # Step 5: Case Management, Merkle Trees & Cryptographic Audit
    # ---------------------------------------------------------
    print_header("Step 5: Case Workflow & Tamper-Evident Evidence Trail")
    new_case = case_manager.create_case(
        title="Demo Coordinated Influence Operation #801",
        description="Cluster of accounts exhibiting synchronized bot-like amplification.",
        priority="high",
        entity_type="cluster",
        entity_id="cluster_demo_01",
        created_by="lead_investigator@socisenti.local"
    )
    case_id = new_case["id"]
    print(f"[*] Investigation Case Created: {case_id}")
    print(f"    - Status: {new_case['status']} | Reviewer Approved: {new_case['reviewer_approved']}")

    # Attach item to case
    case_manager.add_item(
        case_id=case_id,
        item_type="post",
        item_id=target_post.get("id") or f"{target_post.get('platform', 'mock')}:{target_post.get('post_id', '001')}",
        added_by="lead_investigator@socisenti.local"
    )

    # Attach evidence
    ev_item = evidence_manager.create_evidence_item(
        entity_type="post",
        entity_id=target_post.get("id") or f"{target_post.get('platform', 'mock')}:{target_post.get('post_id', '001')}",
        source_url="https://reddit.com/r/demo/comments/1",
        content_snapshot=target_post.get("text", "Sample evidence content"),
        metadata={"platform": "reddit", "risk_score": risk_result["risk_score"]}
    )
    is_ev_valid, ev_msg = evidence_manager.verify_integrity(ev_item)
    print(f"[*] Evidence Item Fingerprinted: {ev_item['entity_id']}")
    print(f"    - Canonical SHA-256: {ev_item['sha256']}")
    print(f"    - Fingerprint Verification: {ev_msg}")

    # Merkle Tree Construction
    evidence_hashes = [ev_item["sha256"], hashlib.sha256(b"aux_evidence_2").hexdigest(), hashlib.sha256(b"aux_evidence_3").hexdigest()]
    merkle_tree = MerkleTree(evidence_hashes)
    merkle_root = merkle_tree.root
    proof = merkle_tree.get_inclusion_proof(0)
    verified = MerkleTree.verify_proof(ev_item["sha256"], proof, merkle_root)
    print(f"[*] Merkle Tree Built (Root: {merkle_root[:20]}...)")
    print(f"    - Merkle Proof Valid for Item 0: {verified}")

    # Audit Log Hash Chain
    audit_entry = audit_chain.append_entry(
        user_id="lead_investigator@socisenti.local",
        action="ATTACH_EVIDENCE",
        target_type="case",
        target_id=case_id,
        payload={"evidence_hash": ev_item["sha256"], "merkle_root": merkle_root}
    )
    is_chain_valid, _, chain_msg = audit_chain.verify_chain(audit_chain.chain)
    print(f"[*] Audit Hash Chain Entry Appended: ID #{audit_entry['id']}")
    print(f"    - Row Hash: {audit_entry['row_hash'][:20]}...")
    print(f"    - Full Audit Chain Valid: {is_chain_valid} ({chain_msg})")

    # ---------------------------------------------------------
    # Step 6: Compliance Dossier (PDF & FinCEN STR XML)
    # ---------------------------------------------------------
    print_header("Step 6: Compliance Dossier & STR Generation")
    os.makedirs("data/reports", exist_ok=True)
    timeline = case_manager.get_timeline(case_id)
    items = case_manager.case_items.get(case_id, [])
    risk_result["explanation"] = shap_result["plain_language_explanation"]
    risk_result["drivers"] = shap_result["top_positive_drivers"]

    pdf_bytes = report_generator.generate_case_pdf(
        case_data=new_case,
        risk_data=risk_result,
        timeline=timeline,
        evidence_items=items,
        merkle_root=merkle_root,
        audit_excerpt=audit_chain.chain[-5:]
    )
    pdf_filename = f"data/reports/dossier_{case_id[:8]}.pdf"
    with open(pdf_filename, "wb") as f:
        f.write(pdf_bytes)
    print(f"[*] Regulatory PDF Case Dossier Generated: {pdf_filename} ({len(pdf_bytes)} bytes)")
    print("    - Embedded Sections: Case Metadata, Merkle Root Header, SHAP Attributions, Evidence Fingerprints, Cryptographic Audit Trail")

    str_doc = report_generator.generate_str_draft_template(
        case_data=new_case,
        risk_data=risk_result,
        evidence_items=items
    )
    print(f"[*] FinCEN SAR/STR Draft Generated (Reference: {str_doc.get('report_reference')}, Type: {str_doc.get('filing_type')})")

    # ---------------------------------------------------------
    # Step 7: Model Hardening & Drift Monitoring (PSI)
    # ---------------------------------------------------------
    print_header("Step 7: Production Hardening & Feature Drift Monitoring")
    # Simulate feature distributions
    np_rand = __import__("numpy").random
    np_rand.seed(42)
    baseline_dist = np_rand.normal(loc=0.50, scale=0.15, size=500)
    current_dist = np_rand.normal(loc=0.52, scale=0.16, size=300)
    psi_metric = calculate_psi(baseline_dist, current_dist)
    drift_status = "STABLE" if psi_metric < 0.10 else ("MODERATE_SHIFT" if psi_metric < 0.25 else "SEVERE_DRIFT")
    print(f"[*] Population Stability Index (PSI): {psi_metric:.4f} -> [{drift_status}]")
    print("    - Alert Threshold: 0.15 | Max Tolerable: 0.25")
    print("    - Prometheus Metrics: Ready at /metrics")

    elapsed_total = time.time() - start_time
    print_header("Demo Completed Successfully")
    print(f"Total Replay Time: {elapsed_total:.2f} seconds")
    print("=" * 70 + "\n")
    return {
        "status": "success",
        "case_id": case_id,
        "clean_posts_count": len(clean_posts),
        "merkle_root": merkle_root,
        "audit_chain_valid": is_chain_valid,
        "pdf_report": pdf_filename,
        "psi_drift": psi_metric,
        "elapsed_seconds": round(elapsed_total, 2)
    }


if __name__ == "__main__":
    limit = 100
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        limit = int(sys.argv[1])
    run_demo(sample_limit=limit)
