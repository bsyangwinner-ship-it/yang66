from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Graduate Nutrition Agent API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/nutrition_agent"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536
    enable_rule_fallback: bool = True

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    s3_endpoint_url: str | None = None
    s3_bucket_name: str = "nutrition-agent"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    report_export_storage: str = "local"
    report_export_prefix: str = "reports"

    prometheus_enabled: bool = True
    otel_enabled: bool = False
    otel_service_name: str = "graduate-nutrition-agent-api"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
