"""
Information extraction module for resume parsing.
Extracts Candidate Name (via spaCy NER), Email, and Phone number using robust patterns.
"""

import re
import logging
from typing import Optional
import spacy

# Configure logging
logger = logging.getLogger(__name__)

# Compile Regex patterns for efficiency
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

# Matches various international and Indian formats
# Supports optional country codes, area codes, separators like hyphens, dots, spaces, parentheses
PHONE_REGEX = re.compile(
    r'(?:'
    r'(?:\+|\b0{0,2})\d{1,4}[-.\s]?'         # Country code: e.g. +91, +1, 0091
    r'(?:\(?\d{2,5}\)?[-.\s]?)?'             # Area code or prefix
    r'\d{3,5}[-.\s]?\d{3,5}(?:[-.\s]?\d{3,5})?' # Main number parts
    r'|'
    r'\b\d{10,12}\b'                         # Raw 10-12 digit numbers
    r')'
)

# Global variable for lazy loading spaCy model
_NLP = None


def _get_spacy_model() -> spacy.language.Language:
    """
    Lazy loads and returns the spaCy 'en_core_web_sm' model.
    Downloads the model if it is not present locally.
    """
    global _NLP
    if _NLP is None:
        try:
            logger.info("Attempting to load spaCy model 'en_core_web_sm'...")
            _NLP = spacy.load("en_core_web_sm")
        except OSError:
            logger.info("spaCy model 'en_core_web_sm' not found. Downloading...")
            try:
                from spacy.cli import download
                download("en_core_web_sm")
                _NLP = spacy.load("en_core_web_sm")
                logger.info("Successfully downloaded and loaded spaCy model 'en_core_web_sm'.")
            except Exception as download_err:
                logger.error(f"Failed to download spaCy model: {download_err}")
                raise download_err
    return _NLP


def extract_email(text: str) -> str:
    """
    Extracts the first valid email address from the text using regex.

    Args:
        text (str): The text to search.

    Returns:
        str: The extracted email address, or "Not Found" if extraction fails.
    """
    if not text:
        return "Not Found"

    try:
        match = EMAIL_REGEX.search(text)
        if match:
            email = match.group(0).strip()
            logger.info(f"Extracted email: {email}")
            return email
    except Exception as e:
        logger.error(f"Error during email extraction: {e}")

    return "Not Found"


def extract_phone(text: str) -> str:
    """
    Extracts the first valid phone number from the text.
    Cleans up the format by removing spaces, hyphens, and parentheses, 
    while preserving country code prefix ('+').

    Args:
        text (str): The text to search.

    Returns:
        str: The cleaned phone number, or "Not Found" if extraction fails.
    """
    if not text:
        return "Not Found"

    try:
        matches = PHONE_REGEX.findall(text)
        for match_str in matches:
            # Clean candidate string to check digits
            cleaned_digits = "".join(c for c in match_str if c.isdigit())
            
            # Avoid false positives like dates, ZIP codes, and version numbers
            # A phone number typically has between 9 and 15 digits
            if 9 <= len(cleaned_digits) <= 15:
                # Retain the leading '+' if it was present in original match
                is_positive_lead = match_str.strip().startswith('+')
                cleaned_phone = f"+{cleaned_digits}" if is_positive_lead else cleaned_digits
                logger.info(f"Extracted and cleaned phone number: {cleaned_phone} (from '{match_str.strip()}')")
                return cleaned_phone
    except Exception as e:
        logger.error(f"Error during phone extraction: {e}")

    return "Not Found"


def extract_name(text: str) -> str:
    """
    Extracts the candidate's name from resume text using a robust 3-stage pipeline:
    1. Line-based Heuristics: Scans the first 5 non-empty lines for a line matching name formats.
    2. spaCy Line NER: Scans early lines using spaCy NER with case normalization.
    3. spaCy Fallback Search: Scans the first 1000 characters for any PERSON entity.

    Args:
        text (str): The text to search.

    Returns:
        str: The extracted name, or "Not Found" if extraction fails.
    """
    if not text:
        return "Not Found"

    blacklist = {
        "resume", "curriculum", "vitae", "summary", "experience", 
        "education", "skills", "contact", "profile", "about", 
        "work", "history", "professional", "personal", "projects", 
        "certifications", "hobbies", "languages", "phone", "email",
        "address", "mobile", "linkedin", "github", "career", "objective",
        "page", "details", "info", "engineer", "developer", "manager", "analyst"
    }

    try:
        # Split text into lines to analyze the top of the resume first
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        candidate_lines = lines[:5]
        
        # --- Stage 1: Line-based Heuristics ---
        for line in candidate_lines:
            line_clean = re.sub(r'\s+', ' ', line)
            
            # Skip if contains symbols common in contact details, links, or sections
            if any(c in line_clean for c in ["@", ":", "/", "\\", "|", "•"]) or re.search(r'\d', line_clean):
                continue
                
            words = line_clean.split()
            # Most candidate names are between 2 and 4 words
            if 2 <= len(words) <= 4:
                # All words should start with uppercase/capital letters
                all_title = all(w[0].isupper() for w in words if w.isalpha())
                not_blacklisted = not any(w.lower() in blacklist for w in words)
                
                if all_title and not_blacklisted:
                    formatted_name = line_clean.title()
                    logger.info(f"Extracted candidate name via Line Heuristics: {formatted_name}")
                    return formatted_name

        # --- Stage 2: spaCy Line NER ---
        nlp = _get_spacy_model()
        for line in candidate_lines:
            if "@" in line or "http" in line or "www" in line or any(c in line for c in [":", "/", "\\"]):
                continue
                
            line_clean = re.sub(r'\s+', ' ', line)
            words = line_clean.split()
            
            if 1 <= len(words) <= 4:
                # Standardize case to help spaCy's model recognize entities
                is_all_caps = all(w.isupper() for w in words if w.isalpha())
                test_str = line_clean.title() if is_all_caps else line_clean
                
                doc = nlp(test_str)
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        name_words = ent.text.strip().split()
                        if 1 <= len(name_words) <= 4:
                            if not any(w.lower() in blacklist for w in name_words):
                                logger.info(f"Extracted candidate name via spaCy Line NER: {test_str}")
                                return test_str
                                
        # --- Stage 3: spaCy Fallback Header Search ---
        header_text = text[:1000]
        doc = nlp(header_text)
        candidates = []
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                name = re.sub(r'\s+', ' ', name)
                words = name.split()
                if 1 <= len(words) <= 4:
                    all_capitalized = all(w.istitle() or w.isupper() or w == '.' for w in words)
                    no_digits_or_special = not re.search(r'[^a-zA-Z\s.-]', name)
                    not_blacklisted = not any(w.lower() in blacklist for w in words)
                    
                    if all_capitalized and no_digits_or_special and not_blacklisted:
                        candidates.append(name)
                        
        if candidates:
            best_candidate = candidates[0]
            logger.info(f"Extracted candidate name via spaCy Fallback: {best_candidate}")
            return best_candidate

    except Exception as e:
        logger.error(f"Error during name extraction: {e}", exc_info=True)

    return "Not Found"
