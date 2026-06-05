"""
Verification script for Phase 1: Resume Parser.
Programmatically creates a mock PDF resume, parses it, extracts details, and validates the output.
"""

import os
import logging
import fitz  # PyMuPDF

from resume_parser.parser import extract_text_from_pdf
from resume_parser.extractor import extract_name, extract_email, extract_phone
from resume_parser.skills import extract_skills

# Setup logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def create_sample_resume_pdf(filename: str) -> None:
    """
    Creates a sample PDF resume programmatically using PyMuPDF (fitz) to facilitate testing.
    """
    print(f"Creating sample PDF resume: '{filename}'...")
    
    doc = fitz.open()
    page = doc.new_page()
    
    # Resume content text lines
    lines = [
        ("AARAV SHARMA", 36, True),  # Text, font size, bold flag
        ("Software Development Engineer", 12, False),
        ("Email: aarav.sharma@domain.com | Mobile: +91 98765 43210", 10, False),
        ("GitHub: github.com/aaravs | LinkedIn: linkedin.com/in/aarav", 10, False),
        ("", 10, False),
        ("PROFESSIONAL SUMMARY", 14, True),
        ("Experienced Senior Software Engineer with a passion for designing scalable", 10, False),
        ("systems, building machine learning models, and orchestrating containerized apps.", 10, False),
        ("", 10, False),
        ("EDUCATION", 14, True),
        ("Bachelor of Technology in Computer Science | IIT Delhi | 2018 - 2022", 10, False),
        ("", 10, False),
        ("WORK EXPERIENCE", 14, True),
        ("Senior Backend Engineer - TechCorp (2022 - Present)", 11, True),
        ("- Designed microservices using Python and Java, boosting throughput by 40%.", 10, False),
        ("- Built predictive analytics systems utilizing Machine Learning models and pandas/numpy.", 10, False),
        ("- Managed container deployments with Docker and Kubernetes on AWS cloud.", 10, False),
        ("", 10, False),
        ("SKILLS", 14, True),
        ("Languages: Python, Java, SQL", 10, False),
        ("Libraries: Pandas, NumPy, scikit-learn", 10, False),
        ("Tools & Platforms: Docker, Kubernetes, AWS, Git", 10, False)
    ]
    
    y = 50  # Starting Y coordinate
    for text, size, is_bold in lines:
        if text == "":
            y += 15
            continue
            
        font = "hebo" if is_bold else "helv"
        page.insert_text((50, y), text, fontsize=size, fontname=font)
        y += size + 8
        
    doc.save(filename)
    doc.close()
    print("Sample PDF resume created successfully.\n")


def main() -> None:
    # Set the name of our sample resume
    sample_pdf = "sample_resume.pdf"
    
    # Generate the sample PDF
    create_sample_resume_pdf(sample_pdf)
    
    # 1. Parse PDF text
    print("=" * 60)
    print("STEP 1: Extracting text from PDF...")
    print("=" * 60)
    pdf_text = extract_text_from_pdf(sample_pdf)
    print(f"--- Extracted Text Preview (First 500 chars) ---\n")
    print(pdf_text[:500])
    print("\n-----------------------------------------------\n")
    
    # 2. Extract Metadata & Skills
    print("=" * 60)
    print("STEP 2: Extracting details from text...")
    print("=" * 60)
    
    name = extract_name(pdf_text)
    email = extract_email(pdf_text)
    phone = extract_phone(pdf_text)
    skills = extract_skills(pdf_text)
    
    # 3. Print Results in readable format
    print("\n" + "=" * 60)
    print("PARSE RESULTS SUMMARY")
    print("=" * 60)
    print(f"Candidate Name : {name}")
    print(f"Email Address  : {email}")
    print(f"Phone Number   : {phone}")
    print(f"Matched Skills : {', '.join(skills) if skills else 'None'}")
    print("=" * 60 + "\n")

    # Clean up generated test file
    if os.path.exists(sample_pdf):
        os.remove(sample_pdf)
        print(f"Cleaned up temporary file '{sample_pdf}'.")


if __name__ == "__main__":
    main()
