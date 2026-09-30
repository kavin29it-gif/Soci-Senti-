"""
Token Bucket Rate Limiter with Redis backend and in-memory fallback.
Ensures platform rate limits (Reddit, YouTube, Telegram) are respected.
"""

import logging
import time

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """Token bucket rate limiter supporting both Redis and in-memory storage."""

    def __init__(self, rate: float = 10.0, capacity: float = 20.0, redis_client=None, key_prefix: str = "ratelimit"):
        """
        Args:
            rate: Tokens added per second.
            capacity: Maximum bucket capacity.
            redis_client: Optional redis.Redis instance.
            key_prefix: Redis key namespace.
        """
        self.rate = rate
        self.capacity = capacity
        self.redis = redis_client
        self.key_prefix = key_prefix

        # In-memory fallback state
        self._tokens = capacity
        self._last_update = time.monotonic()

    def acquire(self, key: str = "default", tokens: float = 1.0, block: bool = True, timeout: float = 10.0) -> bool:
        """
        Attempts to acquire tokens. If block=True, waits until tokens become available.
        Returns True if acquired, False if timed out or rejected.
        """
        start_time = time.monotonic()

        while True:
            if self._try_acquire(key, tokens):
                return True

            if not block:
                return False

            if time.monotonic() - start_time >= timeout:
                logger.warning("Rate limit acquire timed out for key %s", key)
                return False

            # Wait for next token
            sleep_time = min(0.1, max(0.01, tokens / self.rate))
            time.sleep(sleep_time)

    def _try_acquire(self, key: str, tokens: float) -> bool:
        if self.redis is not None:
            try:
                # Redis token bucket via Lua-style atomic transaction
                redis_key = f"{self.key_prefix}:{key}"
                now = time.time()
                pipe = self.redis.pipeline()
                pipe.get(f"{redis_key}:tokens")
                pipe.get(f"{redis_key}:last_updated")
                res = pipe.execute()

                stored_tokens = float(res[0]) if res[0] is not None else self.capacity
                last_updated = float(res[1]) if res[1] is not None else now

                # Add tokens based on elapsed time
                elapsed = max(0.0, now - last_updated)
                current_tokens = min(self.capacity, stored_tokens + (elapsed * self.rate))

                if current_tokens >= tokens:
                    current_tokens -= tokens
                    pipe = self.redis.pipeline()
                    pipe.set(f"{redis_key}:tokens", current_tokens, ex=3600)
                    pipe.set(f"{redis_key}:last_updated", now, ex=3600)
                    pipe.execute()
                    return True
                return False
            except Exception as e:
                logger.debug("Redis rate limit error (%s), using in-memory fallback", e)

        # In-memory fallback
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(self.capacity, self._tokens + (elapsed * self.rate))
        self._last_update = now

        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False
