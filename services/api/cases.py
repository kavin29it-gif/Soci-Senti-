"""
Case Management & Investigation Workflow Service.
Manages case lifecycle (open -> investigating -> review -> closed),
attaches posts/evidence, maintains chronological timelines, enforces reviewer approval,
and logs all actions to the cryptographic audit chain.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from services.fusion.audit import audit_chain
from services.fusion.evidence import evidence_manager
from services.fusion.merkle import MerkleTree

logger = logging.getLogger(__name__)

VALID_STATUSES = ["open", "investigating", "review", "closed_confirmed", "closed_dismissed"]
VALID_PRIORITIES = ["low", "medium", "high", "critical"]


class CaseManager:
    """In-memory and Supabase-compatible Case Management repository."""

    def __init__(self):
        self.cases: dict[str, dict] = {}
        self.case_items: dict[str, list[dict]] = {}   # case_id -> list of items
        self.case_notes: dict[str, list[dict]] = {}   # case_id -> list of notes
        self.timelines: dict[str, list[dict]] = {}    # case_id -> chronological events
        self._seed_default_case()

    def _seed_default_case(self):
        """Initializes default demonstration case."""
        case_id = "c0000000-0000-0000-0000-000000000001"
        now_iso = datetime.now(timezone.utc).isoformat()
        self.cases[case_id] = {
            "id": case_id,
            "title": "Investigation: Coordinated Disinformation Campaign #849",
            "description": "Anomalous coordinated burst across Telegram and Reddit with elevated toxicity.",
            "status": "investigating",
            "priority": "high",
            "created_by": "analyst@socisenti.local",
            "assigned_to": "analyst@socisenti.local",
            "reviewer_approved": False,
            "approved_by": None,
            "approved_at": None,
            "created_at": now_iso,
            "updated_at": now_iso
        }
        self.case_items[case_id] = [
            {"id": "item_1", "item_type": "cluster", "item_id": "cluster_001", "created_at": now_iso}
        ]
        self.case_notes[case_id] = [
            {
                "id": "note_1",
                "author_id": "analyst@socisenti.local",
                "note": "Initial triage: Cluster of 14 accounts flagged by NetworkX Louvain detection.",
                "created_at": now_iso
            }
        ]
        self.timelines[case_id] = [
            {"event": "case_created", "user": "system", "details": "Case opened from high-risk alert", "timestamp": now_iso},
            {"event": "note_added", "user": "analyst@socisenti.local", "details": "Initial triage note added", "timestamp": now_iso}
        ]

    def create_case(
        self,
        title: str,
        description: str,
        priority: str = "medium",
        created_by: str = "analyst@socisenti.local",
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> dict:
        case_id = str(uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        priority_clean = priority.lower() if priority.lower() in VALID_PRIORITIES else "medium"

        new_case = {
            "id": case_id,
            "title": title,
            "description": description,
            "status": "open",
            "priority": priority_clean,
            "created_by": created_by,
            "assigned_to": created_by,
            "reviewer_approved": False,
            "approved_by": None,
            "approved_at": None,
            "created_at": now_iso,
            "updated_at": now_iso
        }

        self.cases[case_id] = new_case
        self.case_items[case_id] = []
        self.case_notes[case_id] = []
        self.timelines[case_id] = [
            {"event": "case_created", "user": created_by, "details": f"Created case '{title}'", "timestamp": now_iso}
        ]

        # Attach origin entity if provided
        if entity_type and entity_id:
            self.add_item(case_id, entity_type, entity_id, added_by=created_by)

        # Record in cryptographic audit log
        audit_chain.append_entry(
            user_id=created_by,
            action="create_case",
            target_type="case",
            target_id=case_id,
            payload={"title": title, "priority": priority_clean}
        )

        return new_case

    def get_case(self, case_id: str) -> Optional[dict]:
        return self.cases.get(case_id)

    def list_cases(self, status: Optional[str] = None, priority: Optional[str] = None) -> list[dict]:
        results = list(self.cases.values())
        if status:
            results = [c for c in results if c["status"] == status]
        if priority:
            results = [c for c in results if c["priority"] == priority]
        # Sort by updated_at descending
        results.sort(key=lambda x: x["updated_at"], reverse=True)
        return results

    def update_case_status(self, case_id: str, new_status: str, user_id: str = "analyst@socisenti.local") -> dict:
        case = self.get_case(case_id)
        if not case:
            raise KeyError(f"Case {case_id} not found.")

        clean_status = new_status.lower()
        if clean_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'. Allowed: {VALID_STATUSES}")

        # Reviewer approval constraint on case closure
        if clean_status in ["closed_confirmed", "closed_dismissed"] and not case["reviewer_approved"]:
            raise PermissionError("Reviewer approval is strictly required before closing an investigation case.")

        old_status = case["status"]
        now_iso = datetime.now(timezone.utc).isoformat()
        case["status"] = clean_status
        case["updated_at"] = now_iso

        # Log timeline event
        self.timelines[case_id].append({
            "event": "status_changed",
            "user": user_id,
            "details": f"Status changed from '{old_status}' to '{clean_status}'",
            "timestamp": now_iso
        })

        # Record in audit chain
        audit_chain.append_entry(
            user_id=user_id,
            action="update_case_status",
            target_type="case",
            target_id=case_id,
            payload={"old_status": old_status, "new_status": clean_status}
        )

        return case

    def approve_case(self, case_id: str, reviewer_id: str = "reviewer@socisenti.local") -> dict:
        """Grants reviewer approval to allow case closure."""
        case = self.get_case(case_id)
        if not case:
            raise KeyError(f"Case {case_id} not found.")

        now_iso = datetime.now(timezone.utc).isoformat()
        case["reviewer_approved"] = True
        case["approved_by"] = reviewer_id
        case["approved_at"] = now_iso
        case["updated_at"] = now_iso

        self.timelines[case_id].append({
            "event": "reviewer_approved",
            "user": reviewer_id,
            "details": "Compliance reviewer approved case closure.",
            "timestamp": now_iso
        })

        audit_chain.append_entry(
            user_id=reviewer_id,
            action="approve_case",
            target_type="case",
            target_id=case_id,
            payload={"approved_by": reviewer_id}
        )

        return case

    def add_item(self, case_id: str, item_type: str, item_id: str, added_by: str = "analyst@socisenti.local") -> dict:
        case = self.get_case(case_id)
        if not case:
            raise KeyError(f"Case {case_id} not found.")

        now_iso = datetime.now(timezone.utc).isoformat()
        item = {
            "id": str(uuid4()),
            "case_id": case_id,
            "item_type": item_type,
            "item_id": item_id,
            "added_by": added_by,
            "created_at": now_iso
        }
        self.case_items[case_id].append(item)

        self.timelines[case_id].append({
            "event": "item_attached",
            "user": added_by,
            "details": f"Attached {item_type} '{item_id}'",
            "timestamp": now_iso
        })

        audit_chain.append_entry(
            user_id=added_by,
            action="attach_item",
            target_type="case",
            target_id=case_id,
            payload={"item_type": item_type, "item_id": item_id}
        )
        return item

    def add_note(self, case_id: str, note_text: str, author_id: str = "analyst@socisenti.local") -> dict:
        case = self.get_case(case_id)
        if not case:
            raise KeyError(f"Case {case_id} not found.")

        now_iso = datetime.now(timezone.utc).isoformat()
        note = {
            "id": str(uuid4()),
            "case_id": case_id,
            "author_id": author_id,
            "note": note_text,
            "created_at": now_iso
        }
        self.case_notes[case_id].append(note)

        self.timelines[case_id].append({
            "event": "note_added",
            "user": author_id,
            "details": note_text[:80] + "..." if len(note_text) > 80 else note_text,
            "timestamp": now_iso
        })

        audit_chain.append_entry(
            user_id=author_id,
            action="add_note",
            target_type="case",
            target_id=case_id,
            payload={"note_snippet": note_text[:50]}
        )
        return note

    def get_timeline(self, case_id: str) -> list[dict]:
        return self.timelines.get(case_id, [])

    def compute_case_merkle_root(self, case_id: str) -> str:
        """Computes Merkle root over all evidence items attached to this case."""
        items = self.case_items.get(case_id, [])
        if not items:
            # Generate deterministic root from case ID and timestamp
            leaf_hashes = [evidence_manager.compute_sha256({"case_id": case_id})]
        else:
            leaf_hashes = [evidence_manager.compute_sha256(item) for item in items]

        tree = MerkleTree(leaf_hashes)
        return tree.root


case_manager = CaseManager()
