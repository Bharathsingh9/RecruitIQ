"""
Generative AI Interview Question Generator.
Interacts with the Groq API (Llama 3 model) to create personalized technical 
and behavioral questions based on candidate skills, project descriptions, and JD requirements.
Includes a robust offline question generator fallback.
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional

# Configure logger
logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"


def generate_fallback_questions(
    candidate_skills: List[str],
    projects: List[str]
) -> Dict[str, List[str]]:
    """
    Generates standard mock interview questions based on candidate skills and projects
    when no Groq API Key is configured or the API request fails.
    """
    logger.info("Generating offline fallback interview questions...")
    
    tech_questions = []
    
    # Generate skill-based questions
    for skill in candidate_skills[:3]:
        tech_questions.append(
            f"Explain how you have used {skill.title()} in your previous work. "
            f"What are some common design patterns or challenges associated with it?"
        )
        tech_questions.append(
            f"Describe how you would optimize performance or troubleshoot a latency bottleneck when working with {skill.title()}."
        )
        
    # Generate project-based questions
    for proj in projects[:2]:
        tech_questions.append(
            f"Walk us through the end-to-end architecture of your project: '{proj.strip()}'. "
            f"What were the key database/design decisions you had to make?"
        )
        
    # Standard tech fallback if list is empty
    if not tech_questions:
        tech_questions = [
            "Explain the difference between supervised and unsupervised learning.",
            "How do you approach debugging a memory leak in a production application?",
            "Explain how you design a RESTful API to handle high-concurrency read requests."
        ]
        
    behavioral_questions = [
        "Describe a challenging technical project you worked on. What were the roadblocks and how did you overcome them?",
        "Tell us about a time you had to resolve a difficult bug or production issue under tight time constraints.",
        "How do you handle disagreements on technical design choices within your engineering team?"
    ]

    return {
        "technical_questions": tech_questions[:5],  # Cap at 5 questions
        "behavioral_questions": behavioral_questions[:3]  # Cap at 3 questions
    }


def generate_interview_questions(
    candidate_skills: List[str],
    projects: List[str],
    job_description: str,
    api_key: Optional[str] = None
) -> Dict[str, List[str]]:
    """
    Generates personalized interview questions based on skills, projects, and JD.
    Hits Groq Llama 3 API for structured JSON output. Falls back to offline questions if key is missing.

    Args:
        candidate_skills (List[str]): List of candidate skills.
        projects (List[str]): List of project descriptions or names.
        job_description (str): Text requirements of the job description.
        api_key (Optional[str]): Groq API Key (falls back to GROQ_API_KEY environment variable if None).

    Returns:
        Dict[str, List[str]]: A dictionary containing "technical_questions" and "behavioral_questions".
    """
    # 1. Resolve API Key
    actual_key = api_key or os.environ.get("GROQ_API_KEY")
    
    if not actual_key:
        logger.warning("No Groq API Key found. Returning offline fallback questions.")
        return generate_fallback_questions(candidate_skills, projects)

    # Clean input variables
    skills_str = ", ".join(candidate_skills) if candidate_skills else "None specified"
    projects_str = "\n".join([f"- {p}" for p in projects]) if projects else "None specified"
    
    # 2. Design Prompts
    system_prompt = (
        "You are an expert technical interviewer and AI recruiter. "
        "Generate a highly targeted set of interview questions for a candidate based on "
        "their skills, project experience, and the job requirements.\n\n"
        "Instructions:\n"
        "- Generate technical questions (4 to 5) directly relating to their skills and projects, matching the JD.\n"
        "- Avoid generic questions. Tailor them to technical details (e.g. optimizing models, architecture, code patterns).\n"
        "- Grade the questions from intermediate to advanced.\n"
        "- Generate behavioral questions (2 to 3) assessing engineering decision making, team communication, and problem-solving.\n"
        "- You MUST output a valid JSON object matching the schema below. Do not wrap in markdown tags or write conversational text.\n\n"
        "JSON SCHEMA:\n"
        "{\n"
        '  "technical_questions": ["question 1", "question 2", ...],\n'
        '  "behavioral_questions": ["question 1", "question 2", ...]\n'
        "}"
    )

    user_prompt = (
        f"CANDIDATE INFORMATION:\n"
        f"- Core Skills: {skills_str}\n"
        f"- Project Details:\n{projects_str}\n\n"
        f"JOB REQUIREMENTS:\n"
        f"- Job Description: {job_description}\n\n"
        f"Please generate the personalized interview questions in the required JSON structure."
    )

    # 3. Call Groq API
    try:
        logger.info(f"Dispatching API request to Groq using model {DEFAULT_MODEL}...")
        
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
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        
        response_data = response.json()
        raw_content = response_data["choices"][0]["message"]["content"]
        
        # Parse output JSON
        parsed_questions = json.loads(raw_content)
        
        # Verify schema elements
        if "technical_questions" in parsed_questions and "behavioral_questions" in parsed_questions:
            logger.info("Successfully received and validated questions from Groq API.")
            return {
                "technical_questions": parsed_questions["technical_questions"],
                "behavioral_questions": parsed_questions["behavioral_questions"]
            }
        
        logger.error("API returned JSON, but it does not match required schema format.")
        return generate_fallback_questions(candidate_skills, projects)

    except Exception as e:
        logger.error(f"Failed to generate questions via Groq API: {e}. Falling back to offline questions.", exc_info=True)
        return generate_fallback_questions(candidate_skills, projects)


# Optional: Example usage block for standalone generation testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Standalone test (uses environment variable GROQ_API_KEY if present)
    skills = ["Python", "Machine Learning", "Deep Learning", "Pandas", "NumPy"]
    projs = ["Fraud Detection System", "Resume Screening AI"]
    jd = "Looking for a Machine Learning Engineer with Python, NLP, Scikit-learn, and Deep Learning experience."
    
    res = generate_interview_questions(skills, projs, jd)
    print("\n--- Generated Questions Results ---")
    print(json.dumps(res, indent=2))
    print("-----------------------------------\n")
