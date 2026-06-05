"""
End-to-End RAG (Retrieval-Augmented Generation) Pipeline.
Fetches relevant contextual chunks from the vector database and formats prompts
for the Groq Llama 3 API to produce precise, hallucination-free answers.
"""

import os
import logging
import requests
from typing import Dict, Any, List, Optional

from app.rag.retriever import retrieve_documents

# Configure logger
logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"
PERSIST_DIR = "vector_store_data"


def answer_query(
    query: str,
    db_type: str = "faiss",
    persist_dir: str = PERSIST_DIR,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes the retrieval-augmented generation loop to answer interview prep queries.

    Args:
        query (str): The candidate's interview question.
        db_type (str): Type of vector store database to read ('faiss' or 'chromadb'). Defaults to 'faiss'.
        persist_dir (str): Persist folder location where database index files are stored.
        api_key (Optional[str]): Groq API key overrides environment variable.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - "query": The input question.
            - "retrieved_documents": A list of text context strings retrieved.
            - "answer": The generated answer from the LLM (or fallback text).
    """
    logger.info(f"RAG Pipeline: Processing query: '{query}'...")
    
    # 1. Retrieve top 3 relevant chunks
    retrieved_segments = retrieve_documents(query, k=3, db_type=db_type, persist_dir=persist_dir)
    retrieved_texts = [doc["text"] for doc in retrieved_segments]
    
    # Format retrieved segments for system prompt
    context_blocks = []
    for doc in retrieved_segments:
        src = doc["metadata"].get("source", "Unknown Source")
        context_blocks.append(f"[Document: {src}]\n{doc['text']}")
    context_str = "\n\n".join(context_blocks)

    # 2. Design Prompt Template (Prompt Engineering)
    system_prompt = (
        "You are an expert interview preparation assistant.\n"
        "Use ONLY the retrieved context below to answer the candidate's question.\n\n"
        "Instructions:\n"
        "- Answer using ONLY the retrieved information. Do not use outside knowledge.\n"
        "- Be concise but detailed and specific. Mention company-specific insights.\n"
        "- If the information is not available in the context, clearly say: "
        "'I am sorry, but the retrieved knowledge base does not contain information to answer this question.'\n"
        "- Do not hallucinate or make up facts.\n\n"
        f"CONTEXT:\n{context_str}"
    )
    
    user_prompt = f"Question: {query}"

    # 3. Resolve API Key
    actual_key = api_key or os.environ.get("GROQ_API_KEY")

    # 4. Generate Answer
    if not actual_key:
        logger.warning("No Groq API Key found for RAG. Returning fallback results.")
        answer = (
            "⚠️ Groq API Key is not configured. Unable to connect to LLM. "
            "Here are the relevant retrieved contexts from the knowledge base:\n\n" + 
            "\n\n".join([f"📖 **{doc['metadata']['source']}**:\n{doc['text']}" for doc in retrieved_segments])
        )
    else:
        try:
            logger.info("Requesting completion from Groq API...")
            headers = {
                "Authorization": f"Bearer {actual_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            }
            
            response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            
            response_data = response.json()
            answer = response_data["choices"][0]["message"]["content"].strip()
            logger.info("Successfully received answer from Groq.")
            
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}", exc_info=True)
            answer = (
                f"⚠️ Failed to connect to Groq LLM ({e}).\n\n"
                f"Here are the matches retrieved from the knowledge base:\n\n" + 
                "\n\n".join([f"📖 **{doc['metadata']['source']}**:\n{doc['text']}" for doc in retrieved_segments])
            )

    return {
        "query": query,
        "retrieved_documents": retrieved_texts,
        "answer": answer
    }


# Optional: Standalone pipeline test block
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Standalone query (uses GROQ_API_KEY environment variable if present)
    test_q = "What questions does Google ask for ML Engineer roles?"
    res = answer_query(test_q)
    
    print("\n" + "=" * 60)
    print(f"RAG PIPELINE RUN FOR QUERY: '{res['query']}'")
    print("=" * 60)
    print(f"Answer:\n{res['answer']}\n")
    print("------------------------------------------------------------")
    print(f"Retrieved {len(res['retrieved_documents'])} context segments.")
    print("=" * 60 + "\n")
