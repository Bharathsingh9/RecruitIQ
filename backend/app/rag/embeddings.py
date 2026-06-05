"""
Embeddings generation module for HireGen AI.
Uses SentenceTransformers to convert text segments into numerical vector embeddings.
"""

import logging
from typing import List
from sentence_transformers import SentenceTransformer

# Configure logger
logger = logging.getLogger(__name__)

# Global variable for lazy-loaded SentenceTransformer model
_EMBEDDING_MODEL = None
MODEL_NAME = "all-MiniLM-L6-v2"


def _get_embedding_model() -> SentenceTransformer:
    """
    Lazy loads and returns the SentenceTransformer model.
    """
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        try:
            logger.info(f"Loading SentenceTransformer model '{MODEL_NAME}'...")
            _EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model: {e}", exc_info=True)
            raise e
    return _EMBEDDING_MODEL


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generates dense vector embeddings for a list of text strings.

    Args:
        texts (List[str]): List of clean text documents/chunks to embed.

    Returns:
        List[List[float]]: A list of float vector representations.
    """
    if not texts:
        logger.warning("Empty list of texts provided for embedding generation.")
        return []

    try:
        model = _get_embedding_model()
        logger.info(f"Generating embeddings for {len(texts)} document chunks in batches...")
        
        # Batch processing (SentenceTransformer handles batching internally via batch_size parameter)
        embeddings_array = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # Convert NumPy array to standard Python list of lists
        embeddings_list = embeddings_array.tolist()
        logger.info("Successfully generated embeddings.")
        return embeddings_list

    except Exception as e:
        logger.error(f"Error during embedding generation: {e}", exc_info=True)
        raise e
