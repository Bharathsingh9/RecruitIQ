import os
import sys
import json
import random

# Add parent dir to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.session import SessionLocal
from app.models.candidate import Candidate
from app.models.evaluation import Evaluation

NAMES = ["John Doe", "Alice Johnson", "Rahul Sharma", "Priya Patel", "Michael Brown", 
         "Sophia Williams", "David Chen", "Emma Wilson", "James Taylor", "Linda Martinez",
         "Robert Garcia", "Maria Rodriguez", "William Smith", "Jessica Anderson", "Daniel Thomas",
         "Sarah Jackson", "Thomas White", "Karen Harris", "Matthew Martin", "Nancy Thompson",
         "Charles Garcia", "Lisa Martinez", "Joseph Robinson", "Betty Clark", "Richard Lewis",
         "Margaret Lee", "Christopher Walker", "Sandra Hall", "Daniel Allen", "Ashley Young"]

SKILLS_POOL = ["Python", "React", "Node.js", "SQL", "AWS", "Docker", "Kubernetes", "TypeScript",
               "GraphQL", "MongoDB", "PostgreSQL", "Machine Learning", "Data Analysis", "Java", "C++"]

def generate_random_candidate():
    name = random.choice(NAMES)
    score = random.uniform(40.0, 99.0)
    
    if score >= 85:
        pred = "Shortlist"
    elif score >= 65:
        pred = "Needs Review"
    else:
        pred = "Reject"
        
    num_matched = random.randint(3, 8)
    num_missing = random.randint(0, 4)
    
    matched = random.sample(SKILLS_POOL, num_matched)
    remaining_skills = [s for s in SKILLS_POOL if s not in matched]
    missing = random.sample(remaining_skills, min(num_missing, len(remaining_skills)))
    
    exp = round(random.uniform(1.0, 15.0), 1)
    edu = random.uniform(60.0, 100.0)
    certs = random.randint(0, 5)
    
    return Candidate(
        name=name,
        email=f"{name.lower().replace(' ', '.')}@example.com",
        phone=f"+1 {random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
        resume_score=round(score, 1),
        matched_skills=json.dumps(matched),
        missing_skills=json.dumps(missing),
        experience_years=exp,
        education_score=round(edu, 1),
        certifications=certs,
        prediction=pred,
        projects_count=random.randint(1, 10)
    )

def seed_db():
    db = SessionLocal()
    try:

            
        print("Clearing existing candidates...")
        db.query(Candidate).delete()
        db.commit()
        
        print("Seeding 30 new realistic candidates...")
        candidates = []
        for _ in range(30):
            cand = generate_random_candidate()
            candidates.append(cand)
            
        db.add_all(candidates)
        db.commit()
        print("Done!")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
