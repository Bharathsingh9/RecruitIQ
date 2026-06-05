"""
Reports Generation and Download API Router.
Compiles and streams individual candidate PDF dossier and campaign-wide Excel logs.
"""

import os
import json
import logging
import tempfile
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.app_config import settings

from app.models.candidate import Candidate

# Import analytical and generation helpers
from app.reports.pdf_report import generate_candidate_pdf
from app.reports.excel_report import generate_excel_report
from app.ml_models.predict import predict_candidate
from app.scoring.resume_scorer import calculate_overall_resume_score
from app.explainability.shap_explainer import explain_prediction
from app.matching.skill_gap_analyzer import generate_learning_path
from app.genai.interview_question_generator import generate_interview_questions
from app.screening.candidate_ranker import calculate_rank_score

logger = logging.getLogger(__name__)
router = APIRouter()


def remove_temp_file(filepath: str):
    """
    Callback utility to delete generated temp file on request completion.
    """
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            logger.info(f"Successfully cleaned up temporary report file: '{filepath}'")
        except Exception as err:
            logger.error(f"Failed to delete temporary file '{filepath}': {err}")


@router.get("/pdf/candidate/{candidate_id}", status_code=status.HTTP_200_OK)
def export_candidate_pdf_report(
    candidate_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """
    Fetch candidate details, compute scores on-the-fly, and generate a printable PDF dossier.
    """
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        
    ).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate evaluation record not found."
        )

    # 1. Parse JSON arrays
    try:
        matched_skills = json.loads(candidate.matched_skills) if candidate.matched_skills else []
        missing_skills = json.loads(candidate.missing_skills) if candidate.missing_skills else []
    except Exception:
        matched_skills = []
        missing_skills = []

    # 2. Re-compute ML and grading values for the PDF layout
    try:
        pred_res = predict_candidate(
            skills_match=candidate.resume_score,
            experience_years=candidate.experience_years,
            education_score=candidate.education_score,
            certifications=candidate.certifications
        )
        confidence = pred_res["confidence"]
        prediction = pred_res["prediction"]
    except Exception:
        confidence = 0.80
        prediction = candidate.prediction

    scorer_res = calculate_overall_resume_score(
        skills_match=candidate.resume_score,
        experience_years=candidate.experience_years,
        projects_count=candidate.projects_count,
        education_score=candidate.education_score
    )
    overall_resume_score = scorer_res["overall_score"]
    grade = scorer_res["grade"]

    # Explain prediction
    try:
        xai_res = explain_prediction(
            skills_match=candidate.resume_score,
            experience_years=candidate.experience_years,
            education_score=candidate.education_score,
            certifications=candidate.certifications,
            predicted_class=prediction
        )
        xai_factors = xai_res["top_factors"]
    except Exception:
        xai_factors = ["Candidate holds matching required skills profile."]

    # Skill recommendations
    gap_res = generate_learning_path(missing_skills)
    learning_path = gap_res["learning_path"]

    # Interview questions
    skills_for_qs = matched_skills if matched_skills else (matched_skills + missing_skills)
    mock_projects = ["Key Technical Implementation Project"]
    try:
        questions = generate_interview_questions(
            candidate_skills=skills_for_qs,
            projects=mock_projects,
            job_description=f"Candidate evaluated on match criteria.",
            api_key=settings.GROQ_API_KEY
        )
    except Exception:
        questions = {"technical_questions": [], "behavioral_questions": []}

    # Prepare report dict
    candidate_data = {
        "name": candidate.name,
        "email": candidate.email or "Not Provided",
        "phone": candidate.phone or "Not Provided",
        "prediction": prediction,
        "confidence": confidence,
        "overall_resume_score": overall_resume_score,
        "resume_score": candidate.resume_score,
        "grade": grade,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "xai_factors": xai_factors,
        "learning_path": learning_path,
        "questions": questions
    }

    # Generate PDF in a temp location
    fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    try:
        generate_candidate_pdf(candidate_data, temp_path)
        background_tasks.add_task(remove_temp_file, temp_path)
        
        filename = f"Evaluation_Report_{candidate.name.replace(' ', '_')}.pdf"
        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type="application/pdf"
        )
    except Exception as pdf_err:
        logger.error(f"Error compiling candidate PDF report: {pdf_err}", exc_info=True)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF report: {str(pdf_err)}"
        )


@router.get("/excel/campaign", status_code=status.HTTP_200_OK)
def export_campaign_excel_sheet(
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """
    Compile all candidate profiles, computed ranks, and KPIs into a multi-sheet spreadsheet.
    """
    candidates = db.query(Candidate).all()
    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No candidate evaluations found to export."
        )

    # 1. Format raw candidates list
    raw_list = []
    for cand in candidates:
        raw_list.append({
            "id": cand.id,
            "name": cand.name,
            "email": cand.email or "N/A",
            "phone": cand.phone or "N/A",
            "resume_score": cand.resume_score,
            "experience_years": cand.experience_years,
            "education_score": cand.education_score,
            "certifications": cand.certifications,
            "projects_count": cand.projects_count,
            "prediction": cand.prediction,
            "created_at": cand.created_at.strftime("%Y-%m-%d %H:%M") if cand.created_at else "N/A"
        })

    # 2. Compile leaderboard list (sortable)
    leaderboard_list = []
    for cand in candidates:
        try:
            pred_res = predict_candidate(
                skills_match=cand.resume_score,
                experience_years=cand.experience_years,
                education_score=cand.education_score,
                certifications=cand.certifications
            )
            confidence = pred_res["confidence"]
        except Exception:
            confidence = 0.80

        scorer_res = calculate_overall_resume_score(
            skills_match=cand.resume_score,
            experience_years=cand.experience_years,
            projects_count=cand.projects_count,
            education_score=cand.education_score
        )
        overall_resume_score = scorer_res["overall_score"]
        grade = scorer_res["grade"]

        rank_score = calculate_rank_score(
            resume_score=overall_resume_score,
            match_score=cand.resume_score,
            prediction=cand.prediction,
            confidence=confidence,
            experience_years=cand.experience_years,
            certifications_count=cand.certifications
        )

        leaderboard_list.append({
            "name": cand.name,
            "overall_resume_score": overall_resume_score,
            "resume_score": cand.resume_score,
            "grade": grade,
            "prediction": cand.prediction,
            "confidence": confidence,
            "experience_years": cand.experience_years,
            "rank_score": rank_score
        })

    # Sort leaderboard by rank score
    leaderboard_list.sort(key=lambda x: x["rank_score"], reverse=True)

    # 3. Calculate metrics KPIs
    total = len(candidates)
    shortlisted = sum(1 for c in candidates if c.prediction == "Shortlist")
    needs_review = sum(1 for c in candidates if c.prediction == "Needs Review")
    rejected = sum(1 for c in candidates if c.prediction == "Reject")
    average_match_score = round(sum(c.resume_score for c in candidates) / total, 1)

    analytics_summary = {
        "total_candidates": total,
        "shortlisted": shortlisted,
        "needs_review": needs_review,
        "rejected": rejected,
        "average_match_score": average_match_score
    }

    # Generate Excel in a temp location
    fd, temp_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)

    try:
        generate_excel_report(raw_list, leaderboard_list, analytics_summary, temp_path)
        background_tasks.add_task(remove_temp_file, temp_path)

        return FileResponse(
            path=temp_path,
            filename="Campaign_Recruiter_Report.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as excel_err:
        logger.error(f"Error compiling campaign Excel report: {excel_err}", exc_info=True)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Excel report: {str(excel_err)}"
        )
