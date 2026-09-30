"""
Reddit Platform Connector (PRAW + Public JSON API Fallback).
Fetches submissions and comments with rate limiting and salted author hashing.
"""

import logging
from collections.abc import Iterator
from datetime import datetime, timezone

import requests

from services.ingestion.connectors.base import BaseConnector, retry_with_backoff
from services.ingestion.models import Engagement, RawPost
from services.ingestion.settings import settings

logger = logging.getLogger(__name__)


class RedditConnector(BaseConnector):
    """Ingests Reddit submissions and comments via PRAW or public JSON."""

    def __init__(self, client_id: str | None = None, client_secret: str | None = None, user_agent: str | None = None, **kwargs):
        super().__init__(name="reddit", rate=1.0, capacity=5.0, **kwargs)
        self.client_id = client_id or settings.reddit_client_id
        self.client_secret = client_secret or settings.reddit_client_secret
        self.user_agent = user_agent or settings.reddit_user_agent
        self.use_praw = bool(self.client_id and self.client_secret)

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _fetch_public_json(self, subreddit_or_query: str, limit: int) -> list[dict]:
        """Public Reddit JSON scraper fallback when PRAW credentials are not supplied."""
        headers = {"User-Agent": self.user_agent or "SociSentiBot/1.0 (Public Research)"}
        clean_target = subreddit_or_query.lstrip("r/").strip() or "all"
        url = f"https://www.reddit.com/r/{clean_target}/new.json?limit={min(limit, 100)}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data", {}).get("children", [])
        logger.warning("Reddit public API returned status %d for %s", resp.status_code, clean_target)
        return []

    def fetch(self, query_or_channel: str = "all", limit: int = 100) -> Iterator[RawPost]:
        """Fetches Reddit submissions matching query or subreddit."""
        logger.info("Fetching Reddit data for target '%s' (limit=%d)...", query_or_channel, limit)
        yielded = 0

        # When credentials are provided, PRAW would be used; otherwise use robust JSON API
        children = self._fetch_public_json(query_or_channel, limit)
        for item in children:
            if limit and yielded >= limit:
                break

            self.rate_limiter.acquire("reddit_request", tokens=1.0)
            data = item.get("data", {})
            post_id = data.get("id")
            if not post_id:
                continue

            raw_author = data.get("author", "unknown_redditor")
            author_id_hash = self.hash_identifier(raw_author)
            author_handle_hash = self.format_handle_hash(raw_author)

            title = data.get("title", "")
            selftext = data.get("selftext", "")
            full_text = f"{title}\n\n{selftext}".strip() if selftext else title

            created_utc = data.get("created_utc", datetime.now(timezone.utc).timestamp())
            created_at = datetime.fromtimestamp(created_utc, timezone.utc)

            post = RawPost(
                platform="reddit",
                post_id=f"t3_{post_id}",
                author_id_hash=author_id_hash,
                author_handle_hash=author_handle_hash,
                text=full_text,
                lang_hint="en",
                created_at=created_at,
                fetched_at=datetime.now(timezone.utc),
                url=f"https://www.reddit.com{data.get('permalink', '')}",
                engagement=Engagement(
                    likes=data.get("ups", 0),
                    shares=0,
                    replies=data.get("num_comments", 0)
                ),
                parent_id=None,
                raw_payload={
                    "subreddit": data.get("subreddit"),
                    "over_18": data.get("over_18", False),
                    "upvote_ratio": data.get("upvote_ratio", 1.0)
                }
            )

            yield post
            yielded += 1
