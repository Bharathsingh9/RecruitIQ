"""
Skill Gap Analyzer module.
Identifies skill gaps and recommends course resources based on a mapping dictionary.
"""

import logging
from typing import List, Dict, Any

# Configure logger
logger = logging.getLogger(__name__)

# Configurable Skill to Learning Course Map
SKILL_LEARNING_MAP = {
    "aws": "AWS Cloud Practitioner",
    "docker": "Docker Fundamentals",
    "kubernetes": "Kubernetes Basics",
    "ci/cd": "GitHub Actions CI/CD",
    "machine learning": "Machine Learning Specialization",
    "deep learning": "Deep Learning Specialization",
    "python": "Python for Everybody Specialization",
    "java": "Java Programming and Software Engineering Fundamentals",
    "sql": "SQL for Data Science",
    "pandas": "Data Analysis with Python (Pandas/Numpy)",
    "numpy": "Numerical Python Fundamentals"
}


def generate_learning_path(missing_skills: List[str]) -> Dict[str, Any]:
    """
    Identifies missing skills from the job description and recommends corresponding learning resources.

    Args:
        missing_skills (List[str]): List of skills missing in the candidate's resume.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - "missing_skills": Sorted list of lowercase missing skills.
            - "learning_path": Sorted list of unique recommended course/resource names.
    """
    logger.info("Initializing learning path generation for missing skills...")
    
    if not missing_skills:
        logger.info("No missing skills provided. Returning empty learning path.")
        return {
            "missing_skills": [],
            "learning_path": []
        }

    # Clean and deduplicate missing skills
    cleaned_skills = sorted(list({s.strip().lower() for s in missing_skills if s and s.strip()}))
    recommendations = set()

    for skill in cleaned_skills:
        if skill in SKILL_LEARNING_MAP:
            course = SKILL_LEARNING_MAP[skill]
            logger.info(f"Matched skill '{skill}' to recommended course '{course}'")
            recommendations.add(course)
        else:
            # Handle unknown skills gracefully by suggesting a standardized online resource fallback
            default_recommendation = f"{skill.title()} Certification Course / Official Tutorial"
            logger.info(f"Unknown skill '{skill}'. Gracefully falling back to: '{default_recommendation}'")
            recommendations.add(default_recommendation)

    sorted_recommendations = sorted(list(recommendations))

    return {
        "missing_skills": cleaned_skills,
        "learning_path": sorted_recommendations
    }


# Optional: Example usage block for standalone module testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_missing = ["aws", "kubernetes", "ci/cd", "rust", "deep learning"]
    
    results = generate_learning_path(test_missing)
    print("\n--- Test Skill Gap Analyzer Results ---")
    print(f"Missing Skills: {results['missing_skills']}")
    print("Learning Path Recommended:")
    for course in results['learning_path']:
        print(f" - {course}")
    print("----------------------------------------\n")
