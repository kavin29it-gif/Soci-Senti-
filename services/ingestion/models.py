"""
Canonical Ingestion Data Models (Pydantic v2).
Ensures strict validation across Reddit, YouTube, Telegram, and Mock connectors.
All author identifiers are hashed with salted SHA-256 before ingestion.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Engagement(BaseModel):
    likes: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    replies: int = Field(default=0, ge=0)


class RawPost(BaseModel):
    platform: str = Field(..., description="Source social platform (reddit, youtube, telegram, mock)")
    post_id: str = Field(..., description="Unique platform-native post identifier")
    author_id_hash: str = Field(..., description="Salted SHA-256 of author account ID")
    author_handle_hash: str | None = Field(default=None, description="Salted SHA-256 of author handle")
    text: str = Field(..., description="Raw post text or comment body")
    lang_hint: str | None = Field(default=None, description="Heuristic language hint from platform metadata")
    created_at: datetime = Field(..., description="Timestamp when post was created on source platform")
    fetched_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when item was ingested")
    url: str | None = Field(default=None, description="Public canonical URL of the post")
    engagement: Engagement = Field(default_factory=Engagement)
    parent_id: str | None = Field(default=None, description="Parent post or comment ID for thread tracking")
    raw_payload: dict[str, Any] = Field(default_factory=dict, description="Original unparsed platform payload")

    @field_validator("author_id_hash")
    @classmethod
    def validate_sha256_length(cls, v: str) -> str:
        if len(v) != 64:
            raise ValueError("author_id_hash must be a valid 64-character SHA-256 hex string")
        return v
