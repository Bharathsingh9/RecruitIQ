"""
Skill extraction module for resume parser.
Matches text content against a predefined, configurable skill database using regex with boundary protections.
"""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)

# Predefined configurable skill database
SKILLS = [
    "python",
    "java",
    "sql",
    "machine learning",
    "deep learning",
    "docker",
    "kubernetes",
    "aws",
    "pandas",
    "numpy"
]


def clean_text_for_skills(text: str) -> str:
    """
    Cleans and normalizes text for skill matching.
    Converts to lowercase, removes newlines, and replaces punctuation with spaces.

    Args:
        text (str): The raw text to clean.

    Returns:
        str: Normalized, lowercase text.
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace newlines, carriage returns, and tabs with space
    text = re.sub(r'[\r\n\t]+', ' ', text)
    
    # Replace common separators/punctuation (like hyphens, underscores, slashes) with space
    # to facilitate matching skills like "machine-learning" as "machine learning"
    text = re.sub(r'[-_/]', ' ', text)
    
    # Normalize multiple whitespace characters to a single space
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_skills(text: str) -> List[str]:
    """
    Extracts matches from a predefined list of skills (SKILLS) found in the text.
    Ensures case-insensitive matching, no duplicates, alphabetical sorting, 
    and prevents false positives (e.g. 'java' matching 'javascript' or 'sql' matching 'mysql').

    Args:
        text (str): The text content of the resume.

    Returns:
        List[str]: A sorted list of unique skills matched in the text.
    """
    if not text:
        return []

    try:
        cleaned_text = clean_text_for_skills(text)
        matched_skills = set()

        for skill in SKILLS:
            # Clean skill to match formatting of cleaned text
            skill_clean = clean_text_for_skills(skill)
            if not skill_clean:
                continue
                
            # Create regex pattern with lookbehinds and lookaheads to ensure
            # the matched term is a whole word/phrase, preventing issues like
            # 'java' matching 'javascript' or 'sql' matching 'nosql'.
            escaped_skill = re.escape(skill_clean)
            pattern = rf'(?<![a-zA-Z0-9]){escaped_skill}(?![a-zA-Z0-9])'
            
            if re.search(pattern, cleaned_text):
                logger.info(f"Matched skill: {skill}")
                matched_skills.add(skill)

        return sorted(list(matched_skills))

    except Exception as e:
        logger.error(f"Error during skill extraction: {e}", exc_info=True)
        return []
