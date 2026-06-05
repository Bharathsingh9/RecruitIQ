"""
Feature Engineering module for HireGen AI.
Prepares parsed and input metrics into a format suitable for the Machine Learning model.
"""

import pandas as pd
import logging

# Configure logger
logger = logging.getLogger(__name__)


def prepare_features(
    skills_match: float,
    experience_years: float,
    education_score: float,
    certifications: int
) -> pd.DataFrame:
    """
    Standardizes candidate metrics into a structured Pandas DataFrame.
    Matches feature column order used during classifier model training.

    Args:
        skills_match (float): Match percentage of core skills (0.0 to 100.0).
        experience_years (float): Number of relevant years of experience.
        education_score (float): Assessment score for candidate's educational background (0.0 to 100.0).
        certifications (int): Number of certifications the candidate has.

    Returns:
        pd.DataFrame: A single-row DataFrame containing the input features.
    """
    try:
        data = {
            "skills_match": [float(skills_match)],
            "experience_years": [float(experience_years)],
            "education_score": [float(education_score)],
            "certifications": [int(certifications)]
        }
        df = pd.DataFrame(data)
        logger.info(f"Successfully prepared features: {data}")
        return df
    except Exception as e:
        logger.error(f"Error during feature preparation: {e}", exc_info=True)
        raise e
