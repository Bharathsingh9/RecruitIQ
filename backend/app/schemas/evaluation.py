"""
Pydantic schemas validation for Candidate Interview Evaluations.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class EvaluationBase(BaseModel):
    question: str
    answer: str


class EvaluationCreate(EvaluationBase):
    candidate_id: int


class EvaluationResponse(BaseModel):
    score: float
    technical_depth: int
    communication: int
    completeness: int
    strengths: List[str]
    improvements: List[str]


class EvaluationOut(EvaluationBase):
    id: int
    candidate_id: int
    score: float
    technical_depth: int
    communication: int
    completeness: int
    strengths: List[str]
    improvements: List[str]
    created_at: datetime

    class Config:
        from_attributes = True
