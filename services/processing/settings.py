"""Processing & Normalization Service Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class ProcessingSettings(BaseSettings):
    app_env: str = "development"
    kafka_bootstrap_servers: str = "localhost:9092"
    raw_posts_topic: str = "raw.posts"
    clean_posts_topic: str = "clean.posts"
    dead_letter_topic: str = "dead.letter"
    redis_url: str = "redis://localhost:6379/0"
    spam_threshold: float = 0.70
    simhash_distance_threshold: int = 3
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_service_role_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = ProcessingSettings()
