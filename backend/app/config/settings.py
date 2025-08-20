import os
from typing import Optional
from pydantic import BaseSettings, validator
from decimal import Decimal

class DatabaseSettings(BaseSettings):
    """Database configuration"""
    database_url: str = "postgresql://user:password@localhost:5432/arbitragevault"
    echo_sql: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = False

class AppSettings(BaseSettings):
    """Application configuration"""
    app_name: str = "ArbitrageVault BookFinder"
    version: str = "1.2.5"
    debug: bool = False
    secret_key: str = "your-secret-key-change-in-production"
    
    # Pagination defaults
    default_page_size: int = 50
    max_page_size: int = 1000
    
    # Business logic thresholds
    default_roi_threshold: Decimal = Decimal("20.0")
    default_velocity_threshold: Decimal = Decimal("50.0")
    default_profit_threshold: Decimal = Decimal("10.0")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

class APIKeySettings(BaseSettings):
    """External API configuration"""
    keepa_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

class Settings(BaseSettings):
    """Combined application settings"""
    
    def __init__(self):
        super().__init__()
        self.database = DatabaseSettings()
        self.app = AppSettings()
        self.api_keys = APIKeySettings()
    
    @property
    def is_production(self) -> bool:
        return not self.app.debug
    
    @property
    def database_url(self) -> str:
        return self.database.database_url

# Global settings instance
settings = Settings()
