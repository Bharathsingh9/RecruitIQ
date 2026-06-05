"""
Report generation module for HireGen AI Recruiter Dashboard.
Formats candidate screening tables and exports them to CSV and Excel binary bytes.
"""

import io
import json
import logging
import pandas as pd
from typing import Union

from dashboard.analytics import get_candidates_df

# Configure logger
logger = logging.getLogger(__name__)


def prepare_report_df() -> pd.DataFrame:
    """
    Utility function to load candidate evaluations and format JSON lists
    into human-readable comma-separated strings.
    """
    df = get_candidates_df()
    if df.empty:
        return df

    df_report = df.copy()

    def clean_skill_list(raw_value: Union[str, list]) -> str:
        """
        Loads skill lists and formats them cleanly.
        """
        if not raw_value:
            return ""
        try:
            skills = json.loads(raw_value) if isinstance(raw_value, str) else raw_value
            if isinstance(skills, list):
                return ", ".join([str(s).title() for s in skills if s])
            return str(skills)
        except Exception as e:
            logger.warning(f"Error parsing skill list during report generation: {e}")
            return str(raw_value)

    # Apply formatting
    df_report["matched_skills"] = df_report["matched_skills"].apply(clean_skill_list)
    df_report["missing_skills"] = df_report["missing_skills"].apply(clean_skill_list)

    # Rename columns for presentation
    df_report.rename(columns={
        "id": "Candidate ID",
        "name": "Full Name",
        "resume_score": "Match Score (%)",
        "matched_skills": "Matched Skills",
        "missing_skills": "Missing Skills",
        "experience_years": "Years of Experience",
        "education_score": "Education Score",
        "certifications": "Certifications Count",
        "prediction": "Evaluation Status",
        "created_at": "Evaluation Date"
    }, inplace=True)

    return df_report


def generate_csv_report() -> str:
    """
    Generates a CSV formatted string of candidate evaluation records.

    Returns:
        str: Comma-separated candidate data.
    """
    try:
        logger.info("Generating CSV report bytes...")
        df_report = prepare_report_df()
        if df_report.empty:
            logger.warning("Empty candidate list. Returning empty string.")
            return ""
        return df_report.to_csv(index=False)
    except Exception as e:
        logger.error(f"Failed to generate CSV report: {e}", exc_info=True)
        return ""


def generate_excel_report() -> bytes:
    """
    Generates an Excel binary bytes buffer of candidate evaluation records.

    Returns:
        bytes: Compressed Excel workbook bytes.
    """
    try:
        logger.info("Generating Excel report bytes...")
        df_report = prepare_report_df()
        if df_report.empty:
            logger.warning("Empty candidate list. Returning empty bytes.")
            return b""

        # Output in-memory bytes stream
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_report.to_excel(writer, index=False, sheet_name="Candidate Rankings")
            
        excel_data = output.getvalue()
        logger.info("Successfully generated Excel report.")
        return excel_data

    except Exception as e:
        logger.error(f"Failed to generate Excel report: {e}", exc_info=True)
        return b""
