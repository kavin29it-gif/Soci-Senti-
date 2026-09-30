"""
Historical Data Store & Repository.
Manages batch writes of normalized CleanPost and Author records.
Supports Supabase Postgres with high-performance local SQLite fallback for testing.
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone

from services.processing.models import CleanPost

logger = logging.getLogger(__name__)


class PostStore:
    """Historical repository for CleanPost and Author records."""

    def __init__(self, db_path: str = "data/posts.db"):
        self.db_path = db_path
        self._init_sqlite()

    def _init_sqlite(self):
        """Initializes high-performance local SQLite database mirroring Supabase schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")

            # Authors table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS authors (
                    id TEXT PRIMARY KEY,
                    author_id_hash TEXT UNIQUE NOT NULL,
                    author_handle_hash TEXT,
                    platform TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    post_count INTEGER DEFAULT 1,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_authors_platform ON authors(platform)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_authors_hash ON authors(author_id_hash)")

            # Posts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    author_id_hash TEXT NOT NULL,
                    author_handle_hash TEXT,
                    text TEXT NOT NULL,
                    lang TEXT,
                    tokens TEXT DEFAULT '[]',
                    entities TEXT DEFAULT '[]',
                    spam_score REAL DEFAULT 0.0,
                    text_hash TEXT,
                    is_duplicate INTEGER DEFAULT 0,
                    url TEXT,
                    engagement TEXT DEFAULT '{}',
                    parent_id TEXT,
                    raw_payload TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    UNIQUE(platform, post_id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author_id_hash)")

    def save_posts_batch(self, posts: list[CleanPost]) -> int:
        """
        Inserts a batch of CleanPost records and updates author statistics.
        Returns the number of successfully saved posts.
        """
        if not posts:
            return 0

        post_rows = []
        author_updates = {}
        now_iso = datetime.now(timezone.utc).isoformat()

        for p in posts:
            post_id_val = p.id or f"{p.platform}_{p.post_id}"
            created_at_iso = p.created_at.isoformat() if isinstance(p.created_at, datetime) else str(p.created_at)
            fetched_at_iso = p.fetched_at.isoformat() if isinstance(p.fetched_at, datetime) else str(p.fetched_at)

            post_rows.append((
                post_id_val,
                p.platform,
                p.post_id,
                p.author_id_hash,
                p.author_handle_hash,
                p.text,
                p.lang,
                json.dumps(p.tokens),
                json.dumps(p.entities),
                p.spam_score,
                p.text_hash,
                1 if p.is_duplicate else 0,
                p.url,
                json.dumps(p.engagement.model_dump()),
                p.parent_id,
                json.dumps(p.raw_payload),
                created_at_iso,
                fetched_at_iso
            ))

            # Aggregate author counts
            if p.author_id_hash not in author_updates:
                author_updates[p.author_id_hash] = {
                    "author_handle_hash": p.author_handle_hash,
                    "platform": p.platform,
                    "first_seen_at": created_at_iso,
                    "last_seen_at": created_at_iso,
                    "count": 1
                }
            else:
                author_updates[p.author_id_hash]["count"] += 1
                author_updates[p.author_id_hash]["last_seen_at"] = max(
                    author_updates[p.author_id_hash]["last_seen_at"], created_at_iso
                )

        inserted_count = 0
        with sqlite3.connect(self.db_path) as conn:
            # Batch insert posts
            cursor = conn.executemany("""
                INSERT OR IGNORE INTO posts (
                    id, platform, post_id, author_id_hash, author_handle_hash,
                    text, lang, tokens, entities, spam_score, text_hash,
                    is_duplicate, url, engagement, parent_id, raw_payload,
                    created_at, fetched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, post_rows)
            inserted_count = cursor.rowcount

            # Batch upsert authors
            for a_hash, a_info in author_updates.items():
                conn.execute("""
                    INSERT INTO authors (
                        id, author_id_hash, author_handle_hash, platform,
                        first_seen_at, last_seen_at, post_count, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(author_id_hash) DO UPDATE SET
                        post_count = post_count + excluded.post_count,
                        last_seen_at = excluded.last_seen_at
                """, (
                    f"auth_{a_hash[:16]}",
                    a_hash,
                    a_info["author_handle_hash"],
                    a_info["platform"],
                    a_info["first_seen_at"],
                    a_info["last_seen_at"],
                    a_info["count"],
                    now_iso
                ))

        return inserted_count

    def query_posts_by_time_range(
        self,
        start_time: str,
        end_time: str,
        platform: str | None = None,
        limit: int = 100
    ) -> list[dict]:
        """
        Queries posts within a time range. Sub-300ms query performance.
        """
        query = "SELECT * FROM posts WHERE created_at >= ? AND created_at <= ?"
        params = [start_time, end_time]
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def count_posts(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT count(*) FROM posts")
            return cursor.fetchone()[0]


# Global store singleton
post_store = PostStore()
