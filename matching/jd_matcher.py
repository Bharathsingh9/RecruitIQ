"""
Job Description Matching engine.
Calculates a match score and details of matching vs missing skills between resume and JD.
"""

import logging
from typing import List, Dict, Any

# Configure logger
logger = logging.getLogger(__name__)


def calculate_match_score(
    resume_skills: List[str],
    jd_skills: List[str]
) -> Dict[str, Any]:
    """
    Compares candidate resume skills with Job Description skills and calculates the match percentage.

    Args:
        resume_skills (List[str]): List of skills parsed from the candidate's resume.
        jd_skills (List[str]): List of skills required for the job description.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - "match_score": Float percentage (0.0 to 100.0) rounded to 2 decimal places.
            - "matched_skills": Sorted list of matched skills.
            - "missing_skills": Sorted list of missing skills required by the JD but absent from the resume.
    """
    logger.info("Initializing match score calculation...")
    
    # Handle empty or invalid inputs
    if not jd_skills:
        logger.warning("Job description skills list is empty or None. Returning 0.0 match score.")
        return {
            "match_score": 0.0,
            "matched_skills": [],
            "missing_skills": []
        }

    # Normalize: Convert to lowercase, strip whitespaces, and deduplicate using sets
    resume_set = {s.strip().lower() for s in resume_skills if s and s.strip()}
    jd_set = {s.strip().lower() for s in jd_skills if s and s.strip()}

    if not jd_set:
        logger.warning("Deduplicated Job Description skills set is empty. Returning 0.0 match score.")
        return {
            "match_score": 0.0,
            "matched_skills": [],
            "missing_skills": []
        }

    # Calculations
    matched_skills = resume_set.intersection(jd_set)
    missing_skills = jd_set.difference(resume_set)

    # Compute percentage
    raw_score = (len(matched_skills) / len(jd_set)) * 100.0
    match_score = round(raw_score, 2)

    logger.info(
        f"Match Score computed: {match_score}% (Matched: {len(matched_skills)}/{len(jd_set)}, "
        f"Missing: {len(missing_skills)})"
    )

    return {
        "match_score": match_score,
        "matched_skills": sorted(list(matched_skills)),
        "missing_skills": sorted(list(missing_skills))
    }


# Optional: Example usage block for standalone module testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_resume = ["Python", "SQL", "Docker", "Git"]
    test_jd = ["python", "SQL", "Docker", "AWS", "Kubernetes"]
    
    results = calculate_match_score(test_resume, test_jd)
    print("\n--- Test JD Matcher Results ---")
    print(f"Match Score   : {results['match_score']}%")
    print(f"Matched Skills : {results['matched_skills']}")
    print(f"Missing Skills : {results['missing_skills']}")
    print("--------------------------------\n")
