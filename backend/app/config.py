"""Configuration settings for the Wildlife Sightings API."""

from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application settings
    app_name: str = "Wildlife Sightings API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API settings
    api_v1_str: str = "/api/v1"
    
    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Database settings
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 0
    
    # Supabase settings
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: Optional[str] = None
    
    # JWT settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # Email settings (for password reset)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Redis settings (for caching)
    redis_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
