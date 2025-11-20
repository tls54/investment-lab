"""
Configuration settings for Investment Lab.

This module loads settings from environment variables and .env file.
Uses Pydantic for validation and type safety.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Pydantic will automatically:
    1. Load from environment variables
    2. Load from .env file (if present)
    3. Validate types
    4. Provide defaults
    """
    
    # API Keys
    alpha_vantage_api_key: Optional[str] = None

    # API Configuration
    api_title: str = "Investment Lab API"
    api_version: str = "0.1.0"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    
    # CORS Settings
    cors_origins: str = "*"  # Comma-separated in .env: "http://localhost:3000,http://localhost:5173"
    
    # Cache Settings
    cache_ttl_seconds: int = 60
    
    # Environment
    environment: str = "development"  # development, staging, production
    debug: bool = True
    
    class Config:
        # Tell Pydantic to load from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Make env var names case-insensitive
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert comma-separated CORS origins to list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Create a single instance to use throughout the app
settings = Settings()