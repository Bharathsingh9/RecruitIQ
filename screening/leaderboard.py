"""
Leaderboard generation and search/filter module for HireGen AI.
Retrieves candidate records, computes composite rank scores, and returns sorted leaderboards.
"""

import logging
from typing import List, Dict, Any, Optional

from database.db import get_all_candidates
from ml_models.predict import predict_candidate
from scoring.resume_scorer import calculate_overall_resume_score
from screening.candidate_ranker import calculate_rank_score

logger = logging.getLogger(__name__)


def generate_leaderboard() -> List[Dict[str, Any]]:
    """
    Retrieves all candidate evaluations from the database, computes their
    composite rank score, and returns them sorted by rank score in descending order.
    """
    try:
        candidates = get_all_candidates()
        leaderboard_data = []
        
        for cand in candidates:
            # 1. Fetch prediction confidence from classifier
            # SQLite does not store confidence, so we fetch it dynamically
            try:
                pred_res = predict_candidate(
                    skills_match=cand["resume_score"],
                    experience_years=cand["experience_years"],
                    education_score=cand["education_score"],
                    certifications=cand["certifications"]
                )
                confidence = pred_res["confidence"]
                prediction = pred_res["prediction"]
            except Exception as e:
                logger.warning(f"Failed to fetch ML prediction details for candidate {cand['name']}: {e}")
                confidence = 0.80
                prediction = cand["prediction"]

            # 2. Fetch independent resume score (weighted)
            # Retrieve projects_count from db dict if present, else default to 2
            projects_count = cand.get("projects_count", 2)
            scorer_res = calculate_overall_resume_score(
                skills_match=cand["resume_score"],
                experience_years=cand["experience_years"],
                projects_count=projects_count,
                education_score=cand["education_score"]
            )
            overall_resume_score = scorer_res["overall_score"]
            grade = scorer_res["grade"]
            
            # 3. Calculate composite rank score
            rank_score = calculate_rank_score(
                resume_score=overall_resume_score,
                match_score=cand["resume_score"],
                prediction=prediction,
                confidence=confidence,
                experience_years=cand["experience_years"],
                certifications_count=cand["certifications"]
            )
            
            cand_item = {
                **cand,
                "confidence": confidence,
                "overall_resume_score": overall_resume_score,
                "grade": grade,
                "rank_score": rank_score,
                "projects_count": projects_count
            }
            leaderboard_data.append(cand_item)
            
        # Sort by rank_score descending
        leaderboard_data.sort(key=lambda x: x["rank_score"], reverse=True)
        
        # Assign rank indices
        for idx, item in enumerate(leaderboard_data, 1):
            item["rank"] = idx
            
        return leaderboard_data
        
    except Exception as e:
        logger.error(f"Failed to generate leaderboard: {e}", exc_info=True)
        return []


def search_and_filter_leaderboard(
    query: str = "",
    skills_filter: Optional[List[str]] = None,
    prediction_filter: Optional[List[str]] = None,
    min_score: float = 0.0,
    min_experience: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Applies search queries and filters over the generated leaderboard results.
    """
    leaderboard = generate_leaderboard()
    filtered = []
    
    query = query.strip().lower()
    
    for cand in leaderboard:
        # 1. Text Search Filter (Name, Email, or matched skills)
        if query:
            name_match = query in cand["name"].lower()
            email_match = cand.get("email") and query in cand["email"].lower()
            skills_text = " ".join(cand["matched_skills"]).lower()
            skills_match = query in skills_text
            
            if not (name_match or email_match or skills_match):
                continue
                
        # 2. Skills Multiselect Filter (All selected must be present in matched_skills)
        if skills_filter:
            cand_skills = [s.lower() for s in cand["matched_skills"]]
            skill_hits = all(sf.lower() in cand_skills for sf in skills_filter)
            if not skill_hits:
                continue
                
        # 3. Classifier Prediction Filter
        if prediction_filter:
            if cand["prediction"] not in prediction_filter:
                continue
                
        # 4. Minimum Score Thresholds
        if cand["rank_score"] < min_score:
            continue
            
        # 5. Minimum Experience Threshold
        if cand["experience_years"] < min_experience:
            continue
            
        filtered.append(cand)
        
    # Re-calculate ranks for filtered results
    for idx, item in enumerate(filtered, 1):
        item["filtered_rank"] = idx
        
    return filtered
