"""
Centralized configuration loader for all services
Loads environment variables from .env file
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


class Config:
    """Centralized configuration for all services"""
    
    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    DB_TYPE: str = os.getenv("DB_TYPE", "postgresql")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "project_management")
    DB_USER: str = os.getenv("DB_USER", "paperless")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "paperless")
    
    # Auto-generate DATABASE_URL if not provided
    @property
    def DATABASE_URL(self) -> str:
        """Generate database URL from components"""
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url
        
        if self.DB_TYPE == "postgresql":
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        elif self.DB_TYPE == "mysql":
            return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        elif self.DB_TYPE == "sqlite":
            return f"sqlite+aiosqlite:///{self.DB_NAME}.db"
        else:
            raise ValueError(f"Unsupported database type: {self.DB_TYPE}")
    
    # ============================================
    # ORCHESTRATOR SERVICE
    # ============================================
    ORCHESTRATOR_HOST: str = os.getenv("ORCHESTRATOR_HOST", "0.0.0.0")
    ORCHESTRATOR_PORT: int = int(os.getenv("ORCHESTRATOR_PORT", "9000"))
    ORCHESTRATOR_DEBUG: bool = os.getenv("ORCHESTRATOR_DEBUG", "true").lower() == "true"
    
    # ============================================
    # ATLAS SERVICE
    # ============================================
    ATLAS_HOST: str = os.getenv("ATLAS_HOST", "0.0.0.0")
    ATLAS_PORT: int = int(os.getenv("ATLAS_PORT", "8000"))
    ATLAS_DEBUG: bool = os.getenv("ATLAS_DEBUG", "true").lower() == "true"
    ATLAS_DATABASE_URL: str = os.getenv("ATLAS_DATABASE_URL", "")
    
    @property
    def atlas_database_url(self) -> str:
        """Get Atlas database URL or use main database"""
        if self.ATLAS_DATABASE_URL:
            return self.ATLAS_DATABASE_URL
        return self.DATABASE_URL
    
    # ============================================
    # WORKPULSE SERVICE
    # ============================================
    WORKPULSE_HOST: str = os.getenv("WORKPULSE_HOST", "0.0.0.0")
    WORKPULSE_PORT: int = int(os.getenv("WORKPULSE_PORT", "8001"))
    WORKPULSE_DEBUG: bool = os.getenv("WORKPULSE_DEBUG", "true").lower() == "true"
    WORKPULSE_DATABASE_URL: str = os.getenv("WORKPULSE_DATABASE_URL", "")
    
    @property
    def workpulse_database_url(self) -> str:
        """Get WorkPulse database URL or use main database"""
        if self.WORKPULSE_DATABASE_URL:
            return self.WORKPULSE_DATABASE_URL
        return self.DATABASE_URL
    
    # ============================================
    # EPR SERVICE
    # ============================================
    EPR_HOST: str = os.getenv("EPR_HOST", "0.0.0.0")
    EPR_PORT: int = int(os.getenv("EPR_PORT", "8003"))
    EPR_DEBUG: bool = os.getenv("EPR_DEBUG", "true").lower() == "true"
    EPR_DATABASE_URL: str = os.getenv("EPR_DATABASE_URL", "")
    
    @property
    def epr_database_url(self) -> str:
        """Get EPR database URL or use main database"""
        if self.EPR_DATABASE_URL:
            return self.EPR_DATABASE_URL
        return self.DATABASE_URL
    
    # ============================================
    # LABS SERVICE
    # ============================================
    LABS_HOST: str = os.getenv("LABS_HOST", "0.0.0.0")
    LABS_PORT: int = int(os.getenv("LABS_PORT", "8004"))
    LABS_DEBUG: bool = os.getenv("LABS_DEBUG", "true").lower() == "true"
    LABS_DATABASE_URL: str = os.getenv("LABS_DATABASE_URL", "")
    
    @property
    def labs_database_url(self) -> str:
        """Get Labs database URL or use main database"""
        if self.LABS_DATABASE_URL:
            return self.LABS_DATABASE_URL
        return self.DATABASE_URL
    
    # ============================================
    # JWT CONFIGURATION
    # ============================================
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_DAYS: int = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
    
    # ============================================
    # SERVICE URLS
    # ============================================
    ATLAS_SERVICE_URL: str = os.getenv("ATLAS_SERVICE_URL", "http://localhost:8000")
    WORKPULSE_SERVICE_URL: str = os.getenv("WORKPULSE_SERVICE_URL", "http://localhost:8001")
    EPR_SERVICE_URL: str = os.getenv("EPR_SERVICE_URL", "http://localhost:8003")
    LABS_SERVICE_URL: str = os.getenv("LABS_SERVICE_URL", "http://localhost:8004")
    
    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    
    # ============================================
    # CORS CONFIGURATION
    # ============================================
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # ============================================
    # ENVIRONMENT
    # ============================================
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # ============================================
    # DERIVED PROPERTIES
    # ============================================
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging"""
        return self.ENVIRONMENT == "staging"


# Create singleton instance
config = Config()


def get_config() -> Config:
    """Get configuration instance"""
    return config


def print_config() -> None:
    """Print current configuration (for debugging)"""
    print("\n" + "="*50)
    print("CURRENT CONFIGURATION")
    print("="*50)
    print(f"Environment: {config.ENVIRONMENT}")
    print(f"Database Type: {config.DB_TYPE}")
    print(f"Database Host: {config.DB_HOST}:{config.DB_PORT}")
    print(f"Database Name: {config.DB_NAME}")
    print(f"Orchestrator: {config.ORCHESTRATOR_HOST}:{config.ORCHESTRATOR_PORT}")
    print(f"Atlas: {config.ATLAS_HOST}:{config.ATLAS_PORT}")
    print(f"WorkPulse: {config.WORKPULSE_HOST}:{config.WORKPULSE_PORT}")
    print(f"EPR: {config.EPR_HOST}:{config.EPR_PORT}")
    print(f"Labs: {config.LABS_HOST}:{config.LABS_PORT}")
    print("="*50 + "\n")
