"""
Training script for Candidate Ranking model.
Generates a sample training dataset, fits a Random Forest Classifier,
evaluates validation performance metrics, and serializes the model weights.
"""

import os
import logging
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_CSV_PATH = "ml_models/data.csv"
MODEL_PATH = "ml_models/candidate_ranker.joblib"


def generate_sample_dataset(output_path: str) -> None:
    """
    Generates a realistic sample dataset for training and saves it to a CSV file.
    Creates structured profiles for Shortlist, Needs Review, and Reject candidates.
    """
    logger.info(f"Generating synthetic training dataset at {output_path}...")
    np.random.seed(42)
    
    samples = []
    
    # 1. Shortlist Candidates (high skills, experience, education, certifications)
    for _ in range(60):
        skills = np.random.uniform(75, 100)
        exp = np.random.uniform(3, 10)
        edu = np.random.uniform(75, 100)
        certs = int(np.random.choice([1, 2, 3, 4, 5], p=[0.2, 0.3, 0.2, 0.2, 0.1]))
        samples.append([skills, exp, edu, certs, "Shortlist"])
        
    # 2. Needs Review Candidates (mid-range skills, experience, education)
    for _ in range(50):
        skills = np.random.uniform(50, 75)
        exp = np.random.uniform(1.5, 4.0)
        edu = np.random.uniform(50, 80)
        certs = int(np.random.choice([0, 1, 2], p=[0.4, 0.4, 0.2]))
        samples.append([skills, exp, edu, certs, "Needs Review"])
        
    # 3. Reject Candidates (low skills, low experience, low certs)
    for _ in range(50):
        skills = np.random.uniform(0, 50)
        exp = np.random.uniform(0, 1.5)
        edu = np.random.uniform(20, 60)
        certs = int(np.random.choice([0, 1], p=[0.8, 0.2]))
        samples.append([skills, exp, edu, certs, "Reject"])

    df = pd.DataFrame(samples, columns=["skills_match", "experience_years", "education_score", "certifications", "label"])
    
    # Save directory safety
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Generated {len(df)} rows of training data.")


def train_model() -> None:
    """
    Loads training dataset, splits into train/test splits,
    fits a Random Forest model, prints evaluation scores, and saves to file.
    """
    # 1. Generate dataset if not present
    if not os.path.exists(DATA_CSV_PATH):
        generate_sample_dataset(DATA_CSV_PATH)
        
    # 2. Load dataset
    logger.info(f"Loading dataset from '{DATA_CSV_PATH}'...")
    df = pd.read_csv(DATA_CSV_PATH)
    
    X = df[["skills_match", "experience_years", "education_score", "certifications"]]
    y = df["label"]
    
    # 3. Split into Train & Validation sets (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    logger.info(f"Data split. Train shape: {X_train.shape}, Test shape: {X_test.shape}")
    
    # 4. Train Random Forest Classifier
    logger.info("Initializing and training Random Forest Classifier...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=6)
    clf.fit(X_train, y_train)
    logger.info("Model training complete.")
    
    # 5. Predict and Evaluate
    predictions = clf.predict(X_test)
    
    # Calculate performance metrics
    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, average="weighted")
    recall = recall_score(y_test, predictions, average="weighted")
    f1 = f1_score(y_test, predictions, average="weighted")
    
    print("\n" + "=" * 50)
    print("MODEL PERFORMANCE EVALUATION METRICS")
    print("=" * 50)
    print(f"Accuracy  : {accuracy * 100.0:.2f}%")
    print(f"Precision : {precision * 100.0:.2f}%")
    print(f"Recall    : {recall * 100.0:.2f}%")
    print(f"F1 Score  : {f1 * 100.0:.2f}%")
    print("=" * 50 + "\n")
    
    # 6. Save model using joblib
    logger.info(f"Saving trained model file to '{MODEL_PATH}'...")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    logger.info("Model saved successfully.")


if __name__ == "__main__":
    train_model()
