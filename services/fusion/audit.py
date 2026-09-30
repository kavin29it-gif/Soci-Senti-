"""
Insert-Only Cryptographic Hash-Chained Audit Log.
Maintains an immutable chain where each entry satisfies:
  row_hash = SHA256(prev_hash || canonical_payload)
Provides verify_audit_chain() walker that detects any record modification or deletion.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Tuple

GENESIS_HASH = "0" * 64


class AuditChainManager:
    """Manages hash-chained audit logging and tamper-evidence verification."""

    def __init__(self):
        self.chain: list[dict] = []
        self._last_hash = GENESIS_HASH

    @staticmethod
    def canonical_json(data: dict) -> str:
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @classmethod
    def compute_row_hash(cls, prev_hash: str, payload: dict) -> str:
        canonical_str = cls.canonical_json(payload)
        to_hash = f"{prev_hash}:{canonical_str}".encode("utf-8")
        return hashlib.sha256(to_hash).hexdigest()

    def append_entry(
        self,
        user_id: str,
        action: str,
        target_type: str,
        target_id: str,
        payload: Optional[dict] = None
    ) -> dict:
        """Appends a new audit record linked to the previous row hash."""
        now_iso = datetime.now(timezone.utc).isoformat()
        entry_data = {
            "user_id": user_id,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "payload": payload or {},
            "created_at": now_iso
        }

        row_hash = self.compute_row_hash(self._last_hash, entry_data)

        record = {
            "id": len(self.chain) + 1,
            "prev_hash": self._last_hash,
            "row_hash": row_hash,
            **entry_data
        }

        self.chain.append(record)
        self._last_hash = row_hash
        return record

    @classmethod
    def verify_chain(cls, rows: list[dict]) -> Tuple[bool, Optional[int], str]:
        """
        Traverses audit chain from genesis, verifying link and hash integrity.
        Returns: (is_valid, corrupted_row_id, details)
        """
        if not rows:
            return True, None, "Audit chain is empty."

        expected_prev = GENESIS_HASH

        for idx, row in enumerate(rows):
            stored_prev = row.get("prev_hash")
            stored_hash = row.get("row_hash")
            row_id = row.get("id", idx + 1)

            # 1. Verify previous hash pointer
            if stored_prev != expected_prev:
                return False, row_id, (
                    f"TAMPERING DETECTED at row ID {row_id}: Broken prev_hash link. "
                    f"Expected {expected_prev[:16]}..., found {stored_prev[:16]}..."
                )

            # 2. Recompute row hash from payload
            payload = {
                "user_id": row.get("user_id"),
                "action": row.get("action"),
                "target_type": row.get("target_type"),
                "target_id": row.get("target_id"),
                "payload": row.get("payload", {}),
                "created_at": row.get("created_at")
            }
            recomputed = cls.compute_row_hash(stored_prev, payload)

            if recomputed != stored_hash:
                return False, row_id, (
                    f"TAMPERING DETECTED at row ID {row_id}: Row contents altered. "
                    f"Expected hash {recomputed[:16]}..., found {stored_hash[:16]}..."
                )

            expected_prev = stored_hash

        return True, None, f"Audit chain valid across {len(rows)} immutable records."


audit_chain = AuditChainManager()
