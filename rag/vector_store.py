"""
Vector Database Connector module for HireGen AI.
Supports both FAISS (file-based index storage) and ChromaDB (persistent client database) 
for indexing and similarity search of document chunks.
"""

import os
import pickle
import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

# Configure logger
logger = logging.getLogger(__name__)


class VectorStore:
    """
    Unified Vector Store wrapper class that abstracts interactions with 
    FAISS and ChromaDB backends.
    """

    def __init__(self, db_type: str = "faiss", persist_dir: str = "vector_store_data"):
        """
        Initializes the vector database instance.

        Args:
            db_type (str): Database type to use - 'faiss' or 'chromadb'. Defaults to 'faiss'.
            persist_dir (str): Directory where the index/database files will be stored.
        """
        self.db_type = db_type.lower()
        self.persist_dir = persist_dir
        self.chunks: List[Dict[str, Any]] = []
        self.faiss_index = None
        self.chroma_client = None
        self.chroma_collection = None
        
        # Ensure directories exist
        os.makedirs(self.persist_dir, exist_ok=True)
        logger.info(f"Initialized VectorStore connector for '{self.db_type}' at directory: '{self.persist_dir}'")

    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        """
        Populates the vector store database index with document chunks and pre-computed embeddings.

        Args:
            chunks (List[Dict[str, Any]]): List of chunk dictionaries containing 'text' and 'metadata'.
            embeddings (List[List[float]]): List of floating vector embeddings corresponding to chunks.
        """
        if not chunks or not embeddings:
            logger.warning("No chunks or embeddings provided to add to vector store.")
            return

        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch between number of chunks ({len(chunks)}) and embeddings ({len(embeddings)})")

        self.chunks = chunks
        embeddings_np = np.array(embeddings, dtype=np.float32)

        if self.db_type == "faiss":
            try:
                import faiss
                dimension = embeddings_np.shape[1]
                logger.info(f"Initializing FAISS IndexFlatL2 with dimension size: {dimension}...")
                
                # Use L2 (Euclidean) distance index
                self.faiss_index = faiss.IndexFlatL2(dimension)
                self.faiss_index.add(embeddings_np)
                logger.info(f"Successfully added {len(chunks)} elements into FAISS index.")
            except ImportError as err:
                logger.error("Failed to import FAISS library. Make sure 'faiss-cpu' is installed.")
                raise err

        elif self.db_type == "chromadb":
            try:
                import chromadb
                logger.info("Initializing ChromaDB persistent storage client...")
                self.chroma_client = chromadb.PersistentClient(path=self.persist_dir)
                
                # Get or create collection
                self.chroma_collection = self.chroma_client.get_or_create_collection(
                    name="interview_prep_kb"
                )
                
                ids = [f"chunk_{i}" for i in range(len(chunks))]
                documents = [c["text"] for c in chunks]
                metadatas = [c["metadata"] for c in chunks]
                
                # Add embeddings and document metadata to Chroma collection
                self.chroma_collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                logger.info(f"Successfully added {len(chunks)} elements to Chroma collection.")
            except ImportError as err:
                logger.error("Failed to import ChromaDB library. Make sure 'chromadb' is installed.")
                raise err

    def save(self) -> None:
        """
        Persists the index to disk.
        """
        if self.db_type == "faiss":
            if self.faiss_index is None:
                logger.warning("FAISS index is not initialized. Nothing to save.")
                return
            
            try:
                import faiss
                index_path = os.path.join(self.persist_dir, "faiss.index")
                chunks_path = os.path.join(self.persist_dir, "chunks.pkl")
                
                logger.info(f"Saving FAISS index to '{index_path}'...")
                faiss.write_index(self.faiss_index, index_path)
                
                logger.info(f"Saving chunk text/metadata to '{chunks_path}'...")
                with open(chunks_path, "wb") as f:
                    pickle.dump(self.chunks, f)
                    
                logger.info("FAISS files saved successfully.")
            except Exception as e:
                logger.error(f"Error saving FAISS store: {e}", exc_info=True)
                raise e

        elif self.db_type == "chromadb":
            # ChromaDB's PersistentClient writes data automatically
            logger.info("ChromaDB automatically persisted updates to disk directory.")

    def load(self) -> None:
        """
        Loads the persisted index files from disk.
        """
        if self.db_type == "faiss":
            index_path = os.path.join(self.persist_dir, "faiss.index")
            chunks_path = os.path.join(self.persist_dir, "chunks.pkl")
            
            if not os.path.exists(index_path) or not os.path.exists(chunks_path):
                raise FileNotFoundError(f"FAISS index files not found in persist directory '{self.persist_dir}'")
                
            try:
                import faiss
                logger.info(f"Loading FAISS index from '{index_path}'...")
                self.faiss_index = faiss.read_index(index_path)
                
                logger.info(f"Loading chunk text/metadata from '{chunks_path}'...")
                with open(chunks_path, "rb") as f:
                    self.chunks = pickle.load(f)
                    
                logger.info(f"Successfully loaded FAISS index with {self.faiss_index.ntotal} elements.")
            except Exception as e:
                logger.error(f"Error loading FAISS store: {e}", exc_info=True)
                raise e

        elif self.db_type == "chromadb":
            try:
                import chromadb
                logger.info(f"Loading ChromaDB persistent store from '{self.persist_dir}'...")
                self.chroma_client = chromadb.PersistentClient(path=self.persist_dir)
                self.chroma_collection = self.chroma_client.get_collection(name="interview_prep_kb")
                logger.info("Successfully loaded ChromaDB collection.")
            except Exception as e:
                logger.error(f"Error loading ChromaDB: {e}", exc_info=True)
                raise e

    def similarity_search(
        self, 
        query_embedding: List[float], 
        k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Performs vector similarity search against the store.

        Args:
            query_embedding (List[float]): Floating representation vector of query.
            k (int): Number of nearest documents to return.

        Returns:
            List[Tuple[Dict[str, Any], float]]: A list of tuples containing (chunk, score/distance).
        """
        if self.db_type == "faiss":
            if self.faiss_index is None:
                raise ValueError("FAISS index is not initialized or loaded.")
                
            query_np = np.array([query_embedding], dtype=np.float32)
            distances, indices = self.faiss_index.search(query_np, k)
            
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                # Index -1 indicates no match or out-of-bounds
                if idx != -1 and idx < len(self.chunks):
                    results.append((self.chunks[idx], float(dist)))
            return results

        elif self.db_type == "chromadb":
            if self.chroma_collection is None:
                raise ValueError("ChromaDB collection is not initialized or loaded.")
                
            query_results = self.chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            
            results = []
            # Extract elements from queries output lists
            documents = query_results["documents"][0]
            metadatas = query_results["metadatas"][0]
            distances = query_results["distances"][0] if "distances" in query_results else [0.0] * len(documents)
            
            for doc, meta, dist in zip(documents, metadatas, distances):
                chunk = {"text": doc, "metadata": meta}
                results.append((chunk, float(dist)))
            return results

        return []
