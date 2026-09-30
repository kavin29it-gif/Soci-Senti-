"""Fusion, Risk Scoring, & Evidence Integrity Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class FusionSettings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_service_role_key: str = ""
    kafka_bootstrap_servers: str = "localhost:9092"
    analysis_results_topic: str = "analysis.results"

    # Risk scoring bands
    low_band_max: float = 39.0
    medium_band_max: float = 69.0
    # High band is 70.0 - 100.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = FusionSettings()
