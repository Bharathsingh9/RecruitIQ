"""
Retrieval engine module for HireGen AI.
Bridges user queries to vector database similarity searches.
"""

import logging
from typing import List, Dict, Any

from app.rag.embeddings import generate_embeddings
from app.rag.vector_store import VectorStore

# Configure logger
logger = logging.getLogger(__name__)

PERSIST_DIR = "vector_store_data"


def retrieve_documents(
    query: str,
    k: int = 5,
    db_type: str = "faiss",
    persist_dir: str = PERSIST_DIR
) -> List[Dict[str, Any]]:
    """
    Computes vector representation of the query and fetches the top K matching document chunks.

    Args:
        query (str): The search query.
        k (int): Number of matching document chunks to retrieve. Defaults to 5.
        db_type (str): Type of vector store database to read ('faiss' or 'chromadb'). Defaults to 'faiss'.
        persist_dir (str): Persist folder location where database index files are stored.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing matching chunks, with keys:
            - "text": The textual content segment.
            - "metadata": Metadata dict containing source details.
            - "score": Computed similarity distance/score.
    """
    logger.info(f"Retrieving top {k} matching segments for query: '{query}'...")
    
    try:
        # 1. Compute query vector
        query_embeddings = generate_embeddings([query])
        if not query_embeddings:
            logger.error("Failed to generate embedding vector for user query.")
            return []
        query_vector = query_embeddings[0]

        # 2. Initialize and load vector database
        logger.info(f"Loading '{db_type}' index from '{persist_dir}'...")
        store = VectorStore(db_type=db_type, persist_dir=persist_dir)
        store.load()

        # 3. Query similarities
        search_hits = store.similarity_search(query_vector, k=k)
        
        # 4. Format outputs
        results = []
        for chunk, score in search_hits:
            results.append({
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "score": round(score, 4)
            })

        logger.info(f"Retrieved {len(results)} matching segments.")
        return results

    except Exception as e:
        logger.error(f"Error during document retrieval: {e}", exc_info=True)
        return []


# Optional: Standalone retrieval test block
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Standalone verification query
    q = "What questions does Google ask for ML Engineer roles?"
    res = retrieve_documents(q, k=3)
    
    print(f"\n--- Retriever Test Query: '{q}' ---")
    for i, doc in enumerate(res, 1):
        print(f"\n[{i}] Source: {doc['metadata']['source']} (Distance: {doc['score']})")
        print(f"Content: {doc['text'][:200]}...")
    print("------------------------------------\n")
