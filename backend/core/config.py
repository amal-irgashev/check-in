from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Info
    PROJECT_NAME: str = "Journal API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Server Settings
    BACKEND_URL: str = "http://localhost:8000"
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8501"]
    PUBLIC_PATHS: set = {"/", "/docs", "/openapi.json"}
    
    # External Services
    OPENAI_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()
