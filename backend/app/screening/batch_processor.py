"""
Batch processing module for screening multiple candidate resumes in parallel.
Extracts candidate information, matches skills, runs predictions, and saves records.
"""

import os
import logging
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from resume_parser.parser import extract_text_from_pdf
from resume_parser.extractor import extract_name, extract_email, extract_phone
from resume_parser.skills import extract_skills
from matching.jd_matcher import calculate_match_score
from scoring.resume_scorer import calculate_overall_resume_score
from ml_models.predict import predict_candidate
from database.db import insert_candidate

# Configure logger
logger = logging.getLogger(__name__)


def process_single_resume(
    pdf_path: str,
    jd_text: str,
    experience_years: float = 3.0,
    education_score: float = 80.0,
    certifications: int = 1,
    projects_count: int = 2
) -> Dict[str, Any]:
    """
    Parses a single resume PDF and scores/classifies the candidate.
    """
    filename = os.path.basename(pdf_path)
    try:
        logger.info(f"Processing candidate resume: '{filename}'")
        
        # 1. Parse PDF text
        resume_text = extract_text_from_pdf(pdf_path)
        if not resume_text:
            raise ValueError(f"Extracted text is empty for {filename}")
            
        # 2. Extract profile attributes
        name = extract_name(resume_text)
        email = extract_email(resume_text)
        phone = extract_phone(resume_text)
        resume_skills = extract_skills(resume_text)
        
        # Extract skills from job description
        jd_skills = extract_skills(jd_text)
        
        # 3. Match skills
        match_results = calculate_match_score(resume_skills, jd_skills)
        match_score = match_results["match_score"]
        matched_skills = match_results["matched_skills"]
        missing_skills = match_results["missing_skills"]
        
        # 4. Resume scoring engine
        scorer_res = calculate_overall_resume_score(
            skills_match=match_score,
            experience_years=experience_years,
            projects_count=projects_count,
            education_score=education_score
        )
        
        # 5. ML Classifier prediction
        pred_res = predict_candidate(
            skills_match=match_score,
            experience_years=experience_years,
            education_score=education_score,
            certifications=certifications
        )
        prediction = pred_res["prediction"]
        confidence = pred_res["confidence"]
        
        # Use filename as candidate name fallback if not parsed
        candidate_name = name
        if not candidate_name or candidate_name == "Not Found" or candidate_name.strip() == "":
            candidate_name = os.path.splitext(filename)[0].replace("_", " ").title()
            
        # 6. Insert candidate into SQLite / Postgres database
        cand_id = insert_candidate(
            name=candidate_name,
            resume_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            experience_years=experience_years,
            education_score=education_score,
            certifications=certifications,
            prediction=prediction
        )
        
        logger.info(f"Successfully processed single resume: {filename} (ID: {cand_id})")
        return {
            "status": "success",
            "id": cand_id,
            "name": candidate_name,
            "email": email,
            "phone": phone,
            "filename": filename,
            "match_score": match_score,
            "resume_score": scorer_res["overall_score"],
            "grade": scorer_res["grade"],
            "prediction": prediction,
            "confidence": confidence,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills
        }
        
    except Exception as e:
        logger.error(f"Error processing resume file {filename}: {e}", exc_info=True)
        return {
            "status": "failed",
            "filename": filename,
            "error": str(e)
        }


def process_multiple_resumes(
    pdf_paths: List[str],
    jd_text: str,
    experience_years_list: Optional[List[float]] = None,
    education_score_list: Optional[List[float]] = None,
    certifications_list: Optional[List[int]] = None,
    projects_count_list: Optional[List[int]] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[Dict[str, Any]]:
    """
    Processes a list of resume PDF paths concurrently using ThreadPoolExecutor.
    """
    total_files = len(pdf_paths)
    results = []
    
    logger.info(f"Starting batch process for {total_files} resume files...")
    
    # Pre-fill lists with defaults if not provided to match pdf_paths size
    exp_list = experience_years_list or [3.0] * total_files
    edu_list = education_score_list or [80.0] * total_files
    certs_list = certifications_list or [1] * total_files
    projs_list = projects_count_list or [2] * total_files
    
    # Determine safe number of worker threads
    max_workers = min(32, os.cpu_count() or 4) * 2
    logger.info(f"Using {max_workers} thread pool workers for batch resume processing.")
    
    completed_count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks
        futures = {}
        for idx, path in enumerate(pdf_paths):
            future = executor.submit(
                process_single_resume,
                pdf_path=path,
                jd_text=jd_text,
                experience_years=exp_list[idx],
                education_score=edu_list[idx],
                certifications=certs_list[idx],
                projects_count=projs_list[idx]
            )
            futures[future] = path
            
        # Collect results as they complete
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            
            completed_count += 1
            if progress_callback:
                progress_callback(completed_count, total_files)
                
    logger.info(f"Batch processing completed. Successful: {len([r for r in results if r['status'] == 'success'])}/{total_files}")
    return results
