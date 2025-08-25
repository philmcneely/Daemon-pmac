"""
Configuration management for Daemon
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    # App metadata
    app_name: str = "Daemon"
    version: str = "0.1.0"
    description: str = "Personal API Framework"
    
    # Security
    secret_key: str = Field(...)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = Field("sqlite:///./daemon.db")
    
    # Server
    host: str = Field("0.0.0.0")
    port: int = Field(8004)
    debug: bool = Field(False)
    reload: bool = Field(False)
    
    # Rate limiting
    rate_limit_requests: int = Field(60)
    rate_limit_window: int = Field(60)
    
    # CORS
    cors_origins: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8080"]
    )
    
    # Security - IP filtering
    allowed_ips: List[str] = Field([])
    
    # Backup
    backup_enabled: bool = Field(True)
    backup_dir: str = Field("./backups")
    backup_retention_days: int = Field(30)
    
    # Monitoring
    metrics_enabled: bool = Field(True)
    logging_level: str = Field("INFO")
    
    # MCP Support
    mcp_enabled: bool = Field(True)
    mcp_tools_prefix: str = Field("daemon_")
    
        # Multi-user settings
    multi_user_mode: str = Field("auto")  # "auto", "single", "multi"
    
    # API URLs
    api_prefix: str = Field("/api/v1")
    docs_url: Optional[str] = Field("/docs")
    redoc_url: Optional[str] = Field("/redoc")
    openapi_url: Optional[str] = Field("/openapi.json")
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("allowed_ips", mode="before")
    @classmethod
    def parse_allowed_ips(cls, v):
        if isinstance(v, str):
            return [ip.strip() for ip in v.split(",") if ip.strip()]
        return v


# Global settings instance
settings = Settings()
