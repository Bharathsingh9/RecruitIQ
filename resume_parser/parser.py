"""
PDF text extraction module using PyMuPDF (fitz).
Provides safe, robust extraction of text from PDF documents.
"""

import os
import logging
from typing import Optional
import fitz  # PyMuPDF

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Safely opens a PDF file, extracts text from all pages, and returns clean text.

    Args:
        pdf_path (str): The absolute or relative path to the PDF file.

    Returns:
        str: The extracted text from the PDF, or an empty string if extraction fails.

    Raises:
        FileNotFoundError: If the PDF file does not exist at the specified path.
        Exception: For general failures during parsing (e.g. corrupted PDF).
    """
    if not pdf_path:
        logger.error("Provided PDF path is empty or None.")
        return ""

    if not os.path.exists(pdf_path):
        error_msg = f"PDF file not found at path: {pdf_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    doc = None
    extracted_text_list = []

    try:
        logger.info(f"Opening PDF file for text extraction: {pdf_path}")
        doc = fitz.open(pdf_path)
        
        total_pages = len(doc)
        logger.info(f"Successfully opened PDF with {total_pages} page(s).")
        
        for page_num in range(total_pages):
            try:
                page = doc.load_page(page_num)
                # "text" format extracts standard plain text layout
                page_text = page.get_text("text")
                if page_text:
                    extracted_text_list.append(page_text)
            except Exception as page_err:
                logger.warning(f"Failed to extract text from page {page_num + 1} of {pdf_path}: {page_err}")
                continue

        # Combine text from all pages
        full_text = "\n".join(extracted_text_list)
        
        # Basic cleanup: strip leading/trailing whitespace
        clean_text = full_text.strip()
        logger.info(f"Successfully extracted {len(clean_text)} characters of text from {pdf_path}.")
        return clean_text

    except Exception as e:
        logger.error(f"Error occurred while processing PDF '{pdf_path}': {e}", exc_info=True)
        # Re-raise or return empty string? The requirement is: "Handle corrupted PDFs gracefully"
        # We log the traceback and return an empty string to handle it gracefully at application level.
        return ""
        
    finally:
        if doc is not None:
            try:
                doc.close()
                logger.info("Closed PDF document handle successfully.")
            except Exception as close_err:
                logger.warning(f"Error closing PDF document handle: {close_err}")
