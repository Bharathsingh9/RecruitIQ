"""
Database session manager using SQLAlchemy.
Creates a connection engine and localized sessionmaker objects based on configuration dialect.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.app_config import settings

# Determine final URL connection string
if settings.DATABASE_URL:
    db_url = settings.DATABASE_URL
    # Force sslmode=require for Neon PostgreSQL
    if "postgres" in db_url and "sslmode" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}sslmode=require"
    
    # Engine arguments for Postgres
    engine = create_engine(db_url, pool_pre_ping=True)
else:
    # Fallback to local SQLite database
    db_url = "sqlite:///./hiregen.db"
    engine = create_engine(
        db_url, 
        connect_args={"check_same_thread": False}
    )

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models mappings
Base = declarative_base()
