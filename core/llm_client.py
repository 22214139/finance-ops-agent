"""Shared Gemini client: single lazily-created client, retry with exponential backoff."""
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DEFAULT_MODEL = "gemini-flash-lite-latest"
MAX_RETRIES = 4
BASE_DELAY_SECONDS = 3
TEMPERATURE = 0.2  # low but nonzero: consistent financial answers, not degenerate output

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set. Copy .env.example to .env and fill it in.")
        _client = genai.Client(api_key=api_key)
    return _client


def generate(prompt: str, model: str = DEFAULT_MODEL) -> str:
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = _get_client().models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=TEMPERATURE),
            )
            return response.text
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(BASE_DELAY_SECONDS * (2 ** attempt))
    raise RuntimeError(f"LLM call failed after {MAX_RETRIES} attempts: {last_error}")
