"""
Master database Base registry file.
Imports SQLAlchemy base model and all class models schemas so that Base.metadata has
full database mappings visibility.
"""

from app.database.session import Base
from app.models.user import User
from app.models.candidate import Candidate
from app.models.evaluation import Evaluation
