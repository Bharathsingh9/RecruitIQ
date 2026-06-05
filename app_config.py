"""
Configuration module for HireGen AI.
Loads settings from environment variables and defines application-wide defaults.
Renamed to app_config to prevent namespace conflicts.
"""

import os
import logging
from typing import Optional

# Configure logger
logger = logging.getLogger(__name__)

# Core API Keys
GROQ_API_KEY: Optional[str] = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY environment variable.")

# Database configuration
# If DATABASE_URL is set (e.g. Postgres on Render/Railway/Neon), use Postgres. Otherwise, default to SQLite.
DATABASE_URL: Optional[str] = os.environ.get("DATABASE_URL")
DB_DIALECT: str = "postgresql" if DATABASE_URL else "sqlite"
SQLITE_DB_FILE: str = os.environ.get("SQLITE_DB_FILE", "hiregen.db")

# Vector Database paths
CHROMA_DB_PATH: str = os.environ.get("CHROMA_DB_PATH", "vector_store_data/chroma_db")
FAISS_DB_PATH: str = os.environ.get("FAISS_DB_PATH", "vector_store_data")

# GenAI model selection
LLM_MODEL: str = os.environ.get("LLM_MODEL", "llama-3.1-8b-instant")
EMBEDDING_MODEL: str = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Application Settings
DEBUG: bool = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

def get_db_connection_params() -> dict:
    """
    Returns database connection details depending on configured dialect.
    """
    if DB_DIALECT == "postgresql":
        logger.info("Database dialect set to PostgreSQL.")
        return {"url": DATABASE_URL}
    else:
        logger.info(f"Database dialect set to SQLite. Database file: {SQLITE_DB_FILE}")
        return {"file": SQLITE_DB_FILE}

logger.info(f"Configuration loaded. Dialect: {DB_DIALECT}, Model: {LLM_MODEL}")
