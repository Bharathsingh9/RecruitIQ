"""
Recruiter Analytics API Router.
Calculates system KPIs, skill distributions, score distributions, and chart coordinates.
"""

import json
import logging
from collections import Counter
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps

from app.models.candidate import Candidate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/kpis", status_code=status.HTTP_200_OK)
def get_recruiter_analytics_kpis(
    db: Session = Depends(deps.get_db)
):
    """
    Computes summary KPIs and distribution arrays for React charts.
    """
    try:
        # Get candidates screened by current user
        candidates = db.query(Candidate).all()
        total_candidates = len(candidates)

        if total_candidates == 0:
            return {
                "kpis": {
                    "total": 0,
                    "shortlisted": 0,
                    "needs_review": 0,
                    "rejected": 0,
                    "average_score": 0.0
                },
                "prediction_distribution": [],
                "top_skills": [],
                "top_missing_skills": [],
                "score_distribution": [],
                "experience_vs_score": []
            }

        # Calculate KPIs
        shortlisted = sum(1 for c in candidates if c.prediction == "Shortlist")
        needs_review = sum(1 for c in candidates if c.prediction == "Needs Review")
        rejected = sum(1 for c in candidates if c.prediction == "Reject")
        average_score = round(sum(c.resume_score for c in candidates) / total_candidates, 2)

        # 1. Prediction distribution
        pred_dist = [
            {"name": "Shortlist", "value": shortlisted},
            {"name": "Needs Review", "value": needs_review},
            {"name": "Reject", "value": rejected}
        ]

        # 2. Extract skills frequency
        matched_skills_counter = Counter()
        missing_skills_counter = Counter()

        for cand in candidates:
            try:
                matched = json.loads(cand.matched_skills) if cand.matched_skills else []
                for m in matched:
                    if m.strip():
                        matched_skills_counter[m.strip().title()] += 1
            except Exception:
                pass

            try:
                missing = json.loads(cand.missing_skills) if cand.missing_skills else []
                for ms in missing:
                    if ms.strip():
                        missing_skills_counter[ms.strip().title()] += 1
            except Exception:
                pass

        top_skills = [{"skill": k, "count": v} for k, v in matched_skills_counter.most_common(10)]
        top_missing_skills = [{"skill": k, "count": v} for k, v in missing_skills_counter.most_common(10)]

        # 3. Score distribution buckets (0-20, 21-40, 41-60, 61-80, 81-100)
        buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
        for cand in candidates:
            score = cand.resume_score
            if score <= 20:
                buckets["0-20"] += 1
            elif score <= 40:
                buckets["21-40"] += 1
            elif score <= 60:
                buckets["41-60"] += 1
            elif score <= 80:
                buckets["61-80"] += 1
            else:
                buckets["81-100"] += 1

        score_dist = [{"range": k, "count": v} for k, v in buckets.items()]

        # 4. Experience vs Score scatter coordinates
        exp_vs_score = []
        for cand in candidates:
            exp_vs_score.append({
                "name": cand.name,
                "experience": cand.experience_years,
                "score": cand.resume_score,
                "prediction": cand.prediction
            })

        return {
            "kpis": {
                "total": total_candidates,
                "shortlisted": shortlisted,
                "needs_review": needs_review,
                "rejected": rejected,
                "average_score": average_score
            },
            "prediction_distribution": pred_dist,
            "top_skills": top_skills,
            "top_missing_skills": top_missing_skills,
            "score_distribution": score_dist,
            "experience_vs_score": exp_vs_score
        }

    except Exception as e:
        logger.error(f"Error calculating analytics KPIs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load analytics: {str(e)}"
        )
