"""
Explainable AI (XAI) module for HireGen AI.
Uses SHAP (SHapley Additive exPlanations) to explain individual candidate predictions
made by the Random Forest classifier and renders Plotly feature contribution plots.
"""

import os
import joblib
import logging
import numpy as np
import pandas as pd
import shap
import plotly.graph_objects as go
from typing import Dict, Any, List, Tuple

from app.ml_models.feature_engineering import prepare_features

# Configure logger
logger = logging.getLogger(__name__)

# Dynamically resolve model path relative to app folder
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(os.path.dirname(CURRENT_DIR), "ml_models", "candidate_ranker.joblib")


def load_model() -> Any:
    """
    Loads the trained candidate ranker model.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Trained Random Forest model file missing at '{MODEL_PATH}'")
    return joblib.load(MODEL_PATH)


def explain_prediction(
    skills_match: float,
    experience_years: float,
    education_score: float,
    certifications: int,
    predicted_class: str
) -> Dict[str, Any]:
    """
    Calculates SHAP values for a single candidate profile and extracts top positive/negative decision factors.

    Args:
        skills_match (float): Skills match percentage.
        experience_years (float): Candidate years of experience.
        education_score (float): Education match score.
        certifications (int): Certifications count.
        predicted_class (str): Prediction label output (Shortlist/Needs Review/Reject).

    Returns:
        Dict[str, Any]: Explanation dictionary containing:
            - "prediction": Target prediction label.
            - "top_factors": List of human-readable decision factor strings.
            - "shap_values": Dictionary mapping feature name to contribution score.
    """
    logger.info(f"Generating SHAP explanation for candidate prediction: {predicted_class}...")
    
    try:
        model = load_model()
        
        # 1. Prepare candidate single-row features dataframe
        features_df = prepare_features(skills_match, experience_years, education_score, certifications)
        
        # 2. Initialize TreeExplainer
        explainer = shap.TreeExplainer(model)
        raw_shap = explainer.shap_values(features_df)
        
        # Determine class index corresponding to the predicted class label
        classes = list(model.classes_)
        if predicted_class not in classes:
            logger.warning(f"Predicted class '{predicted_class}' not found in model classes: {classes}. Defaulting to first class.")
            class_idx = 0
        else:
            class_idx = classes.index(predicted_class)

        # 3. Parse and standardize SHAP values across API versions
        # Standard format should be a 1D array corresponding to feature contributions
        if isinstance(raw_shap, list):
            # Typical for older SHAP outputs representing list of classes 2D arrays
            feature_contributions = raw_shap[class_idx][0]
        elif isinstance(raw_shap, np.ndarray):
            if raw_shap.ndim == 3:
                # New standard shape: (num_samples, num_features, num_classes)
                feature_contributions = raw_shap[0, :, class_idx]
            elif raw_shap.ndim == 2:
                # Handle binary or single output models (num_samples, num_features)
                feature_contributions = raw_shap[0]
            else:
                feature_contributions = raw_shap.flatten()
        else:
            # Handles SHAP Explanation objects (newer API surfaces)
            values = getattr(raw_shap, "values", None)
            if values is not None:
                if values.ndim == 3:
                    feature_contributions = values[0, :, class_idx]
                else:
                    feature_contributions = values[0]
            else:
                logger.warning("Could not extract values from SHAP structure. Defaulting to zero contributions.")
                feature_contributions = np.zeros(features_df.shape[1])

        # Map features to contributions
        feature_names = list(features_df.columns)
        contributions_dict = {}
        for name, val in zip(feature_names, feature_contributions):
            contributions_dict[name] = float(val)

        logger.info(f"SHAP contributions computed: {contributions_dict}")

        # 4. Generate Human-Readable Factors (Stage 4)
        factors = []
        
        # Heuristic labels depending on direction of feature weight contribution
        # Positive values represent pull towards predicted class; negative represents pull away.
        # We customize factors text based on predicted class for contextual accuracy.
        feature_mappings = {
            "skills_match": {
                "name": "Skills Match",
                "pos": f"High skill match score ({skills_match}%)",
                "neg": f"Low skill match score ({skills_match}%)"
            },
            "experience_years": {
                "name": "Experience",
                "pos": f"Strong experience level ({experience_years} years)",
                "neg": f"Less relative experience ({experience_years} years)"
            },
            "education_score": {
                "name": "Education Score",
                "pos": f"Good education score ({education_score}%)",
                "neg": f"Lower education score ({education_score}%)"
            },
            "certifications": {
                "name": "Certifications",
                "pos": f"Relevant certifications count ({certifications})",
                "neg": f"Fewer active certifications ({certifications})"
            }
        }

        # Sort features by absolute contribution size to list most important factors first
        sorted_features = sorted(contributions_dict.items(), key=lambda item: abs(item[1]), reverse=True)
        
        for name, val in sorted_features:
            mapping = feature_mappings[name]
            # If contribution is positive, candidate attribute supported the prediction
            if val >= 0:
                factors.append(f"✓ {mapping['pos']}")
            else:
                factors.append(f"✗ {mapping['neg']}")

        return {
            "prediction": predicted_class,
            "top_factors": factors,
            "shap_values": contributions_dict
        }

    except Exception as e:
        logger.error(f"Failed to explain candidate prediction: {e}", exc_info=True)
        # Graceful fallback explanation
        return {
            "prediction": predicted_class,
            "top_factors": [
                f"Skills match profile: {skills_match}%",
                f"Candidate experience: {experience_years} years",
                f"Education score: {education_score}%",
                f"Active Certifications: {certifications}"
            ],
            "shap_values": {
                "skills_match": 0.0,
                "experience_years": 0.0,
                "education_score": 0.0,
                "certifications": 0.0
            }
        }


def plot_shap_explanation(shap_values: Dict[str, float]) -> go.Figure:
    """
    Renders an interactive Plotly horizontal bar chart showing individual feature contributions.
    """
    feature_display_names = {
        "skills_match": "Skills Match Score",
        "experience_years": "Years of Experience",
        "education_score": "Education Score",
        "certifications": "Certifications Count"
    }
    
    y_labels = []
    x_values = []
    colors = []
    
    # Sort features for visualization
    for feature, val in sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=False):
        y_labels.append(feature_display_names.get(feature, feature))
        x_values.append(val)
        colors.append("#4CAF50" if val >= 0 else "#F44336")  # Green for positive contribution, Red for negative
        
    fig = go.Figure(go.Bar(
        x=x_values,
        y=y_labels,
        orientation="h",
        marker_color=colors,
        text=[f"{val:+.3f}" for val in x_values],
        textposition="outside"
    ))
    
    fig.update_layout(
        title="Feature Contributions (SHAP Values)",
        xaxis_title="Contribution Direction & Score",
        yaxis_title="Profile Metric",
        template="plotly_dark",
        margin=dict(t=50, b=20, l=20, r=20),
        height=250
    )
    return fig


# Optional: Standalone XAI module test block
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test candidate
    test_candidate = {
        "skills_match": 90.0,
        "experience_years": 4.0,
        "education_score": 85.0,
        "certifications": 3,
        "predicted_class": "Shortlist"
    }
    
    res = explain_prediction(**test_candidate)
    print("\n--- Standalone XAI Explanation Results ---")
    print(f"Prediction: {res['prediction']}")
    print("Decision Factors:")
    for f in res["top_factors"]:
        print(f" {f}")
    print(f"SHAP Values: {res['shap_values']}")
    print("------------------------------------------\n")
