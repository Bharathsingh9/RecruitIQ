"""
Configuration module for HireGen AI.
Loads settings from environment variables and defines application-wide defaults.
Renamed to app_config to prevent namespace conflicts.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# Core API Keys
GROQ_API_KEY: Optional[str] = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY environment variable.")

# Database configuration
DATABASE_URL: Optional[str] = os.environ.get("DATABASE_URL")

logger.info(f"DATABASE_URL = {DATABASE_URL}")

# Validation logic for DATABASE_URL
invalid_placeholders = [
    "",
    "your_database_url_here",
    "placeholder",
    "example",
    "test",
    "dummy"
]

if DATABASE_URL is None or DATABASE_URL.strip().lower() in invalid_placeholders:
    logger.warning("Invalid DATABASE_URL detected.")
    logger.warning("Switching to SQLite.")
    DATABASE_URL = None
elif not (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")):
    logger.warning("Invalid DATABASE_URL detected (not a valid postgres URL).")
    logger.warning("Switching to SQLite.")
    DATABASE_URL = None

if DATABASE_URL is None:
    DB_DIALECT = "sqlite"
else:
    DB_DIALECT = "postgresql"

logger.info(f"Selected database type: {DB_DIALECT}")

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
        return {"url": DATABASE_URL}
    else:
        return {"file": SQLITE_DB_FILE}

logger.info(f"Configuration loaded. Dialect: {DB_DIALECT}, Model: {LLM_MODEL}")
