"""
Base Abstract Social Media Connector.
Enforces canonical RawPost generation, salted SHA-256 author hashing,
token-bucket rate limiting, and exponential backoff.
"""

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator

from services.ingestion.models import RawPost
from services.ingestion.rate_limiter import TokenBucketRateLimiter
from services.ingestion.settings import settings

logger = logging.getLogger(__name__)


def retry_with_backoff(max_retries: int = 3, initial_delay: float = 0.5, backoff_factor: float = 2.0):
    """Decorator for exponential backoff retries on network/API errors."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_err = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    logger.warning(
                        "Attempt %d/%d failed for %s: %s. Retrying in %.2fs...",
                        attempt + 1, max_retries, func.__name__, e, delay
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
            raise last_err
        return wrapper
    return decorator


class BaseConnector(ABC):
    """Abstract base class for all social intelligence data connectors."""

    def __init__(
        self,
        name: str,
        rate: float = 5.0,
        capacity: float = 15.0,
        salt: str | None = None,
        store_raw_handles: bool | None = None
    ):
        self.name = name
        self.salt = salt or settings.author_hash_salt
        self.store_raw_handles = store_raw_handles if store_raw_handles is not None else settings.store_raw_handles
        self.rate_limiter = TokenBucketRateLimiter(rate=rate, capacity=capacity, key_prefix=f"ratelimit:{name}")

    def hash_identifier(self, identifier: str) -> str:
        """Computes a non-reversible salted SHA-256 hash for privacy preservation."""
        if not identifier:
            identifier = "anonymous"
        salted = f"{self.salt}:{identifier}".encode()
        return hashlib.sha256(salted).hexdigest()

    def format_handle_hash(self, handle: str | None) -> str | None:
        if not handle:
            return None
        return self.hash_identifier(handle.lstrip("@"))

    @abstractmethod
    def fetch(self, query_or_channel: str, limit: int = 100) -> Iterator[RawPost]:
        """
        Fetches public items matching the query or channel.
        Yields canonical RawPost objects.
        """
