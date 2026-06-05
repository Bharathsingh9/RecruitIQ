"""
Centralized Groq LLM API client wrapper for HireGen AI.
Handles API requests with exponential backoff retry logic, structured JSON parsing, and exception management.
"""

import time
import json
import logging
import requests
from typing import Dict, Any, List, Optional
import app_config as config

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqClient:
    """
    Client wrapper for interacting with Groq Cloud LLM API.
    """
    def __init__(self, api_key: Optional[str] = None):
        # Fallback to configured key if not passed explicitly
        self.api_key = api_key or config.GROQ_API_KEY
        self.model = config.LLM_MODEL

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        max_retries: int = 3,
        initial_backoff: float = 2.0
    ) -> Optional[str]:
        """
        Dispatches chat completion requests to Groq with retries and exponential backoff.
        """
        if not self.api_key:
            logger.warning("Groq API key not set. Skipping API request.")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        backoff = initial_backoff
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Dispatching request to Groq API (Attempt {attempt}/{max_retries})...")
                response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=25)
                response.raise_for_status()
                
                resp_json = response.json()
                content = resp_json["choices"][0]["message"]["content"].strip()
                return content

            except requests.exceptions.HTTPError as http_err:
                status_code = http_err.response.status_code if http_err.response is not None else 500
                logger.error(f"Groq API HTTP Error {status_code}: {http_err}")
                if status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    logger.info(f"Retrying in {backoff} seconds...")
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    break
            except requests.exceptions.RequestException as req_err:
                logger.error(f"Groq Request Exception: {req_err}")
                if attempt < max_retries:
                    logger.info(f"Retrying in {backoff} seconds...")
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    break
            except Exception as e:
                logger.error(f"Unexpected error calling Groq: {e}", exc_info=True)
                break
                
        return None

    def get_structured_json(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback_json: Dict[str, Any],
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Sends requests forcing JSON format, parsing output into Python dict.
        Falls back to provided dictionary if parsing fails or client is offline.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        raw_output = self.chat_completion(
            messages=messages,
            response_format="json",
            temperature=temperature,
            max_tokens=max_tokens
        )

        if not raw_output:
            logger.warning("No response from Groq. Returning fallback JSON structure.")
            return fallback_json

        try:
            parsed_data = json.loads(raw_output)
            return parsed_data
        except json.JSONDecodeError as decode_err:
            logger.error(f"Failed to parse JSON response: '{raw_output}'. Error: {decode_err}")
            return fallback_json
