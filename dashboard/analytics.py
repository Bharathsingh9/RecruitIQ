"""
Analytics module for HireGen AI Recruiter Dashboard.
Queries candidate records from SQLite and generates analytical metrics and dataframes.
"""

import json
import sqlite3
import logging
import pandas as pd
from typing import Dict, Any, List

# Configure logger
logger = logging.getLogger(__name__)

DB_FILE = "hiregen.db"


def get_candidates_df() -> pd.DataFrame:
    """
    Loads all candidate records from the SQLite database into a Pandas DataFrame.
    Returns an empty DataFrame with core columns if the table does not exist or has no rows.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            # Query candidate list
            df = pd.read_sql_query("SELECT * FROM candidates", conn)
            logger.info(f"Loaded DataFrame with {len(df)} candidate rows.")
            return df
    except Exception as e:
        logger.error(f"Error loading candidates dataframe: {e}")
        # Return empty structured dataframe as fallback
        return pd.DataFrame(columns=[
            "id", "name", "resume_score", "matched_skills", "missing_skills", 
            "experience_years", "education_score", "certifications", "prediction", "created_at"
        ])


def get_total_candidates() -> int:
    """
    Returns the total count of screened candidates.
    """
    df = get_candidates_df()
    return len(df)


def get_shortlisted_candidates() -> int:
    """
    Returns the count of candidates classified as 'Shortlist'.
    """
    df = get_candidates_df()
    if df.empty or "prediction" not in df.columns:
        return 0
    return int(df[df["prediction"] == "Shortlist"].shape[0])


def get_rejected_candidates() -> int:
    """
    Returns the count of candidates classified as 'Reject'.
    """
    df = get_candidates_df()
    if df.empty or "prediction" not in df.columns:
        return 0
    return int(df[df["prediction"] == "Reject"].shape[0])


def get_review_candidates() -> int:
    """
    Returns the count of candidates classified as 'Needs Review'.
    """
    df = get_candidates_df()
    if df.empty or "prediction" not in df.columns:
        return 0
    return int(df[df["prediction"] == "Needs Review"].shape[0])


def get_average_match_score() -> float:
    """
    Returns the average match score across all candidates, rounded to 2 decimal places.
    """
    df = get_candidates_df()
    if df.empty or "resume_score" not in df.columns:
        return 0.0
    return round(float(df["resume_score"].mean()), 2)


def get_top_skills(n: int = 5) -> pd.DataFrame:
    """
    Analyzes matched skills frequency and returns the top n skills found in candidate resumes.
    """
    df = get_candidates_df()
    if df.empty or "matched_skills" not in df.columns:
        return pd.DataFrame(columns=["Skill", "Count"])

    all_skills = []
    for _, row in df.iterrows():
        try:
            skills_raw = row["matched_skills"]
            if isinstance(skills_raw, str):
                skills = json.loads(skills_raw)
            else:
                skills = skills_raw
            if isinstance(skills, list):
                all_skills.extend([s.strip().lower() for s in skills if s])
        except Exception as e:
            logger.warning(f"Error parsing matched skills: {e}")
            continue

    if not all_skills:
        return pd.DataFrame(columns=["Skill", "Count"])

    counts = pd.Series(all_skills).value_counts().reset_index()
    counts.columns = ["Skill", "Count"]
    # Capitalize for display consistency
    counts["Skill"] = counts["Skill"].str.title()
    return counts.head(n)


def get_top_missing_skills(n: int = 5) -> pd.DataFrame:
    """
    Analyzes missing skills frequency and returns the top n skills candidates are lacking relative to JDs.
    """
    df = get_candidates_df()
    if df.empty or "missing_skills" not in df.columns:
        return pd.DataFrame(columns=["Skill", "Count"])

    all_missing = []
    for _, row in df.iterrows():
        try:
            skills_raw = row["missing_skills"]
            if isinstance(skills_raw, str):
                skills = json.loads(skills_raw)
            else:
                skills = skills_raw
            if isinstance(skills, list):
                all_missing.extend([s.strip().lower() for s in skills if s])
        except Exception as e:
            logger.warning(f"Error parsing missing skills: {e}")
            continue

    if not all_missing:
        return pd.DataFrame(columns=["Skill", "Count"])

    counts = pd.Series(all_missing).value_counts().reset_index()
    counts.columns = ["Skill", "Count"]
    counts["Skill"] = counts["Skill"].str.title()
    return counts.head(n)


def get_candidate_distribution() -> pd.DataFrame:
    """
    Returns prediction category distribution counts.
    """
    df = get_candidates_df()
    if df.empty or "prediction" not in df.columns:
        return pd.DataFrame(columns=["Prediction", "Count"])
        
    counts = df["prediction"].value_counts().reset_index()
    counts.columns = ["Prediction", "Count"]
    return counts
