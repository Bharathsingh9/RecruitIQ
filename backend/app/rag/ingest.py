"""
Ingestion script for the RAG Interview Knowledge Base.
Loads TXT/PDF files, cleans and chunks the text, computes embeddings, and persists the vector index.
"""

import os
import re
import logging
from typing import List, Dict, Any

from app.rag.embeddings import generate_embeddings
from app.rag.vector_store import VectorStore

# Configure logging
logger = logging.getLogger(__name__)

# Configurable constants
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
DATA_DIRS = [
    "data/interview_experiences",
    "data/dsa_questions",
    "data/company_questions"
]
DEFAULT_DB_TYPE = "faiss"
PERSIST_DIR = "vector_store_data"


def load_pdf_text(pdf_path: str) -> str:
    """
    Extracts text from a PDF file using PyMuPDF (fitz).
    """
    try:
        import fitz
        text = []
        with fitz.open(pdf_path) as doc:
            for page in doc:
                page_text = page.get_text()
                if page_text:
                    text.append(page_text)
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Error loading PDF '{pdf_path}': {e}", exc_info=True)
        return ""


def recursive_split_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Custom character-based text splitter that splits text recursively on separators
    (paragraphs, lines, spaces) to fit chunk size constraints without cutting words.
    Mimics RecursiveCharacterTextSplitter behavior.
    """
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # If we aren't at the end of the text, backtrack to find a clean separator
        if end < text_len:
            best_boundary = -1
            # Search window of 150 characters back from target end
            search_window = text[max(start, end - 150):end]
            
            # Look for standard boundaries
            for separator in ["\n\n", "\n", " "]:
                pos = search_window.rfind(separator)
                if pos != -1:
                    # Convert window offset back to absolute position
                    best_boundary = max(start, end - 150) + pos + len(separator)
                    break
            
            if best_boundary != -1:
                end = best_boundary
                
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
            
        if end >= text_len:
            break
            
        # Move forward, accounting for overlap, ensuring start always advances
        next_start = end - chunk_overlap
        if next_start <= start:
            start = end
        else:
            start = next_start
            
    return chunks


def load_documents() -> List[Dict[str, Any]]:
    """
    Reads all PDF and TXT documents from the designated data folders.
    
    Returns:
        List[Dict[str, Any]]: List of documents with 'text' and 'metadata'.
    """
    documents = []
    
    for folder in DATA_DIRS:
        if not os.path.exists(folder):
            logger.info(f"Folder '{folder}' does not exist. Creating...")
            os.makedirs(folder, exist_ok=True)
            continue
            
        for file_name in os.listdir(folder):
            file_path = os.path.join(folder, file_name)
            
            # Only process files
            if not os.path.isfile(file_path):
                continue
                
            text_content = ""
            category = os.path.basename(folder)
            
            if file_name.lower().endswith(".txt"):
                try:
                    logger.info(f"Loading text document: '{file_path}'")
                    with open(file_path, "r", encoding="utf-8") as f:
                        text_content = f.read()
                except Exception as e:
                    logger.error(f"Error reading file '{file_path}': {e}")
                    
            elif file_name.lower().endswith(".pdf"):
                logger.info(f"Loading PDF document: '{file_path}'")
                text_content = load_pdf_text(file_path)
                
            if text_content.strip():
                documents.append({
                    "text": text_content,
                    "metadata": {
                        "source": file_name,
                        "category": category,
                        "path": file_path
                    }
                })
                
    logger.info(f"Loaded {len(documents)} raw documents in total.")
    return documents


def clean_documents(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Cleans raw document texts by stripping whitespace and removing duplicates.
    """
    logger.info("Cleaning raw documents...")
    cleaned_docs = []
    seen_texts = set()
    
    for doc in docs:
        raw_text = doc["text"]
        
        # Clean whitespaces
        cleaned_text = re.sub(r'\s+', ' ', raw_text).strip()
        
        # Prevent exact duplicate documents
        if cleaned_text not in seen_texts:
            seen_texts.add(cleaned_text)
            doc["text"] = cleaned_text
            cleaned_docs.append(doc)
            
    logger.info(f"Cleaned documents. Unique document count: {len(cleaned_docs)}")
    return cleaned_docs


def ingest_pipeline(db_type: str = DEFAULT_DB_TYPE) -> None:
    """
    Executes the full ingestion pipeline:
    1. Loads TXT and PDF documents from data folders.
    2. Cleans text.
    3. Chunks documents using Recursive split bounds.
    4. Computes SentenceTransformer embeddings.
    5. Saves to Vector Database (FAISS or ChromaDB).
    """
    # 1. Load & Clean
    raw_docs = load_documents()
    if not raw_docs:
        logger.warning("No documents found in data folders. Ingestion halted.")
        return
        
    unique_docs = clean_documents(raw_docs)
    
    # 2. Chunking
    logger.info("Splitting documents into chunks...")
    chunks = []
    for doc in unique_docs:
        split_segments = recursive_split_text(
            doc["text"], 
            chunk_size=CHUNK_SIZE, 
            chunk_overlap=CHUNK_OVERLAP
        )
        
        for segment in split_segments:
            chunks.append({
                "text": segment,
                "metadata": doc["metadata"]
            })
            
    logger.info(f"Created {len(chunks)} total text chunks.")
    
    # 3. Embeddings
    texts_to_embed = [c["text"] for c in chunks]
    embeddings = generate_embeddings(texts_to_embed)
    
    # 4. Save to Vector Store
    logger.info(f"Storing chunks in vector database of type '{db_type}'...")
    store = VectorStore(db_type=db_type, persist_dir=PERSIST_DIR)
    store.add_documents(chunks, embeddings)
    store.save()
    logger.info("Ingestion completed successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Run FAISS ingestion by default
    ingest_pipeline(DEFAULT_DB_TYPE)
