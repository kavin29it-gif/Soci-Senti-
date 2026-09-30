"""
Binary Merkle Tree & Inclusion Proof Engine.
Constructs verifiable Merkle trees over evidence fingerprints,
generates compact audit inclusion proofs, and verifies proof paths.
Includes AnchorService v2 stub for public blockchain anchoring.
"""

import hashlib
import logging

logger = logging.getLogger(__name__)


def hash_pair(left: str, right: str) -> str:
    """Computes SHA-256 over concatenated binary hashes."""
    combined = f"{left}:{right}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


class MerkleTree:
    """Binary Merkle tree implementation with inclusion proof generation."""

    def __init__(self, leaf_hashes: list[str]):
        if not leaf_hashes:
            raise ValueError("Merkle tree must contain at least one leaf hash.")
        self.leaf_hashes = leaf_hashes
        self.levels: list[list[str]] = []
        self._build_tree()

    def _build_tree(self):
        current_level = list(self.leaf_hashes)
        self.levels.append(current_level)

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # If odd number of leaves, duplicate the last element
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                parent = hash_pair(left, right)
                next_level.append(parent)
            current_level = next_level
            self.levels.append(current_level)

    @property
    def root(self) -> str:
        """Returns the Merkle root hash."""
        return self.levels[-1][0]

    def get_inclusion_proof(self, leaf_index: int) -> list[dict]:
        """
        Generates an inclusion proof path for the leaf at the specified index.
        Returns a list of sibling nodes: [{"position": "left"|"right", "hash": "..."}]
        """
        if leaf_index < 0 or leaf_index >= len(self.leaf_hashes):
            raise IndexError("Leaf index out of bounds.")

        proof = []
        idx = leaf_index

        for level in self.levels[:-1]:
            is_right_child = (idx % 2 == 1)
            sibling_idx = idx - 1 if is_right_child else idx + 1

            if sibling_idx < len(level):
                sibling_hash = level[sibling_idx]
            else:
                sibling_hash = level[idx]

            proof.append({
                "position": "left" if is_right_child else "right",
                "hash": sibling_hash
            })
            idx //= 2

        return proof

    @staticmethod
    def verify_proof(leaf_hash: str, proof: list[dict], expected_root: str) -> bool:
        """
        Verifies that leaf_hash belongs to the tree with expected_root given the proof path.
        """
        current_hash = leaf_hash
        for step in proof:
            sibling_hash = step["hash"]
            if step["position"] == "left":
                current_hash = hash_pair(sibling_hash, current_hash)
            else:
                current_hash = hash_pair(current_hash, sibling_hash)

        return current_hash == expected_root


class AnchorService:
    """
    Decentralized Public Ledger Anchoring Service.
    # TODO(v2): Transmits Merkle root hashes to public blockchain networks (Ethereum / Polygon / Bitcoin OP_RETURN).
    """

    def anchor_merkle_root(self, root_hash: str, case_id: str) -> str:
        """Anchors Merkle root hash to external blockchain network."""
        raise NotImplementedError(
            "# TODO(v2): Blockchain anchoring is out of scope for MVP (~60% scope). "
            "Please use local Merkle root and hash-chain verification for MVP compliance."
        )


anchor_service = AnchorService()
