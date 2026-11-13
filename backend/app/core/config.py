"""Application configuration loaded from environment.

Fails fast at import time if required secrets are missing.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "IAM Platform"
    app_env: str = "development"
    app_debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # --- Security ---
    secret_key: str = Field(..., min_length=32)
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    password_reset_token_expire_minutes: int = 30
    jwt_algorithm: str = "HS256"

    # --- Argon2id ---
    argon2_time_cost: int = 3
    argon2_memory_cost: int = 65536
    argon2_parallelism: int = 4
    argon2_hash_len: int = 32
    argon2_salt_len: int = 16

    # --- Lockout ---
    max_failed_login_attempts: int = 5
    lockout_duration_minutes: int = 15

    # --- Database ---
    database_url: str = Field(...)

    # --- Redis ---
    redis_url: str = Field(...)

    # --- Rate limiting (Phase 4, D32–D35) ---
    ratelimit_enabled: bool = True
    ratelimit_key_prefix: str = "iam:rl"
    ratelimit_login_ip_limit: int = 10
    ratelimit_login_ip_window: int = 60
    ratelimit_login_account_limit: int = 5
    ratelimit_login_account_window: int = 60
    ratelimit_refresh_ip_limit: int = 30
    ratelimit_refresh_ip_window: int = 60
    ratelimit_register_ip_limit: int = 5
    ratelimit_register_ip_window: int = 300
    ratelimit_forgot_ip_limit: int = 3
    ratelimit_forgot_ip_window: int = 300
    ratelimit_forgot_email_limit: int = 3
    ratelimit_forgot_email_window: int = 3600

    # --- CORS ---
    cors_origins: str = "http://localhost:3000"

    @field_validator("secret_key")
    @classmethod
    def _reject_placeholder_secret(cls, v: str) -> str:
        if v.startswith("CHANGE_ME"):
            raise ValueError(
                "SECRET_KEY is still the placeholder. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
