import logging
import os
import time
from typing import Optional

from dotenv import load_dotenv
from google import genai
from groq import Groq

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "800"))

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class LLMError(RuntimeError):
    """Raised when every available LLM provider fails."""


def _is_rate_limit(error: Exception) -> bool:
    msg = str(error).lower()
    return (
        "rate_limit" in msg
        or "rate limit" in msg
        or "429" in msg
        or "quota" in msg
        or "resource_exhausted" in msg
    )


def _llm_call_groq(prompt: str, system: str, max_tokens: int) -> str:
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=TEMPERATURE,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def _llm_call_gemini(prompt: str, system: str, max_tokens: int) -> str:
    full_prompt = f"{system}\n\n{prompt}"
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=full_prompt,
        config={"max_output_tokens": max_tokens},
    )
    return response.text


def llm_call(
    prompt: str,
    system: str = "You are a helpful historical analysis assistant.",
    *,
    max_tokens: Optional[int] = None,
) -> str:
    """Call the primary LLM (Groq) with a Gemini fallback on rate limits or errors.

    Retries each provider once on rate-limit, then gives up with ``LLMError``.

    ``max_tokens`` overrides the global ``LLM_MAX_TOKENS`` ceiling for this call.
    Tight per-call budgets are the cheapest way to keep token usage down.
    """

    budget = max_tokens if max_tokens is not None else MAX_TOKENS
    last_error: Exception | None = None

    for attempt in range(2):
        try:
            return _llm_call_groq(prompt, system, budget)
        except Exception as exc:
            last_error = exc
            if _is_rate_limit(exc) and attempt == 0:
                logger.warning("Groq rate limited, retrying in 5s")
                time.sleep(5)
                continue
            logger.warning("Groq failed (%s), falling back to Gemini", exc)
            break

    for attempt in range(2):
        try:
            return _llm_call_gemini(prompt, system, budget)
        except Exception as exc:
            last_error = exc
            if _is_rate_limit(exc) and attempt == 0:
                logger.warning("Gemini rate limited, retrying in 10s")
                time.sleep(10)
                continue
            logger.error("Gemini failed (%s)", exc)
            break

    raise LLMError(f"All LLM providers failed; last error: {last_error}") from last_error
