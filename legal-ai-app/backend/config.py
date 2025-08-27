from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # JWT Configuration
    jwt_secret: str = "your-super-secret-jwt-key-here"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database Configuration
    database_url: str = "postgresql://username:password@localhost:5432/legal_ai_db"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # Google Drive API Configuration
    google_drive_client_id: str = ""
    google_drive_client_secret: str = ""
    google_drive_credentials_file: str = "credentials.json"
    
    # AI Model Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Model Paths
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    faiss_index_path: str = "./ml_models/faiss_index.bin"
    classifier_model_path: str = "./ml_models/legal_classifier.pkl"
    
    # Application Settings
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()