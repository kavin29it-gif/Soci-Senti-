"""
Social Intelligence Ingestion CLI.
Usage:
    python -m services.ingestion.run --platform mock --limit 500
    python -m services.ingestion.run --platform reddit --query "cybersecurity" --limit 100
    python -m services.ingestion.run --platform youtube --query "finance fraud" --limit 50
    python -m services.ingestion.run --platform telegram --query "durov" --limit 50
"""

import argparse
import logging
import sys
import time

from services.ingestion.connectors.mock import MockConnector
from services.ingestion.connectors.reddit import RedditConnector
from services.ingestion.connectors.stubs import InstagramConnector, XConnector
from services.ingestion.connectors.telegram import TelegramConnector
from services.ingestion.connectors.youtube import YouTubeConnector
from services.ingestion.settings import settings
from services.ingestion.streaming import stream_manager
from services.processing.consumer import pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ingestion.cli")


def get_connector(platform: str, sample_dir: str = "data/sample"):
    plat = platform.lower().strip()
    if plat == "mock":
        return MockConnector(sample_dir=sample_dir)
    elif plat == "reddit":
        return RedditConnector()
    elif plat == "youtube":
        return YouTubeConnector()
    elif plat == "telegram":
        return TelegramConnector()
    elif plat == "x":
        return XConnector()
    elif plat == "instagram":
        return InstagramConnector()
    else:
        raise ValueError(f"Unknown platform '{platform}'. Choose from: mock, reddit, youtube, telegram, x, instagram.")


def run_ingestion(platform: str, query: str = "", limit: int = 100, sample_dir: str = "data/sample") -> dict:
    connector = get_connector(platform, sample_dir=sample_dir)
    logger.info("Starting ingestion on platform '%s' (limit=%d, query='%s')...", platform, limit, query)

    start_time = time.time()
    fetched_count = 0
    clean_count = 0
    duplicate_count = 0
    spam_count = 0

    try:
        for raw_post in connector.fetch(query_or_channel=query, limit=limit):
            fetched_count += 1

            # Publish raw post to raw.posts topic
            stream_manager.publish(
                topic=settings.raw_posts_topic,
                key=f"{raw_post.platform}:{raw_post.post_id}",
                value=raw_post.model_dump(mode="json")
            )

            # Process through normalization pipeline
            clean = pipeline.process_raw_post(raw_post)
            if clean is not None:
                clean_count += 1
                if clean.is_duplicate:
                    duplicate_count += 1
            else:
                # Dropped either as exact duplicate or dead-letter spam
                if pipeline.deduplicator.is_exact_duplicate(raw_post.platform, raw_post.post_id):
                    duplicate_count += 1
                else:
                    spam_count += 1

        # Flush remaining buffered clean posts
        pipeline.flush()

    except NotImplementedError as e:
        logger.error("Platform '%s' is not implemented: %s", platform, e)
        return {"error": str(e), "platform": platform}

    elapsed = max(0.001, time.time() - start_time)
    throughput = fetched_count / elapsed

    summary = {
        "platform": platform,
        "fetched": fetched_count,
        "clean_emitted": clean_count,
        "duplicates": duplicate_count,
        "spam_dropped": spam_count,
        "elapsed_seconds": round(elapsed, 2),
        "throughput_posts_per_sec": round(throughput, 1)
    }

    logger.info("=== Ingestion Run Completed ===")
    logger.info("Fetched: %d | Clean: %d | Duplicates: %d | Spam: %d", fetched_count, clean_count, duplicate_count, spam_count)
    logger.info("Time: %.2fs | Throughput: %.1f posts/sec", elapsed, throughput)
    return summary


def main():
    parser = argparse.ArgumentParser(description="SociSenti Ingestion Runner")
    parser.add_argument("--platform", type=str, default="mock", help="Source platform: mock, reddit, youtube, telegram, x, instagram")
    parser.add_argument("--query", type=str, default="", help="Query keyword, subreddit, or channel name")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of posts to fetch")
    parser.add_argument("--sample-dir", type=str, default="data/sample", help="Sample directory for mock connector")

    args = parser.parse_args()
    try:
        run_ingestion(args.platform, query=args.query, limit=args.limit, sample_dir=args.sample_dir)
    except Exception as e:
        logger.error("Ingestion failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
