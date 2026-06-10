"""
Database management module for HireGen AI.
Supports both local SQLite and PostgreSQL (e.g., Neon) database engines transparently
based on environment configuration. Supports candidate projects_count fields.
"""

import json
import logging
from typing import List, Dict, Any, Optional
import app_config as config

# Configure logger
logger = logging.getLogger(__name__)


def get_db_connection() -> Any:
    """
    Establishes and returns a database connection for SQLite or PostgreSQL.
    """
    try:
        if config.DB_DIALECT == "postgresql":
            import psycopg2
            if not config.DATABASE_URL:
                raise ValueError("DATABASE_URL is not set but dialect is configured as postgresql.")
            conn = psycopg2.connect(config.DATABASE_URL)
            logger.info("Using PostgreSQL database.")
            logger.info("PostgreSQL connection established.")
            return conn
        else:
            import sqlite3
            conn = sqlite3.connect(config.SQLITE_DB_FILE)
            logger.info("Using SQLite database for local development.")
            logger.info("SQLite connection established.")
            return conn
    except Exception as e:
        logger.error(f"Failed to connect to database ({config.DB_DIALECT}): {e}", exc_info=True)
        if config.DB_DIALECT == "postgresql":
            logger.warning(f"PostgreSQL connection failed. Falling back to SQLite. Error: {e}")
            import sqlite3
            config.DB_DIALECT = "sqlite"
            conn = sqlite3.connect(config.SQLITE_DB_FILE)
            logger.info("Using SQLite database for local development.")
            logger.info("SQLite connection established.")
            return conn
        raise e


def get_cursor(conn: Any) -> Any:
    """
    Returns a database cursor. For PostgreSQL, uses RealDictCursor for dictionary support.
    """
    if config.DB_DIALECT == "postgresql":
        from psycopg2.extras import RealDictCursor
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        conn.row_factory = sqlite3_row_factory
        return conn.cursor()


def sqlite3_row_factory(cursor, row):
    """
    Helper to return sqlite3 rows as dictionary results.
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def create_database() -> None:
    """
    Creates the candidates table if it does not already exist.
    """
    try:
        logger.info(f"Checking/creating database schema in ({config.DB_DIALECT})...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if config.DB_DIALECT == "postgresql":
            # PostgreSQL schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    resume_score REAL,
                    matched_skills TEXT,
                    missing_skills TEXT,
                    experience_years REAL,
                    education_score REAL,
                    certifications INTEGER,
                    prediction TEXT,
                    projects_count INTEGER DEFAULT 2,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            # SQLite schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    resume_score REAL,
                    matched_skills TEXT,
                    missing_skills TEXT,
                    experience_years REAL,
                    education_score REAL,
                    certifications INTEGER,
                    prediction TEXT,
                    projects_count INTEGER DEFAULT 2,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
        conn.commit()
        
        # Safe migration check: add projects_count column to existing database if missing
        try:
            placeholder = "%s" if config.DB_DIALECT == "postgresql" else "?"
            cursor.execute("ALTER TABLE candidates ADD COLUMN projects_count INTEGER DEFAULT 2")
            conn.commit()
            logger.info("Migrated schema: Added 'projects_count' column successfully.")
        except Exception:
            # Column already exists
            pass
            
        cursor.close()
        conn.close()
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}", exc_info=True)
        raise e


def insert_candidate(
    name: str,
    resume_score: float,
    matched_skills: List[str],
    missing_skills: List[str],
    experience_years: float,
    education_score: float,
    certifications: int,
    prediction: str,
    projects_count: int = 2
) -> int:
    """
    Inserts a candidate record and returns the created candidate's database ID.
    """
    try:
        matched_json = json.dumps(matched_skills)
        missing_json = json.dumps(missing_skills)

        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = "%s" if config.DB_DIALECT == "postgresql" else "?"
        query = f"""
            INSERT INTO candidates (
                name, resume_score, matched_skills, missing_skills, 
                experience_years, education_score, certifications, prediction, projects_count
            )
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """
        
        cursor.execute(
            query,
            (
                name, resume_score, matched_json, missing_json,
                experience_years, education_score, certifications, prediction, projects_count
            )
        )
        
        if config.DB_DIALECT == "postgresql":
            cursor.execute("SELECT LASTVAL()")
            candidate_id = cursor.fetchone()[0]
        else:
            candidate_id = cursor.lastrowid
            
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Successfully inserted candidate '{name}' with ID: {candidate_id}")
        return candidate_id if candidate_id is not None else -1

    except Exception as e:
        logger.error(f"Failed to insert candidate '{name}': {e}", exc_info=True)
        raise e


def get_all_candidates() -> List[Dict[str, Any]]:
    """
    Retrieves all candidates sorted by registration date.
    """
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        
        cursor.execute("SELECT * FROM candidates ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        candidates = []
        for row in rows:
            candidates.append({
                "id": row["id"],
                "name": row["name"],
                "resume_score": row["resume_score"],
                "matched_skills": json.loads(row["matched_skills"]) if row["matched_skills"] else [],
                "missing_skills": json.loads(row["missing_skills"]) if row["missing_skills"] else [],
                "experience_years": row["experience_years"],
                "education_score": row["education_score"],
                "certifications": row["certifications"],
                "prediction": row["prediction"],
                "projects_count": row.get("projects_count", 2),
                "created_at": str(row["created_at"])
            })
            
        cursor.close()
        conn.close()
        return candidates
    except Exception as e:
        logger.error(f"Failed to fetch all candidates: {e}", exc_info=True)
        return []


def get_candidate_by_id(candidate_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves candidate by unique ID.
    """
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        
        placeholder = "%s" if config.DB_DIALECT == "postgresql" else "?"
        cursor.execute(f"SELECT * FROM candidates WHERE id = {placeholder}", (candidate_id,))
        row = cursor.fetchone()
        
        record = None
        if row:
            record = {
                "id": row["id"],
                "name": row["name"],
                "resume_score": row["resume_score"],
                "matched_skills": json.loads(row["matched_skills"]) if row["matched_skills"] else [],
                "missing_skills": json.loads(row["missing_skills"]) if row["missing_skills"] else [],
                "experience_years": row["experience_years"],
                "education_score": row["education_score"],
                "certifications": row["certifications"],
                "prediction": row["prediction"],
                "projects_count": row.get("projects_count", 2),
                "created_at": str(row["created_at"])
            }
            
        cursor.close()
        conn.close()
        return record
    except Exception as e:
        logger.error(f"Failed to fetch candidate by ID {candidate_id}: {e}", exc_info=True)
        return None


def delete_candidate(candidate_id: int) -> bool:
    """
    Deletes candidate by ID.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = "%s" if config.DB_DIALECT == "postgresql" else "?"
        cursor.execute(f"DELETE FROM candidates WHERE id = {placeholder}", (candidate_id,))
        
        if config.DB_DIALECT == "postgresql":
            rows_affected = cursor.rowcount
        else:
            rows_affected = cursor.rowcount
            
        conn.commit()
        cursor.close()
        conn.close()
        
        return rows_affected > 0
    except Exception as e:
        logger.error(f"Failed to delete candidate ID {candidate_id}: {e}", exc_info=True)
        return False
