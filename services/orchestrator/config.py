"""
Configuration settings for Orchestrator
Uses centralized config_loader from project root
"""
import sys
from pathlib import Path
import os

# Try to import config_loader from current directory first (Docker)
# Then try parent directories (local development)
try:
    from config_loader import get_config
except ModuleNotFoundError:
    try:
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        from config_loader import get_config
    except ModuleNotFoundError:
        # Add parent directory to path to import config_loader
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from config_loader import get_config

# Get centralized config
config = get_config()

# Create settings object for backward compatibility
class Settings:
    """Settings wrapper for centralized config"""
    
    @property
    def database_url(self) -> str:
        return config.DATABASE_URL
    
    @property
    def jwt_secret(self) -> str:
        return config.JWT_SECRET
    
    @property
    def jwt_algorithm(self) -> str:
        return config.JWT_ALGORITHM
    
    @property
    def access_token_expire_days(self) -> int:
        return config.JWT_EXPIRE_DAYS
    
    @property
    def atlas_service_url(self) -> str:
        return config.ATLAS_SERVICE_URL
    
    @property
    def workpulse_service_url(self) -> str:
        return config.WORKPULSE_SERVICE_URL
    
    @property
    def epr_service_url(self) -> str:
        return config.EPR_SERVICE_URL
    
    @property
    def labs_service_url(self) -> str:
        return config.LABS_SERVICE_URL
    
    @property
    def service_secret(self) -> str:
        return "shared-secret-token"
    
    @property
    def environment(self) -> str:
        return config.ENVIRONMENT
    
    @property
    def debug(self) -> bool:
        return config.DEBUG


settings = Settings()
