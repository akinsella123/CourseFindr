from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    app_name: str = "CourseMatch API"
    debug: bool = False
    version: str = "1.0.0"
    
    # Database settings
    database_url: str = "postgresql://user:password@localhost/coursematch"
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    
    # Security settings
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS settings
    backend_cors_origins: list = ["http://localhost:3000", "http://localhost:8080"]
    
    # NLP settings
    spacy_model: str = "en_core_web_sm"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    """Get cached settings instance."""
    return Settings()


settings = get_settings()