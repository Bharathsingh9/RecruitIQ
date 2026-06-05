"""
SQLAlchemy Evaluation model mapping candidate answer evaluation records in database.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.session import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    technical_depth = Column(Integer, nullable=False)
    communication = Column(Integer, nullable=False)
    completeness = Column(Integer, nullable=False)
    strengths = Column(Text, nullable=False)     # Serialized JSON array of strings
    improvements = Column(Text, nullable=False)   # Serialized JSON array of strings
    created_at = Column(DateTime, default=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="evaluations")
