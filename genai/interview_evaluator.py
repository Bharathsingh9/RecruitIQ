"""
AI Interview Copilot Answer Evaluator module.
Evaluates candidate interview answers against technical questions using Groq Llama 3.1 model
for scores (0-10), strengths, and improvement suggestions. 
Includes a robust offline keyword-based fallback evaluator.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional

# Configure logger
logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"


def generate_fallback_evaluation(question: str, answer: str) -> Dict[str, Any]:
    """
    Computes a realistic mock evaluation using keyword matching heuristics
    when no Groq API Key is configured or the API request fails.
    """
    logger.info("Generating offline fallback interview answer evaluation...")
    
    question_lower = question.lower()
    answer_lower = answer.lower()
    
    # Heuristics: check for keyword indicators
    rf_keywords = ["tree", "forest", "average", "bagging", "parallel"]
    xgb_keywords = ["xgb", "boost", "sequential", "residual", "gradient", "error"]
    generic_keywords = ["model", "class", "data", "algorithm", "learn"]
    
    rf_hits = sum(1 for kw in rf_keywords if kw in answer_lower)
    xgb_hits = sum(1 for kw in xgb_keywords if kw in answer_lower)
    generic_hits = sum(1 for kw in generic_keywords if kw in answer_lower)
    
    total_hits = rf_hits + xgb_hits + generic_hits
    
    # Standard question-specific check (e.g. Random Forest vs XGBoost)
    if "random forest" in question_lower and "xgboost" in question_lower:
        if rf_hits > 0 and xgb_hits > 0:
            # High-quality answer
            score = 8.5
            tech_depth = 8
            communication = 9
            completeness = 8
            strengths = [
                "Correctly defines the bootstrap aggregating (bagging) concepts of Random Forest.",
                "Accurately explains the sequential boosting correction behavior of XGBoost."
            ]
            improvements = [
                "Expand on the bias-variance tradeoff difference between bagging and boosting.",
                "Discuss the computational complexity and parallelization limits of training sequential trees."
            ]
        else:
            # Partial answer
            score = 5.0
            tech_depth = 4
            communication = 6
            completeness = 5
            strengths = ["Identifies the general classification model families."]
            improvements = [
                "Clearly distinguish bagging (Random Forest) from boosting (XGBoost).",
                "Explain how bagging averages predictions while boosting fits residuals sequentially."
            ]
    else:
        # Generic fallback based on keyword counts
        if total_hits >= 5:
            score = 8.0
            tech_depth = 8
            communication = 8
            completeness = 8
            strengths = ["Good usage of technical terms.", "Concepts are described clearly."]
            improvements = ["Explain how you would implement or tune this model in production.", "Discuss potential scaling bottlenecks."]
        elif total_hits >= 2:
            score = 6.0
            tech_depth = 5
            communication = 7
            completeness = 6
            strengths = ["Basic understanding of the core concept."]
            improvements = ["Add more technical depth and elaborate on specific parameters.", "Mention real-world project applications."]
        else:
            score = 4.0
            tech_depth = 3
            communication = 5
            completeness = 4
            strengths = ["Attempted the response."]
            improvements = ["Provide a more detailed explanation of core algorithms.", "Include specific examples or code implementations."]

    return {
        "score": score,
        "technical_depth": tech_depth,
        "communication": communication,
        "completeness": completeness,
        "strengths": strengths,
        "improvements": improvements
    }


def evaluate_answer(
    question: str,
    answer: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates candidate's typed answer to an interview question using Groq API.
    Returns structured scores, strengths, and areas of improvement.

    Args:
        question (str): The technical question asked.
        answer (str): The candidate's typed response.
        api_key (Optional[str]): Groq API Key (falls back to GROQ_API_KEY environment variable).

    Returns:
        Dict[str, Any]: Assessment summary matching target JSON keys.
    """
    # 1. Resolve API Key
    actual_key = api_key or os.environ.get("GROQ_API_KEY")
    
    if not actual_key:
        logger.warning("No Groq API Key found. Returning offline fallback evaluation.")
        return generate_fallback_evaluation(question, answer)

    # 2. Design Prompt Template (Prompt Engineering)
    system_prompt = (
        "You are a Senior Technical Interviewer. "
        "Evaluate the candidate's answer to the technical question.\n\n"
        "Evaluation Criteria:\n"
        "1. Technical Accuracy: Are core engineering concepts explained correctly?\n"
        "2. Completeness: Does the answer address all parts of the question?\n"
        "3. Communication Clarity: Is the phrasing logical, clear, and professional?\n"
        "4. Depth of Knowledge: Does the candidate show advanced understanding of the topic?\n"
        "5. Real-World Understanding: Does the candidate explain practical tradeoffs or use cases?\n\n"
        "You MUST return a valid JSON object matching the schema below. Do not wrap in markdown or write conversational texts.\n\n"
        "REQUIRED JSON FORMAT:\n"
        "{\n"
        '  "score": 0.0 to 10.0 (float),\n'
        '  "technical_depth": 0 to 10 (integer),\n'
        '  "communication": 0 to 10 (integer),\n'
        '  "completeness": 0 to 10 (integer),\n'
        '  "strengths": ["strength 1", "strength 2", ...],\n'
        '  "improvements": ["improvement 1", "improvement 2", ...]\n'
        "}"
    )

    user_prompt = (
        f"QUESTION: {question}\n\n"
        f"CANDIDATE ANSWER: {answer}\n\n"
        f"Please provide your evaluation in the required JSON structure."
    )

    # 3. Call Groq API
    try:
        logger.info("Dispatching answer evaluation request to Groq API...")
        headers = {
            "Authorization": f"Bearer {actual_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": 1024
        }
        
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        
        response_data = response.json()
        raw_content = response_data["choices"][0]["message"]["content"].strip()
        
        # Parse evaluation JSON
        eval_dict = json.loads(raw_content)
        
        # Verify required keys
        required_keys = ["score", "technical_depth", "communication", "completeness", "strengths", "improvements"]
        if all(k in eval_dict for k in required_keys):
            logger.info("Successfully received and validated answer evaluation from Groq API.")
            return {
                "score": float(eval_dict["score"]),
                "technical_depth": int(eval_dict["technical_depth"]),
                "communication": int(eval_dict["communication"]),
                "completeness": int(eval_dict["completeness"]),
                "strengths": eval_dict["strengths"],
                "improvements": eval_dict["improvements"]
            }
            
        logger.error("API returned JSON, but it does not match required schema format.")
        return generate_fallback_evaluation(question, answer)

    except Exception as e:
        logger.error(f"Failed to evaluate answer via Groq API: {e}. Falling back to offline evaluation.", exc_info=True)
        return generate_fallback_evaluation(question, answer)


# Optional: Standalone evaluator test block
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_q = "Explain the difference between Random Forest and XGBoost."
    test_a = (
        "Random Forest combines multiple decision trees and averages predictions. "
        "XGBoost builds trees sequentially and focuses on correcting previous errors."
    )
    
    # Standalone verification run (uses GROQ_API_KEY environment variable if present)
    res = evaluate_answer(test_q, test_a)
    print("\n--- Standalone Answer Evaluator Results ---")
    print(json.dumps(res, indent=2))
    print("-------------------------------------------\n")
