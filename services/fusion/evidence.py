"""
Evidence Preservation and Cryptographic Hash Verification.
Generates canonical SHA-256 fingerprints of evidence items and detects tampering.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Tuple


class EvidenceManager:
    """Manages canonical evidence fingerprints and cryptographic verification."""

    @staticmethod
    def canonical_json(data: dict) -> str:
        """Returns sorted, deterministic canonical JSON string."""
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @classmethod
    def compute_sha256(cls, data: dict) -> str:
        """Computes SHA-256 over canonical JSON string."""
        raw = cls.canonical_json(data).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @classmethod
    def create_evidence_item(
        cls,
        entity_type: str,
        entity_id: str,
        source_url: str,
        content_snapshot: str,
        metadata: Optional[dict] = None
    ) -> dict:
        """Creates a timestamped evidence record with canonical SHA-256 fingerprint."""
        now_iso = datetime.now(timezone.utc).isoformat()
        core_payload = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "source_url": source_url,
            "content_snapshot": content_snapshot,
            "fetched_at": now_iso,
            "metadata": metadata or {}
        }

        fingerprint = cls.compute_sha256(core_payload)

        return {
            **core_payload,
            "sha256": fingerprint,
            "http_status": 200,
            "created_at": now_iso
        }

    @classmethod
    def verify_integrity(cls, evidence_item: dict) -> Tuple[bool, str]:
        """
        Recomputes SHA-256 from current content and verifies against stored sha256 fingerprint.
        Returns: (is_valid, status_message)
        """
        stored_hash = evidence_item.get("sha256")
        if not stored_hash:
            return False, "Missing sha256 fingerprint in evidence item"

        # Reconstruct canonical core payload
        core_payload = {
            "entity_type": evidence_item.get("entity_type"),
            "entity_id": evidence_item.get("entity_id"),
            "source_url": evidence_item.get("source_url"),
            "content_snapshot": evidence_item.get("content_snapshot"),
            "fetched_at": evidence_item.get("fetched_at"),
            "metadata": evidence_item.get("metadata", {})
        }

        recomputed_hash = cls.compute_sha256(core_payload)
        if recomputed_hash == stored_hash:
            return True, "Integrity verified: SHA-256 fingerprint matches canonical content."
        else:
            return False, (
                f"TAMPERING DETECTED: Recomputed hash ({recomputed_hash[:16]}...) does not "
                f"match recorded fingerprint ({stored_hash[:16]}...)."
            )


evidence_manager = EvidenceManager()
