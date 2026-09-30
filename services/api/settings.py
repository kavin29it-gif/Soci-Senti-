"""API Gateway & Case Management Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    app_env: str = "development"
    port: int = 8000
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    jwt_secret: str = "super_secret_jwt_signing_key_for_development"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = APISettings()
