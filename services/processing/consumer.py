"""
Processing Consumer Pipeline.
Consumes RawPost items, applies deduplication (Bloom + exact + SimHash),
filters spam heuristics to dead.letter, extracts NLP tokens/entities,
emits CleanPost to clean.posts topic, and writes batches to the historical store.
"""

import logging

from services.ingestion.models import RawPost
from services.ingestion.streaming import stream_manager
from services.processing.dedup import Deduplicator
from services.processing.models import CleanPost
from services.processing.nlp import NLPPipeline
from services.processing.settings import settings
from services.processing.spam import SpamFilter
from services.processing.store import PostStore, post_store

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """End-to-end normalization and quality pipeline."""

    def __init__(self, store: PostStore | None = None, spam_threshold: float = 0.70):
        self.store = store or post_store
        self.deduplicator = Deduplicator()
        self.spam_filter = SpamFilter(threshold=spam_threshold)
        self.nlp = NLPPipeline()

        # Batch accumulator for high-throughput database writes
        self._batch_buffer: list[CleanPost] = []
        self._batch_size = 500

    def process_raw_post(self, raw: RawPost) -> CleanPost | None:
        """
        Processes a single RawPost.
        Returns CleanPost if valid, or None if dropped as duplicate or dead.letter spam.
        """
        # 1. Exact Duplicate Check
        if self.deduplicator.is_exact_duplicate(raw.platform, raw.post_id):
            logger.debug("Dropped exact duplicate post: %s:%s", raw.platform, raw.post_id)
            return None

        # Record exact ID seen
        self.deduplicator.record_exact(raw.platform, raw.post_id)

        # 2. Spam Evaluation
        is_spam, spam_score, reason = self.spam_filter.is_spam(raw.text)
        if is_spam:
            # Route to dead.letter topic
            dead_letter_payload = {
                "platform": raw.platform,
                "post_id": raw.post_id,
                "text": raw.text,
                "spam_score": spam_score,
                "drop_reason": reason,
                "dropped_at": raw.fetched_at.isoformat()
            }
            stream_manager.publish(
                topic=settings.dead_letter_topic,
                key=f"{raw.platform}:{raw.post_id}",
                value=dead_letter_payload
            )
            logger.debug("Routed spam post %s to dead.letter (%s)", raw.post_id, reason)
            return None

        # 3. Near-Duplicate Check (SimHash)
        is_near_dup, simhash_hex = self.deduplicator.check_and_record_near_duplicate(raw.text, raw.post_id)

        # 4. NLP Extraction (Tokens, Entities, Language)
        nlp_data = self.nlp.process(raw.text, lang_hint=raw.lang_hint)

        # 5. Construct Canonical CleanPost
        clean = CleanPost(
            id=f"{raw.platform}_{raw.post_id}",
            platform=raw.platform,
            post_id=raw.post_id,
            author_id_hash=raw.author_id_hash,
            author_handle_hash=raw.author_handle_hash,
            text=raw.text,
            lang=nlp_data["lang"],
            tokens=nlp_data["tokens"],
            entities=nlp_data["entities"],
            spam_score=spam_score,
            text_hash=simhash_hex,
            is_duplicate=is_near_dup,
            url=raw.url,
            engagement=raw.engagement,
            parent_id=raw.parent_id,
            raw_payload=raw.raw_payload,
            created_at=raw.created_at,
            fetched_at=raw.fetched_at
        )

        # 6. Publish to clean.posts topic
        stream_manager.publish(
            topic=settings.clean_posts_topic,
            key=f"{clean.platform}:{clean.post_id}",
            value=clean.model_dump(mode="json")
        )

        # 7. Add to batch write buffer
        self._batch_buffer.append(clean)
        if len(self._batch_buffer) >= self._batch_size:
            self.flush()

        return clean

    def flush(self) -> int:
        """Flushes the buffered clean posts to the database."""
        if not self._batch_buffer:
            return 0
        count = self.store.save_posts_batch(self._batch_buffer)
        self._batch_buffer.clear()
        return count


# Global default pipeline singleton
pipeline = ProcessingPipeline()
