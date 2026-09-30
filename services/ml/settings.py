"""ML Serving & Feature Pipeline Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class MLSettings(BaseSettings):
    app_env: str = "development"
    port: int = 8001
    redis_url: str = "redis://localhost:6379/0"
    model_dir: str = "services/ml/models"
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    drift_psi_threshold: float = 0.15

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = MLSettings()
