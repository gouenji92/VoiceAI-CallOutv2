from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    # Database
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 ngày
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "https://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "null"  # Cho phép file:// protocol
    ]
    
    # API Configuration
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "VoiceAI Backend API"
    DEBUG: bool = False
    
    # Model Paths
    INTENT_MODEL_PATH: str = "./models/phobert-intent-classifier"
    SENTIMENT_MODEL_NAME: str = "lct-distilbert-base-vietnamese-sentiment"
    
    @validator("JWT_SECRET_KEY", pre=True)
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

# Initialize settings
settings = Settings()