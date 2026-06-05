"""
RAG Knowledge Assistant Router.
Handles question answering using the vector knowledge base index and LLM formatting.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api import deps
from app.app_config import settings

from app.rag.rag_pipeline import answer_query
from app.rag.retriever import retrieve_documents

logger = logging.getLogger(__name__)
router = APIRouter()


class RAGQueryRequest(BaseModel):
    query: str
    db_type: Optional[str] = "faiss"


class RAGSourceDoc(BaseModel):
    source: str
    text: str
    score: float


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[RAGSourceDoc]


@router.post("/query", response_model=RAGQueryResponse, status_code=status.HTTP_200_OK)
def query_knowledge_assistant(
    payload: RAGQueryRequest
):
    """
    Query the interview preparation RAG knowledge base.
    Retrieves matching document segments and generates a summary response.
    """
    if not payload.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty."
        )

    try:
        # Get raw retrieved docs for source formatting
        retrieved_docs = retrieve_documents(
            query=payload.query,
            k=3,
            db_type=payload.db_type,
            persist_dir="vector_store_data"
        )

        # Run full pipeline to get answer
        pipeline_res = answer_query(
            query=payload.query,
            db_type=payload.db_type,
            persist_dir="vector_store_data",
            api_key=settings.GROQ_API_KEY
        )

        sources_out = []
        for doc in retrieved_docs:
            src = doc["metadata"].get("source", "Unknown Source")
            sources_out.append(
                RAGSourceDoc(
                    source=src,
                    text=doc["text"],
                    score=doc["score"]
                )
            )

        return RAGQueryResponse(
            query=payload.query,
            answer=pipeline_res["answer"],
            sources=sources_out
        )

    except Exception as e:
        logger.error(f"Error querying RAG assistant: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query failed: {str(e)}"
        )
