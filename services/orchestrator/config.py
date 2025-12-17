"""
Configuration settings for Orchestrator
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://admin:secure_password@localhost:5432/project_management"
    
    # JWT
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_days: int = 7
    
    # Service URLs
    atlas_service_url: str = "http://localhost:8000"
    workpulse_service_url: str = "http://localhost:8001"
    epr_service_url: str = "http://localhost:8003"
    labs_service_url: str = "http://localhost:8004"
    
    # Service Communication
    service_secret: str = "shared-secret-token"
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
