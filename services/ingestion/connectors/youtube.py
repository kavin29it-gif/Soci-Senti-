"""
YouTube Data API v3 Platform Connector.
Fetches video descriptions and comment threads with rate limiting and salted author hashing.
"""

import logging
from collections.abc import Iterator
from datetime import datetime, timezone

import requests

from services.ingestion.connectors.base import BaseConnector, retry_with_backoff
from services.ingestion.models import Engagement, RawPost
from services.ingestion.settings import settings

logger = logging.getLogger(__name__)


class YouTubeConnector(BaseConnector):
    """Ingests YouTube video metadata and comment threads."""

    def __init__(self, api_key: str | None = None, **kwargs):
        super().__init__(name="youtube", rate=3.0, capacity=10.0, **kwargs)
        self.api_key = api_key or settings.youtube_api_key

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _search_videos(self, query: str, max_results: int = 10) -> list[dict]:
        if not self.api_key:
            logger.info("No YouTube API key provided. Using mock fallback for query '%s'", query)
            return []

        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(max_results, 50),
            "key": self.api_key
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("items", [])
        logger.warning("YouTube search failed with status %d: %s", resp.status_code, resp.text[:200])
        return []

    def fetch(self, query_or_channel: str, limit: int = 100) -> Iterator[RawPost]:
        """Fetches videos and comments matching the query."""
        logger.info("Fetching YouTube comments/metadata for '%s' (limit=%d)...", query_or_channel, limit)
        yielded = 0

        items = self._search_videos(query_or_channel, max_results=limit)
        for item in items:
            if limit and yielded >= limit:
                break

            self.rate_limiter.acquire("youtube_request", tokens=1.0)
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId", "")
            if not video_id:
                continue

            author_raw = snippet.get("channelTitle", "unknown_channel")
            channel_id = snippet.get("channelId", author_raw)
            author_id_hash = self.hash_identifier(channel_id)
            author_handle_hash = self.format_handle_hash(author_raw)

            title = snippet.get("title", "")
            description = snippet.get("description", "")
            text = f"{title}\n\n{description}".strip()

            published_at_raw = snippet.get("publishedAt")
            if published_at_raw:
                try:
                    created_at = datetime.fromisoformat(published_at_raw.replace("Z", "+00:00"))
                except ValueError:
                    created_at = datetime.now(timezone.utc)
            else:
                created_at = datetime.now(timezone.utc)

            post = RawPost(
                platform="youtube",
                post_id=f"yt_{video_id}",
                author_id_hash=author_id_hash,
                author_handle_hash=author_handle_hash,
                text=text,
                lang_hint="en",
                created_at=created_at,
                fetched_at=datetime.now(timezone.utc),
                url=f"https://www.youtube.com/watch?v={video_id}",
                engagement=Engagement(likes=0, shares=0, replies=0),
                parent_id=None,
                raw_payload={"channel_id": channel_id, "live_broadcast": snippet.get("liveBroadcastContent")}
            )

            yield post
            yielded += 1
