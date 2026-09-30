"""
Mock / Sample Replay Connector.
Enables offline and automated demonstration without live third-party API credentials.
Reads pre-generated canonical sample files from data/sample/.
"""

import glob
import json
import logging
import os
from collections.abc import Iterator
from datetime import datetime, timezone

from services.ingestion.connectors.base import BaseConnector
from services.ingestion.models import Engagement, RawPost

logger = logging.getLogger(__name__)


class MockConnector(BaseConnector):
    """Replays pre-recorded sample social media posts for local tests and demos."""

    def __init__(self, sample_dir: str = "data/sample", replay_speed_factor: float = 0.0, **kwargs):
        rate = 10000.0 if replay_speed_factor == 0.0 else 100.0
        capacity = 20000.0 if replay_speed_factor == 0.0 else 200.0
        super().__init__(name="mock", rate=rate, capacity=capacity, **kwargs)
        self.sample_dir = sample_dir
        self.replay_speed_factor = replay_speed_factor

    def fetch(self, query_or_channel: str = "", limit: int = 100) -> Iterator[RawPost]:
        """
        Replays records from the sample dataset.
        If query_or_channel is provided, filters for posts containing that term.
        """
        json_pattern = os.path.join(self.sample_dir, "*.json")
        sample_files = glob.glob(json_pattern)
        if not sample_files:
            logger.error("No sample JSON files found in %s", self.sample_dir)
            return

        yielded_count = 0
        target_term = query_or_channel.lower().strip() if query_or_channel else ""

        for sample_file in sample_files:
            try:
                with open(sample_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception as e:
                logger.error("Failed to read %s: %s", sample_file, e)
                continue

            for raw_item in records:
                if limit and yielded_count >= limit:
                    return

                # Acquire token from rate limiter
                self.rate_limiter.acquire("replay", tokens=1.0)

                # Text filter if query provided
                text = raw_item.get("text", "")
                if target_term and target_term not in text.lower():
                    continue

                # Ensure canonical author hashing is verified
                author_id_hash = raw_item.get("author_id_hash")
                if not author_id_hash or len(author_id_hash) != 64:
                    author_id_hash = self.hash_identifier(raw_item.get("author", "unknown_user"))

                author_handle_hash = raw_item.get("author_handle_hash")
                if not author_handle_hash:
                    author_handle_hash = self.format_handle_hash(raw_item.get("handle"))

                # Engagement object
                eng_data = raw_item.get("engagement", {})
                engagement = Engagement(
                    likes=eng_data.get("likes", 0),
                    shares=eng_data.get("shares", 0),
                    replies=eng_data.get("replies", 0)
                )

                # Parse or default created_at
                created_at_raw = raw_item.get("created_at")
                if isinstance(created_at_raw, str):
                    try:
                        created_at = datetime.fromisoformat(created_at_raw)
                    except ValueError:
                        created_at = datetime.now(timezone.utc)
                else:
                    created_at = datetime.now(timezone.utc)

                post = RawPost(
                    platform=raw_item.get("platform", "mock"),
                    post_id=str(raw_item.get("post_id", f"mock_{yielded_count}")),
                    author_id_hash=author_id_hash,
                    author_handle_hash=author_handle_hash,
                    text=text,
                    lang_hint=raw_item.get("lang_hint", "en"),
                    created_at=created_at,
                    fetched_at=datetime.now(timezone.utc),
                    url=raw_item.get("url", f"https://mock.platform/post/{raw_item.get('post_id')}"),
                    engagement=engagement,
                    parent_id=raw_item.get("parent_id"),
                    raw_payload=raw_item.get("raw_payload", {})
                )

                yield post
                yielded_count += 1
