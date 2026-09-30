"""Ingestion Service Settings (pydantic-settings)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestionSettings(BaseSettings):
    app_env: str = "development"
    author_hash_salt: str = "socisenti_super_secret_salt_2026_change_in_production"
    store_raw_handles: bool = False
    kafka_bootstrap_servers: str = "localhost:9092"
    raw_posts_topic: str = "raw.posts"
    redis_url: str = "redis://localhost:6379/0"
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "SociSentiBot/1.0"
    youtube_api_key: str = ""
    telegram_api_id: str = ""
    telegram_api_hash: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = IngestionSettings()
