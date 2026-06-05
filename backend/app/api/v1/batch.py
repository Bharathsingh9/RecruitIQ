"""
Batch Upload and Candidate Leaderboard API Router.
Supports parallel parsing, classification, database storage, and filtering of candidates.
"""

import os
import uuid
import json
import tempfile
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.api import deps
from app.app_config import settings

from app.models.candidate import Candidate
from app.database.session import SessionLocal

# Import parsing, scoring, ranking, and explanation modules
from app.resume_parser.parser import extract_text_from_pdf
from app.resume_parser.extractor import extract_name, extract_email, extract_phone
from app.resume_parser.skills import extract_skills
from app.matching.jd_matcher import calculate_match_score
from app.scoring.resume_scorer import calculate_overall_resume_score
from app.ml_models.predict import predict_candidate
from app.explainability.shap_explainer import explain_prediction
from app.genai.interview_question_generator import generate_interview_questions
from app.screening.candidate_ranker import calculate_rank_score

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory dictionary to track async batch tasks
# format: { task_id: { "status": "processing"|"completed"|"failed", "processed": int, "total": int, "errors": list, "results": list } }
BATCH_TASKS: Dict[str, Dict[str, Any]] = {}


def run_batch_screening(
    task_id: str,
    user_id: int,
    file_contents: List[tuple],  # List of tuples: (filename, bytes_content)
    jd_text: str,
    experience_years: float,
    education_score: float,
    certifications: int,
    projects_list: List[str]
):
    """
    Background worker function that processes multiple resume files, computes scores,
    and inserts records into the database.
    """
    db: Session = SessionLocal()
    BATCH_TASKS[task_id]["status"] = "processing"
    
    try:
        for filename, content in file_contents:
            temp_path = None
            try:
                # 1. Create a temp file to hold the PDF bytes
                suffix = os.path.splitext(filename)[1] or ".pdf"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(content)
                    temp_path = tmp.name

                # 2. Parse text
                resume_text = extract_text_from_pdf(temp_path)
                if not resume_text:
                    raise ValueError("Empty or unparsable resume text")

                # 3. Extract profile details
                name = extract_name(resume_text)
                email = extract_email(resume_text)
                phone = extract_phone(resume_text)
                resume_skills = extract_skills(resume_text)
                
                # JD skills
                jd_skills = extract_skills(jd_text)

                # 4. Match skills
                match_results = calculate_match_score(resume_skills, jd_skills)
                match_score = match_results["match_score"]
                matched_skills = match_results["matched_skills"]
                missing_skills = match_results["missing_skills"]

                # 5. ML Classifier prediction
                pred_res = predict_candidate(
                    skills_match=match_score,
                    experience_years=experience_years,
                    education_score=education_score,
                    certifications=certifications
                )
                prediction = pred_res["prediction"]

                # 6. Save candidate profile to database using SQLAlchemy ORM
                candidate_name = name
                if not candidate_name or candidate_name == "Not Found" or candidate_name.strip() == "":
                    candidate_name = os.path.splitext(filename)[0].replace("_", " ").title()

                new_cand = Candidate(
                    user_id=user_id,
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

                BATCH_TASKS[task_id]["results"].append({
                    "id": new_cand.id,
                    "name": new_cand.name,
                    "prediction": prediction,
                    "score": match_score
                })

            except Exception as item_err:
                logger.error(f"Failed to process file {filename} in batch: {item_err}", exc_info=True)
                BATCH_TASKS[task_id]["errors"].append({
                    "filename": filename,
                    "error": str(item_err)
                })
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                
                # Update progress count
                BATCH_TASKS[task_id]["processed"] += 1
                
        BATCH_TASKS[task_id]["status"] = "completed"
        logger.info(f"Batch task {task_id} finished successfully.")

    except Exception as batch_err:
        logger.error(f"Fatal batch task error for {task_id}: {batch_err}", exc_info=True)
        BATCH_TASKS[task_id]["status"] = "failed"
    finally:
        db.close()


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_batch_resumes(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    jd_text: str = Form(...),
    experience_years: float = Form(3.0),
    education_score: float = Form(80.0),
    certifications: int = Form(1),
    projects: str = Form("")
):
    """
    Accepts a list of files to screen, schedules parallel processing,
    and returns a task ID to query progress status.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files uploaded."
        )

    # Validate that all files are PDFs
    for f in files:
        if not f.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only PDF uploads are supported. File '{f.filename}' is invalid."
            )

    # Read all files to bytes immediately so we can pass them to the thread worker
    file_contents = []
    for f in files:
        bytes_data = await f.read()
        file_contents.append((f.filename, bytes_data))

    task_id = str(uuid.uuid4())
    BATCH_TASKS[task_id] = {
        "status": "queued",
        "processed": 0,
        "total": len(files),
        "errors": [],
        "results": []
    }

    projects_list = [p.strip() for p in projects.split("\n") if p.strip()]

    background_tasks.add_task(
        run_batch_screening,
        task_id=task_id,
        
        file_contents=file_contents,
        jd_text=jd_text,
        experience_years=experience_years,
        education_score=education_score,
        certifications=certifications,
        projects_list=projects_list
    )

    return {
        "task_id": task_id,
        "status": "queued",
        "total_files": len(files)
    }


@router.get("/status/{task_id}")
def get_batch_status(task_id: str):
    """
    Check the current processing status of an uploaded batch.
    """
    if task_id not in BATCH_TASKS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch task not found."
        )
    return BATCH_TASKS[task_id]


@router.get("/leaderboard")
def get_candidates_leaderboard(
    search: str = "",
    prediction: Optional[str] = None,
    min_score: float = 0.0,
    min_experience: float = 0.0,
    db: Session = Depends(deps.get_db)
):
    """
    Fetch, score, and rank candidates for the active user session.
    Supports query parameters to filter names, predictions, and threshold scores.
    """
    query = db.query(Candidate)
    
    # 1. Apply static DB filters
    if prediction:
        # prediction can be comma separated list, e.g. "Shortlist,Needs Review"
        pred_classes = [p.strip() for p in prediction.split(",") if p.strip()]
        if pred_classes:
            query = query.filter(Candidate.prediction.in_(pred_classes))
            
    if min_experience > 0:
        query = query.filter(Candidate.experience_years >= min_experience)

    candidates = query.all()
    leaderboard_data = []

    for cand in candidates:
        # Deserialize JSON arrays
        try:
            matched_skills = json.loads(cand.matched_skills) if cand.matched_skills else []
        except Exception:
            matched_skills = []
            
        try:
            missing_skills = json.loads(cand.missing_skills) if cand.missing_skills else []
        except Exception:
            missing_skills = []

        # Predict dynamically to get confidence/ml_predictions
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

        # Calculate overall resume score
        scorer_res = calculate_overall_resume_score(
            skills_match=cand.resume_score,
            experience_years=cand.experience_years,
            projects_count=cand.projects_count,
            education_score=cand.education_score
        )
        overall_resume_score = scorer_res["overall_score"]
        grade = scorer_res["grade"]

        # Calculate composite rank score
        rank_score = calculate_rank_score(
            resume_score=overall_resume_score,
            match_score=cand.resume_score,
            prediction=cand.prediction,
            confidence=confidence,
            experience_years=cand.experience_years,
            certifications_count=cand.certifications
        )

        cand_item = {
            "id": cand.id,
            "name": cand.name,
            "email": cand.email,
            "phone": cand.phone,
            "resume_score": cand.resume_score,  # Match score %
            "overall_resume_score": overall_resume_score,
            "grade": grade,
            "experience_years": cand.experience_years,
            "education_score": cand.education_score,
            "certifications": cand.certifications,
            "prediction": cand.prediction,
            "confidence": confidence,
            "rank_score": rank_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "created_at": cand.created_at
        }
        leaderboard_data.append(cand_item)

    # 2. Apply search text filters (Name, Email, Skills)
    if search:
        search_lower = search.strip().lower()
        filtered_data = []
        for c in leaderboard_data:
            name_hit = search_lower in c["name"].lower()
            email_hit = c["email"] and search_lower in c["email"].lower()
            skills_hit = any(search_lower in s.lower() for s in c["matched_skills"])
            if name_hit or email_hit or skills_hit:
                filtered_data.append(c)
        leaderboard_data = filtered_data

    # 3. Apply min composite score filter
    if min_score > 0:
        leaderboard_data = [c for c in leaderboard_data if c["rank_score"] >= min_score]

    # 4. Sort by composite rank score in descending order
    leaderboard_data.sort(key=lambda x: x["rank_score"], reverse=True)

    # 5. Assign rank numbers
    for idx, c in enumerate(leaderboard_data, 1):
        c["rank"] = idx

    return leaderboard_data


@router.get("/candidate/{candidate_id}", status_code=status.HTTP_200_OK)
def get_candidate_details(
    candidate_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Fetch comprehensive candidate assessment details (scoring, predictions, SHAP, learning path, and questions).
    """
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        
    ).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate evaluation record not found."
        )

    try:
        matched_skills = json.loads(candidate.matched_skills) if candidate.matched_skills else []
    except Exception:
        matched_skills = []

    try:
        missing_skills = json.loads(candidate.missing_skills) if candidate.missing_skills else []
    except Exception:
        missing_skills = []

    # Re-calculate Dynamic ML outputs
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

    # Re-run XAI SHAP explanations
    try:
        xai_res = explain_prediction(
            skills_match=candidate.resume_score,
            experience_years=candidate.experience_years,
            education_score=candidate.education_score,
            certifications=candidate.certifications,
            predicted_class=prediction
        )
        xai_factors = xai_res["top_factors"]
        shap_values = xai_res["shap_values"]
    except Exception:
        xai_factors = ["Evaluated candidate attributes match general profile criteria."]
        shap_values = {}

    # Skill courses recommendations
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

    return {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "resume_score": candidate.resume_score,
        "overall_resume_score": overall_resume_score,
        "grade": grade,
        "experience_years": candidate.experience_years,
        "education_score": candidate.education_score,
        "certifications": candidate.certifications,
        "prediction": prediction,
        "confidence": confidence,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "xai_factors": xai_factors,
        "shap_values": shap_values,
        "learning_path": learning_path,
        "questions": questions
    }


@router.delete("/candidate/{candidate_id}", status_code=status.HTTP_200_OK)
def delete_candidate_record(
    candidate_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Deletes a candidate evaluation record from the database.
    """
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        
    ).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate evaluation record not found."
        )

    db.delete(candidate)
    db.commit()
    return {"detail": "Candidate record deleted successfully."}

