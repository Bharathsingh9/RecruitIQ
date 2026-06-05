"""
Pydantic schemas validation for Candidate screening models.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class CandidateBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    resume_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    experience_years: float
    education_score: float
    certifications: int
    prediction: str
    projects_count: int = 2


class CandidateCreate(CandidateBase):
    pass


class CandidateOut(CandidateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
