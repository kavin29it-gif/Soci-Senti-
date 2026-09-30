"""
Deduplication Engine.
Combines a Bloom filter (Redis/in-memory), exact (platform, post_id) verification,
and 64-bit weighted SimHash for near-duplicate text detection.
"""

import hashlib
import logging
import re

logger = logging.getLogger(__name__)


class SimHash:
    """64-bit weighted SimHash implementation with word unigrams and bigrams."""

    @staticmethod
    def _hash_feature(feature: str) -> int:
        return int(hashlib.md5(feature.encode("utf-8")).hexdigest()[:16], 16)

    @classmethod
    def compute(cls, text: str) -> int:
        """Computes a 64-bit SimHash integer fingerprint for given text."""
        tokens = re.findall(r"\w+", text.lower())
        if not tokens:
            return 0

        # Unigrams + bigrams for robust phrase matching
        features = list(tokens)
        for i in range(len(tokens) - 1):
            features.append(f"{tokens[i]}_{tokens[i+1]}")

        v = [0] * 64
        for feat in features:
            h = cls._hash_feature(feat)
            weight = max(1, len(feat))
            for i in range(64):
                bit = (h >> i) & 1
                v[i] += weight if bit else -weight

        fingerprint = 0
        for i in range(64):
            if v[i] > 0:
                fingerprint |= (1 << i)
        return fingerprint

    @staticmethod
    def hamming_distance(hash1: int, hash2: int) -> int:
        """Calculates the number of differing bits between two 64-bit hashes."""
        x = (hash1 ^ hash2) & 0xFFFFFFFFFFFFFFFF
        return bin(x).count("1")


class BloomFilter:
    """Fast Bloom filter with Redis backing and in-memory bitset fallback."""

    def __init__(self, capacity: int = 100000, error_rate: float = 0.01, redis_client=None, key: str = "bloom:posts"):
        self.capacity = capacity
        self.error_rate = error_rate
        self.redis = redis_client
        self.key = key

        self.size = 1000000 # 1 million bits (~125 KB)
        self.hash_count = 5
        self._in_memory_bits = bytearray(self.size // 8)

    def _get_offsets(self, item: str) -> list[int]:
        offsets = []
        raw_bytes = item.encode("utf-8")
        h1 = int(hashlib.sha256(raw_bytes).hexdigest()[:16], 16)
        h2 = int(hashlib.md5(raw_bytes).hexdigest()[:16], 16)
        for i in range(self.hash_count):
            combined = (h1 + i * h2) % self.size
            offsets.append(combined)
        return offsets

    def add(self, item: str):
        offsets = self._get_offsets(item)
        if self.redis is not None:
            try:
                pipe = self.redis.pipeline()
                for offset in offsets:
                    pipe.setbit(self.key, offset, 1)
                pipe.execute()
                return
            except Exception as e:
                logger.debug("Redis bloom error (%s), using local fallback", e)

        for offset in offsets:
            byte_idx = offset // 8
            bit_idx = offset % 8
            self._in_memory_bits[byte_idx] |= (1 << bit_idx)

    def contains(self, item: str) -> bool:
        offsets = self._get_offsets(item)
        if self.redis is not None:
            try:
                pipe = self.redis.pipeline()
                for offset in offsets:
                    pipe.getbit(self.key, offset)
                bits = pipe.execute()
                return all(b == 1 for b in bits)
            except Exception as e:
                logger.debug("Redis bloom error (%s), using local fallback", e)

        for offset in offsets:
            byte_idx = offset // 8
            bit_idx = offset % 8
            if not (self._in_memory_bits[byte_idx] & (1 << bit_idx)):
                return False
        return True


class Deduplicator:
    """Unified deduplication engine coordinating Bloom filter, exact ID, and near-duplicate SimHash."""

    def __init__(self, redis_client=None, simhash_distance_threshold: int = 10):
        self.bloom = BloomFilter(redis_client=redis_client)
        self.exact_seen: set[str] = set()
        self.simhash_seen: list[tuple[int, str]] = [] # list of (simhash, post_id)
        self.threshold = simhash_distance_threshold

    def is_exact_duplicate(self, platform: str, post_id: str) -> bool:
        """Checks if (platform, post_id) has already been seen."""
        key = f"{platform}:{post_id}"
        if not self.bloom.contains(key):
            return False
        return key in self.exact_seen

    def record_exact(self, platform: str, post_id: str):
        key = f"{platform}:{post_id}"
        self.bloom.add(key)
        self.exact_seen.add(key)

    def check_and_record_near_duplicate(self, text: str, post_id: str) -> tuple[bool, str]:
        """
        Computes SimHash and checks if near-duplicate exists.
        Returns: (is_near_duplicate, simhash_hex)
        """
        fingerprint = SimHash.compute(text)
        simhash_hex = f"{fingerprint:016x}"

        # Check against existing recent fingerprints
        for stored_hash, orig_id in self.simhash_seen[-2000:]:
            if SimHash.hamming_distance(fingerprint, stored_hash) <= self.threshold:
                return True, simhash_hex

        self.simhash_seen.append((fingerprint, post_id))
        return False, simhash_hex
