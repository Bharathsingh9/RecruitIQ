import os
import sys

# Add parent dir to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.session import SessionLocal
from app.models.candidate import Candidate
from app.models.evaluation import Evaluation

def clear_db():
    db = SessionLocal()
    try:
        print("Clearing existing candidates...")
        db.query(Candidate).delete()
        db.commit()
        print("Done!")
    finally:
        db.close()

if __name__ == "__main__":
    clear_db()
