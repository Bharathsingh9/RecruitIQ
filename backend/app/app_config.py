"""
Pydantic environment configurations schema for FastAPI backend service.
"""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Project defaults
    PROJECT_NAME: str = "HireGen AI API"
    API_V1_STR: str = "/api/v1"
    
    # Auth secrets
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Groq API endpoints key
    GROQ_API_KEY: str
    LLM_MODEL: str = "llama-3.1-8b-instant"
    
    # Storage settings
    CHROMA_DB_PATH: str = "vector_store_data/chroma_db"
    FAISS_DB_PATH: str = "vector_store_data"
    
    # DB URL: Defaults to local SQLite if DATABASE_URL is empty
    DATABASE_URL: Optional[str] = None
    
    class Config:
        case_sensitive = True
        env_file = ".env"

from pydantic import ValidationError

# Instantiate configuration settings
try:
    settings = Settings()
except ValidationError as e:
    error_msg = str(e)
    if "GROQ_API_KEY" in error_msg:
        raise ValueError("Missing GROQ_API_KEY environment variable.")
    if "SECRET_KEY" in error_msg:
        raise ValueError("Missing SECRET_KEY environment variable.")
    raise
