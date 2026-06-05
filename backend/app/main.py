"""
FastAPI Application Entry Point.
Initializes middleware, routing structures, and startup database schema creation.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.app_config import settings
from app.api.v1 import screening, batch, copilot, rag, analytics, reports
from app.database.session import Base, engine

# Setup logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy tables
try:
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables successfully created.")
except Exception as db_err:
    logger.error(f"Failed to create database tables during startup: {db_err}")

# Create app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Register CORS Middleware to allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(screening.router, prefix=f"{settings.API_V1_STR}/screening", tags=["Candidate Screening"])
app.include_router(batch.router, prefix=f"{settings.API_V1_STR}/batch", tags=["Batch Processing & Leaderboard"])
app.include_router(copilot.router, prefix=f"{settings.API_V1_STR}/copilot", tags=["AI Interview Copilot"])
app.include_router(rag.router, prefix=f"{settings.API_V1_STR}/rag", tags=["RAG Knowledge Assistant"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Dashboard Analytics"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports Export"])


@app.get("/")
def read_root():
    """
    Service heartbeat diagnostic status.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME
    }
