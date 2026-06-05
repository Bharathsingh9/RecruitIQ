"""
AI Interview Copilot Router.
Handles question generation and answer evaluation using Groq API and ORM persistence.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.app_config import settings

from app.models.candidate import Candidate
from app.models.evaluation import Evaluation
from app.schemas.evaluation import EvaluationOut, EvaluationResponse

# Import copilot genai logic
from app.genai.interview_question_generator import generate_interview_questions
from app.genai.interview_evaluator import evaluate_answer

logger = logging.getLogger(__name__)
router = APIRouter()


class GenerateQuestionsRequest(BaseModel):
    candidate_id: int
    job_description: Optional[str] = "Software Engineer position with technical skills matching core capabilities."


class EvaluateAnswerRequest(BaseModel):
    candidate_id: int
    question: str
    answer: str


@router.post("/generate-questions", status_code=status.HTTP_200_OK)
def get_copilot_questions(
    payload: GenerateQuestionsRequest,
    db: Session = Depends(deps.get_db)
):
    """
    Generate tailored technical and behavioral questions for a candidate
    based on their matched skills and profile.
    """
    # Fetch candidate
    candidate = db.query(Candidate).filter(
        Candidate.id == payload.candidate_id,
        
    ).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found."
        )

    try:
        candidate_skills = json.loads(candidate.matched_skills) if candidate.matched_skills else []
    except Exception:
        candidate_skills = []

    # Prepare some mock projects for the candidate if none are specified
    projects_list = [f"Project {i+1} using {skill}" for i, skill in enumerate(candidate_skills[:2])]
    if not projects_list:
        projects_list = ["Enterprise application architecture", "Automated data pipeline"]

    questions_res = generate_interview_questions(
        candidate_skills=candidate_skills,
        projects=projects_list,
        job_description=payload.job_description,
        api_key=settings.GROQ_API_KEY
    )

    return questions_res


@router.post("/evaluate", response_model=EvaluationOut, status_code=status.HTTP_201_CREATED)
def evaluate_candidate_answer(
    payload: EvaluateAnswerRequest,
    db: Session = Depends(deps.get_db)
):
    """
    Evaluate a candidate's typed answer using the Groq API model evaluation.
    Persists evaluation metrics (score, depths, strengths, improvements) in database.
    """
    # Check candidate ownership
    candidate = db.query(Candidate).filter(
        Candidate.id == payload.candidate_id,
        
    ).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found."
        )

    # Evaluate answer
    eval_res = evaluate_answer(
        question=payload.question,
        answer=payload.answer,
        api_key=settings.GROQ_API_KEY
    )

    # Persist in DB
    new_eval = Evaluation(
        candidate_id=payload.candidate_id,
        question=payload.question,
        answer=payload.answer,
        score=eval_res["score"],
        technical_depth=eval_res["technical_depth"],
        communication=eval_res["communication"],
        completeness=eval_res["completeness"],
        strengths=json.dumps(eval_res["strengths"]),
        improvements=json.dumps(eval_res["improvements"])
    )

    db.add(new_eval)
    db.commit()
    db.refresh(new_eval)

    # Convert lists before returning
    return EvaluationOut(
        id=new_eval.id,
        candidate_id=new_eval.candidate_id,
        question=new_eval.question,
        answer=new_eval.answer,
        score=new_eval.score,
        technical_depth=new_eval.technical_depth,
        communication=new_eval.communication,
        completeness=new_eval.completeness,
        strengths=eval_res["strengths"],
        improvements=eval_res["improvements"],
        created_at=new_eval.created_at
    )


@router.get("/evaluations/{candidate_id}", response_model=List[EvaluationOut])
def get_candidate_evaluations(
    candidate_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Retrieve all copilot answer evaluation logs recorded for a candidate.
    """
    # Confirm candidate belongs to user
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        
    ).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found."
        )

    evals = db.query(Evaluation).filter(Evaluation.candidate_id == candidate_id).all()
    results = []
    for ev in evals:
        try:
            strengths = json.loads(ev.strengths) if ev.strengths else []
        except Exception:
            strengths = []
        try:
            improvements = json.loads(ev.improvements) if ev.improvements else []
        except Exception:
            improvements = []

        results.append(
            EvaluationOut(
                id=ev.id,
                candidate_id=ev.candidate_id,
                question=ev.question,
                answer=ev.answer,
                score=ev.score,
                technical_depth=ev.technical_depth,
                communication=ev.communication,
                completeness=ev.completeness,
                strengths=strengths,
                improvements=improvements,
                created_at=ev.created_at
            )
        )
    return results
