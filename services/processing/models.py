"""
Canonical Normalized Clean Post Data Model (Pydantic v2).
Adds NLP cleaning, entity annotations, spam score, and dedup text hashes.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from services.ingestion.models import Engagement


class CleanPost(BaseModel):
    id: str | None = Field(default=None, description="UUID primary key if assigned")
    platform: str
    post_id: str
    author_id_hash: str
    author_handle_hash: str | None = None
    text: str
    lang: str = Field(default="en", description="Detected language code (ISO 639-1)")
    tokens: list[str] = Field(default_factory=list, description="Lemmatized or cleaned tokens")
    entities: list[dict[str, str]] = Field(default_factory=list, description="Extracted named entities [{'text': '...', 'label': '...'}]")
    spam_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Heuristic spam probability score")
    text_hash: str = Field(..., description="MinHash / SimHash or normalized SHA-256 for dedup")
    is_duplicate: bool = Field(default=False, description="Whether near-duplicate was detected")
    url: str | None = None
    engagement: Engagement = Field(default_factory=Engagement)
    parent_id: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
