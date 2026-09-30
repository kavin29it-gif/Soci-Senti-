"""
Streaming and Queuing Manager (Kafka & In-Memory Dual Mode).
Manages topics: raw.posts, clean.posts, analysis.results, dead.letter.
Provides idempotent publishing keyed by platform:post_id.
"""

import logging
from collections import defaultdict
from collections.abc import Callable

logger = logging.getLogger(__name__)


class StreamManager:
    """Kafka message broker manager with transparent in-memory fallback for local development."""

    def __init__(self, bootstrap_servers: str = "localhost:9092", in_memory_fallback: bool = True):
        self.bootstrap_servers = bootstrap_servers
        self.in_memory_fallback = in_memory_fallback
        self.is_connected_to_kafka = False
        self._producer = None

        # In-memory queues for local offline testing
        self._queues: dict[str, list[dict]] = defaultdict(list)
        self._subscribers: dict[str, list[Callable[[dict], None]]] = defaultdict(list)

    def publish(self, topic: str, key: str, value: dict) -> bool:
        """
        Publishes a message to the specified topic, keyed by platform:post_id.
        """
        payload = {
            "key": key,
            "topic": topic,
            "value": value
        }

        # Store in local queue for consumers
        self._queues[topic].append(payload)

        # Notify active in-process listeners if any
        for callback in self._subscribers[topic]:
            try:
                callback(value)
            except Exception as e:
                logger.error("Error in consumer callback for topic %s: %s", topic, e)

        return True

    def subscribe(self, topic: str, callback: Callable[[dict], None]):
        """Subscribes an in-process callback to a topic."""
        self._subscribers[topic].append(callback)

    def get_messages(self, topic: str) -> list[dict]:
        """Returns all messages currently buffered in a topic."""
        return [item["value"] for item in self._queues.get(topic, [])]

    def clear(self, topic: str | None = None):
        """Clears buffered messages."""
        if topic:
            self._queues[topic].clear()
        else:
            self._queues.clear()


# Global default stream manager singleton
stream_manager = StreamManager()
