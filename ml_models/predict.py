"""
Prediction service module for Candidate Ranking model.
Loads the Random Forest model and makes classification predictions with confidence scores.
Includes automatic model-training fallback and heuristic rules as a secondary fallback.
"""

import os
import joblib
import logging
from typing import Dict, Any

from ml_models.feature_engineering import prepare_features

# Configure logger
logger = logging.getLogger(__name__)

MODEL_PATH = "ml_models/candidate_ranker.joblib"


def predict_candidate(
    skills_match: float,
    experience_years: float,
    education_score: float,
    certifications: int
) -> Dict[str, Any]:
    """
    Predicts the classification category (Shortlist, Needs Review, Reject) 
    and returns prediction class and probability confidence score.
    Relies strictly on the trained RandomForest Classifier.

    Args:
        skills_match (float): Score match of core skills (0 to 100).
        experience_years (float): Candidate years of experience.
        education_score (float): Education match score (0 to 100).
        certifications (int): Certifications count.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - "prediction": Classification label string (Shortlist/Needs Review/Reject).
            - "confidence": Float probability score of prediction class.

    Raises:
        FileNotFoundError: If the model weights joblib file is missing and cannot be trained.
        Exception: For errors during prediction calculations.
    """
    # 1. Self-healing model training if file does not exist
    if not os.path.exists(MODEL_PATH):
        logger.info(f"Model file '{MODEL_PATH}' not found. Attempting automatic training...")
        from ml_models.train import train_model
        train_model()

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Trained model file could not be found at {MODEL_PATH}")

    # 2. Load model from joblib file
    clf = joblib.load(MODEL_PATH)
    
    # Prepare features
    features_df = prepare_features(skills_match, experience_years, education_score, certifications)
    
    # Perform prediction
    pred_label = clf.predict(features_df)[0]
    
    # Calculate prediction probability/confidence
    probabilities = clf.predict_proba(features_df)[0]
    # Map class labels to index positions
    classes = clf.classes_
    class_idx = list(classes).index(pred_label)
    confidence = round(float(probabilities[class_idx]), 2)
    
    logger.info(f"Successfully predicted class '{pred_label}' with confidence {confidence}.")
    return {
        "prediction": pred_label,
        "confidence": confidence
    }


# Optional: Example usage block for standalone prediction testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test candidate profiles
    candidate_profiles = [
        {"skills_match": 95, "experience_years": 4, "education_score": 90, "certifications": 3},
        {"skills_match": 60, "experience_years": 2.5, "education_score": 70, "certifications": 1},
        {"skills_match": 35, "experience_years": 0.5, "education_score": 50, "certifications": 0}
    ]
    
    print("\n--- Running Prediction Tests ---")
    for profile in candidate_profiles:
        res = predict_candidate(**profile)
        print(f"Profile: {profile} --> Result: {res}")
    print("--------------------------------\n")
