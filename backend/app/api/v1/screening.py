"""
Screening API Router for single candidate resume evaluation.
"""

import os
import json
import tempfile
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.api import deps
from app.app_config import settings

from app.models.candidate import Candidate

# Import logic modules from backend package structure
from app.resume_parser.parser import extract_text_from_pdf
from app.resume_parser.extractor import extract_name, extract_email, extract_phone
from app.resume_parser.skills import extract_skills
from app.matching.jd_matcher import calculate_match_score
from app.scoring.resume_scorer import calculate_overall_resume_score
from app.ml_models.predict import predict_candidate
from app.explainability.shap_explainer import explain_prediction
from app.genai.interview_question_generator import generate_interview_questions

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", status_code=status.HTTP_201_CREATED)
async def analyze_candidate_resume(
    file: UploadFile = File(...),
    jd_text: str = Form(...),
    experience_years: float = Form(4.0),
    education_score: float = Form(85.0),
    certifications: int = Form(3),
    projects: str = Form(""),
    db: Session = Depends(deps.get_db)
):
    """
    Uploads a resume PDF, extracts texts/skills, matches parameters, runs classifier prediction,
    calculates SHAP decision values, generates interview questions, and saves to database.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF file uploads are supported."
        )

    temp_path = None
    try:
        # Save uploaded file to temp path
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name

        # 1. Parse text from PDF
        resume_text = extract_text_from_pdf(temp_path)
        if not resume_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from the uploaded PDF resume."
            )

        # 2. Extract profile details
        name = extract_name(resume_text)
        email = extract_email(resume_text)
        phone = extract_phone(resume_text)
        resume_skills = extract_skills(resume_text)
        
        # JD skills
        jd_skills = extract_skills(jd_text)

        # 3. Match skills
        match_results = calculate_match_score(resume_skills, jd_skills)
        match_score = match_results["match_score"]
        matched_skills = match_results["matched_skills"]
        missing_skills = match_results["missing_skills"]

        # 4. Independent Resume Scorer
        projects_list = [p.strip() for p in projects.split("\n") if p.strip()]
        scorer_res = calculate_overall_resume_score(
            skills_match=match_score,
            experience_years=experience_years,
            projects_count=len(projects_list),
            education_score=education_score
        )
        overall_score = scorer_res["overall_score"]
        grade = scorer_res["grade"]

        # 5. Classifier prediction
        pred_res = predict_candidate(
            skills_match=match_score,
            experience_years=experience_years,
            education_score=education_score,
            certifications=certifications
        )
        prediction = pred_res["prediction"]
        confidence = pred_res["confidence"]

        # 6. SHAP Explainable AI decision explanations
        xai_res = explain_prediction(
            skills_match=match_score,
            experience_years=experience_years,
            education_score=education_score,
            certifications=certifications,
            predicted_class=prediction
        )

        # 7. Generate screening interview questions using Groq
        questions = generate_interview_questions(
            candidate_skills=matched_skills if matched_skills else resume_skills,
            projects=projects_list,
            job_description=jd_text,
            api_key=settings.GROQ_API_KEY
        )

        # 8. Save candidate profile to database using SQLAlchemy ORM
        candidate_name = name
        if not candidate_name or candidate_name == "Not Found" or candidate_name.strip() == "":
            candidate_name = os.path.splitext(file.filename)[0].replace("_", " ").title()

        new_cand = Candidate(
            
            name=candidate_name,
            email=email if email != "Not Found" else None,
            phone=phone if phone != "Not Found" else None,
            resume_score=match_score,
            matched_skills=json.dumps(matched_skills),
            missing_skills=json.dumps(missing_skills),
            experience_years=experience_years,
            education_score=education_score,
            certifications=certifications,
            prediction=prediction,
            projects_count=len(projects_list)
        )
        db.add(new_cand)
        db.commit()
        db.refresh(new_cand)

        return {
            "candidate_id": new_cand.id,
            "name": new_cand.name,
            "email": new_cand.email,
            "phone": new_cand.phone,
            "match_score": match_score,
            "resume_score": overall_score,
            "grade": grade,
            "prediction": prediction,
            "confidence": confidence,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "xai_factors": xai_res["top_factors"],
            "shap_values": xai_res["shap_values"],
            "questions": questions
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during candidate screening: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Candidate analysis failed: {str(e)}"
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
