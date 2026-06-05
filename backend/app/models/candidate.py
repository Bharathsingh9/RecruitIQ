"""
SQLAlchemy Candidate model mapping for candidate evaluations table.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.session import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    resume_score = Column(Float, nullable=False)
    matched_skills = Column(Text, nullable=False)  # Serialized JSON array of strings
    missing_skills = Column(Text, nullable=False)  # Serialized JSON array of strings
    experience_years = Column(Float, nullable=False)
    education_score = Column(Float, nullable=False)
    certifications = Column(Integer, nullable=False)
    prediction = Column(String(50), nullable=False)
    projects_count = Column(Integer, nullable=False, default=2)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    evaluations = relationship("Evaluation", back_populates="candidate", cascade="all, delete-orphan")
