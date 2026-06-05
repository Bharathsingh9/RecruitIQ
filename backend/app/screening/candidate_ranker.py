"""
Candidate Ranker Engine for HireGen AI.
Calculates composite rank scores by weighting resume score, skills match, 
machine learning classification confidence, candidate experience, and certifications.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Configurable composite rank weights (Must sum to 1.0)
RANK_WEIGHTS = {
    "resume_score": 0.35,      # Independent Resume Scorer
    "match_score": 0.35,       # Skills similarity/match score
    "ml_prediction": 0.15,     # ML model class confidence
    "experience": 0.10,        # Years of experience (scaled)
    "certifications": 0.05     # Certifications count (scaled)
}


def calculate_rank_score(
    resume_score: float,
    match_score: float,
    prediction: str,
    confidence: float,
    experience_years: float,
    certifications_count: int
) -> float:
    """
    Computes a weighted, multi-factor composite ranking score out of 100.

    Args:
        resume_score (float): Score out of 100 from resume scorer engine.
        match_score (float): Skills JD match score (0.0 to 100.0).
        prediction (str): Class prediction (Shortlist/Needs Review/Reject).
        confidence (float): Confidence score (0.0 to 1.0).
        experience_years (float): Total candidate experience years.
        certifications_count (int): Total certifications candidate holds.

    Returns:
        float: Rounded composite rank score (0.0 to 100.0).
    """
    try:
        # 1. Base scores
        r_score = max(0.0, min(100.0, float(resume_score)))
        m_score = max(0.0, min(100.0, float(match_score)))
        
        # 2. ML Prediction contribution
        # Shortlist gets full confidence value, Needs Review gets half, Reject gets 0
        pred = str(prediction).strip().lower()
        if "shortlist" in pred:
            ml_factor = float(confidence) * 100.0
        elif "review" in pred:
            ml_factor = float(confidence) * 50.0
        else:
            ml_factor = 0.0
            
        # 3. Experience scaling (scaled up to 10 years)
        exp_factor = min(float(experience_years) / 10.0, 1.0) * 100.0
        
        # 4. Certifications scaling (scaled up to 5 certs)
        cert_factor = min(float(certifications_count) / 5.0, 1.0) * 100.0
        
        # 5. Composite sum
        composite_score = (
            r_score * RANK_WEIGHTS["resume_score"] +
            m_score * RANK_WEIGHTS["match_score"] +
            ml_factor * RANK_WEIGHTS["ml_prediction"] +
            exp_factor * RANK_WEIGHTS["experience"] +
            cert_factor * RANK_WEIGHTS["certifications"]
        )
        
        final_score = round(composite_score, 2)
        logger.debug(f"Computed candidate rank score: {final_score}/100 (Resume: {r_score}, Match: {m_score}, ML: {ml_factor}, Exp: {exp_factor}, Certs: {cert_factor})")
        return max(0.0, min(100.0, final_score))
        
    except Exception as e:
        logger.error(f"Error calculating candidate rank score: {e}", exc_info=True)
        # Fallback to simple average of resume and match score
        return round((float(resume_score) + float(match_score)) / 2.0, 2)
