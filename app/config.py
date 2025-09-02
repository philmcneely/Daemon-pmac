"""
Module: config
Description: Configuration management and settings validation using Pydantic
             for environment-based configuration

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- pydantic: 2.5.2+ - Data validation and settings management
- pydantic-settings: 2.0+ - Environment variable configuration

Usage:
    from app.config import settings

    # Access configuration values
    database_url = settings.database_url
    secret_key = settings.secret_key

    # All settings automatically loaded from environment variables or .env file

Notes:
    - Settings automatically load from .env file in development
    - Environment variables override .env file values
    - Database URL defaults to SQLite for local development
    - Security settings have safe defaults but should be overridden in production
"""

from typing import Any, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # App metadata
    app_name: str = "Daemon"
    version: str = "0.3.1"
    description: str = "Personal API Framework"

    # Security
    secret_key: str = Field(default="dev_secret_key_change_in_production_12345")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = Field(default="sqlite:///./daemon.db")

    # Server configuration - bind to all interfaces
    host: str = Field(default="0.0.0.0")  # nosec B104
    port: int = Field(default=8007)
    debug: bool = Field(default=False)
    reload: bool = Field(default=False)

    # Rate limiting
    rate_limit_requests: int = Field(default=60)
    rate_limit_window: int = Field(default=60)

    # CORS
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:8006",  # Frontend server
            "http://localhost:8004",  # Original port
        ]
    )

    # Security - IP filtering
    allowed_ips: List[str] = Field(default_factory=list)

    # Backup
    backup_enabled: bool = Field(default=True)
    backup_dir: str = Field(default="./backups")
    backup_retention_days: int = Field(default=30)

    # Monitoring
    metrics_enabled: bool = Field(default=True)
    logging_level: str = Field(default="INFO")

    # MCP Support
    mcp_enabled: bool = Field(default=True)
    mcp_tools_prefix: str = Field(default="daemon_")

    # Multi-user settings
    multi_user_mode: str = Field(default="auto")  # "auto", "single", "multi"

    # Multi-app hosting configuration
    deployment_mode: str = Field(default="development")
    frontend_port: int = Field(default=8006)
    external_domain: Optional[str] = Field(default=None)
    api_base_path: str = Field(default="")
    frontend_base_path: str = Field(default="")
    daemon_api_url: Optional[str] = Field(default=None)

    # API URLs
    api_prefix: str = Field(default="/api/v1")
    docs_url: Optional[str] = Field(default="/docs")
    redoc_url: Optional[str] = Field(default="/redoc")
    openapi_url: Optional[str] = Field(default="/openapi.json")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return list(v) if v is not None else []

    @field_validator("allowed_ips", mode="before")
    @classmethod
    def parse_allowed_ips(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [ip.strip() for ip in v.split(",") if ip.strip()]
        return list(v) if v is not None else []


# Global settings instance
settings = Settings()
