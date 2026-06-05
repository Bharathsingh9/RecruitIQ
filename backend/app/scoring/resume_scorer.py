"""
Resume Scoring Engine for HireGen AI.
Calculates independent candidate scoring attributes and maps them to letter grades
based on a weighted breakdown of skills, experience, projects, and education.
"""

import logging
from typing import Dict, Any

# Configure logger
logger = logging.getLogger(__name__)

# Configurable Weights (Must sum to 1.0)
WEIGHTS = {
    "skills": 0.40,
    "experience": 0.25,
    "projects": 0.20,
    "education": 0.15
}


def calculate_skills_score(skills_match: float) -> float:
    """
    Computes weighted score component for skills.
    skills_match represents percentage (0.0 to 100.0).
    """
    # Clip value to valid range
    val = max(0.0, min(100.0, float(skills_match)))
    return val * WEIGHTS["skills"]


def calculate_experience_score(experience_years: float) -> float:
    """
    Computes experience score component out of 100, then weights it.
    Uses linear progression model: score = years * 20 + 8 (for years >= 0.5, capped at 100).
    """
    years = max(0.0, float(experience_years))
    if years == 0.0:
        score = 0.0
    else:
        score = min(years * 20.0 + 8.0, 100.0)
    return score * WEIGHTS["experience"]


def calculate_projects_score(projects_count: int) -> float:
    """
    Computes projects score component out of 100, then weights it.
    Uses linear progression model: score = count * 15 + 10 (for count >= 1, capped at 100).
    """
    count = max(0, int(projects_count))
    if count == 0:
        score = 0.0
    else:
        score = min(count * 15.0 + 10.0, 100.0)
    return score * WEIGHTS["projects"]


def calculate_education_score(education_score: float) -> float:
    """
    Computes weighted score component for education.
    education_score represents percentage (0.0 to 100.0).
    """
    val = max(0.0, min(100.0, float(education_score)))
    return val * WEIGHTS["education"]


def assign_grade(score: float) -> str:
    """
    Maps score out of 100 to standard letter grades.
    """
    if score >= 90.0:
        return "A+"
    elif score >= 80.0:
        return "A"
    elif score >= 70.0:
        return "B"
    elif score >= 60.0:
        return "C"
    else:
        return "D"


def calculate_overall_resume_score(
    skills_match: float,
    experience_years: float,
    projects_count: int,
    education_score: float
) -> Dict[str, Any]:
    """
    Calculates overall weighted score and assigns evaluation grade.

    Args:
        skills_match (float): Skills match score (0 to 100).
        experience_years (float): Candidate's years of experience.
        projects_count (int): Number of projects the candidate worked on.
        education_score (float): Education score (0 to 100).

    Returns:
        Dict[str, Any]: Evaluation summary:
            - "overall_score": Rounded overall score (0 to 100).
            - "grade": Assigned letter grade.
            - "breakdown": Dictionary of rounded components scores.
    """
    logger.info("Calculating candidate resume scores...")
    
    # 1. Compute components
    s_comp = calculate_skills_score(skills_match)
    exp_comp = calculate_experience_score(experience_years)
    proj_comp = calculate_projects_score(projects_count)
    edu_comp = calculate_education_score(education_score)

    # 2. Compute overall sum
    overall_raw = s_comp + exp_comp + proj_comp + edu_comp
    overall_score = round(overall_raw)
    
    # Clip just in case of float boundary exceeding 100
    overall_score = max(0, min(100, overall_score))
    
    # Assign grade
    grade = assign_grade(float(overall_score))

    logger.info(f"Resume Score calculated: {overall_score}/100. Grade: {grade}")

    return {
        "overall_score": overall_score,
        "grade": grade,
        "breakdown": {
            "skills": round(s_comp),
            "experience": round(exp_comp),
            "projects": round(proj_comp),
            "education": round(edu_comp)
        }
    }


# Optional: Standalone scoring test block
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Run test parameters matching requirements:
    # Skills Match = 90, Experience Years = 4, Projects Count = 5, Education Score = 85
    test_cand = {
        "skills_match": 90.0,
        "experience_years": 4.0,
        "projects_count": 5,
        "education_score": 85.0
    }
    
    res = calculate_overall_resume_score(**test_cand)
    print("\n--- Standalone Resume Scorer Results ---")
    print(f"Overall Score : {res['overall_score']}")
    print(f"Grade         : {res['grade']}")
    print(f"Breakdown     : {res['breakdown']}")
    print("----------------------------------------\n")
