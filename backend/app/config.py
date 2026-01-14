"""Configuration management for the DocuSign Clone backend."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "DocuSign Clone"
    app_env: str = "development"
    debug: bool = True
    api_version: str = "v1"
    secret_key: str = "dev-secret-key-change-in-production"

    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600

    # Email (SMTP)
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@example.com"
    smtp_from_name: str = "DocuSign Clone"

    # Rate Limiting
    rate_limit_per_minute: int = 100
    auth_rate_limit_per_minute: int = 10

    # Security
    bcrypt_rounds: int = 12
    password_min_length: int = 12
    verification_token_expire_hours: int = 24
    reset_token_expire_hours: int = 1
    max_login_attempts: int = 5
    account_lockout_minutes: int = 30

    # CORS
    cors_origins: str = "http://localhost:3000"
    cors_allow_credentials: bool = True

    # S3 Storage
    s3_bucket_name: str = "docusign-clone-dev"
    s3_region: str = "us-east-1"
    s3_access_key: str = "dev-access-key"
    s3_secret_key: str = "dev-secret-key"
    s3_endpoint_url: str = ""  # Optional, for S3-compatible services
    s3_presigned_url_expiration: int = 3600  # 1 hour in seconds

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
