"""
Telegram Platform Connector (Telethon & Public Web Preview Scraper).
Fetches messages from public broadcast channels with rate limiting and salted author hashing.
"""

import logging
import re
from collections.abc import Iterator
from datetime import datetime, timezone

import requests

from services.ingestion.connectors.base import BaseConnector, retry_with_backoff
from services.ingestion.models import Engagement, RawPost
from services.ingestion.settings import settings

logger = logging.getLogger(__name__)


class TelegramConnector(BaseConnector):
    """Ingests public Telegram channel messages."""

    def __init__(self, api_id: str | None = None, api_hash: str | None = None, **kwargs):
        super().__init__(name="telegram", rate=2.0, capacity=8.0, **kwargs)
        self.api_id = api_id or settings.telegram_api_id
        self.api_hash = api_hash or settings.telegram_api_hash

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _fetch_web_preview(self, channel: str) -> list[dict]:
        """Fetches public message preview HTML from t.me/s/{channel} without requiring credentials."""
        clean_channel = channel.lstrip("@").strip()
        url = f"https://t.me/s/{clean_channel}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SociSentiResearch/1.0"}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.warning("Telegram channel preview %s returned %d", clean_channel, resp.status_code)
                return []

            # Simple, fast regex extraction from Telegram's clean public preview DOM
            messages = []
            html = resp.text
            # Extract message blocks
            raw_blocks = re.findall(r'<div class="tgme_widget_message_wrap[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL)

            for block in raw_blocks:
                # Extract message id
                id_match = re.search(r'data-post="([^"]+)"', block)
                if not id_match:
                    continue
                data_post = id_match.group(1) # e.g. "durov/250"

                # Extract text
                text_match = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', block, re.DOTALL)
                raw_text = text_match.group(1) if text_match else ""
                # Strip HTML tags
                clean_text = re.sub(r'<[^>]+>', '', raw_text).strip()
                if not clean_text:
                    continue

                # Extract date
                time_match = re.search(r'<time datetime="([^"]+)"', block)
                date_str = time_match.group(1) if time_match else None

                # Extract views
                views_match = re.search(r'<span class="tgme_widget_message_views">([^<]+)</span>', block)
                views_str = views_match.group(1) if views_match else "0"

                messages.append({
                    "post_id": data_post.replace("/", "_"),
                    "channel": clean_channel,
                    "text": clean_text,
                    "date": date_str,
                    "views": views_str
                })
            return messages
        except Exception as e:
            logger.warning("Error fetching Telegram preview for %s: %s", clean_channel, e)
            return []

    def fetch(self, query_or_channel: str, limit: int = 100) -> Iterator[RawPost]:
        """Fetches posts from the specified Telegram channel."""
        logger.info("Fetching Telegram public posts from '%s' (limit=%d)...", query_or_channel, limit)
        yielded = 0

        items = self._fetch_web_preview(query_or_channel)
        for item in items:
            if limit and yielded >= limit:
                break

            self.rate_limiter.acquire("telegram_request", tokens=1.0)
            author_id_hash = self.hash_identifier(item["channel"])
            author_handle_hash = self.format_handle_hash(item["channel"])

            created_at_raw = item.get("date")
            if created_at_raw:
                try:
                    created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
                except ValueError:
                    created_at = datetime.now(timezone.utc)
            else:
                created_at = datetime.now(timezone.utc)

            post = RawPost(
                platform="telegram",
                post_id=f"tg_{item['post_id']}",
                author_id_hash=author_id_hash,
                author_handle_hash=author_handle_hash,
                text=item["text"],
                lang_hint="en",
                created_at=created_at,
                fetched_at=datetime.now(timezone.utc),
                url=f"https://t.me/{item['channel']}/{item['post_id'].split('_')[-1]}",
                engagement=Engagement(likes=0, shares=0, replies=0),
                parent_id=None,
                raw_payload={"channel": item["channel"], "views": item["views"]}
            )

            yield post
            yielded += 1
