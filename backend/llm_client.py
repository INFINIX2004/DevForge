"""
LLM Client — priority chain: Gemini → OpenAI → Groq (free)
Get a free Groq key at console.groq.com (takes 30 seconds)
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

_gemini_client = None
_openai_client = None
_groq_client   = None

GEMINI_MODEL = "gemini-1.5-flash-latest"
OPENAI_MODEL = "gpt-4o-mini"
GROQ_MODEL   = "llama-3.3-70b-versatile"   # free, fast, great at JSON + code


def _get_gemini():
    global _gemini_client
    if _gemini_client is None and GEMINI_API_KEY:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


def _get_openai():
    global _openai_client
    if _openai_client is None and OPENAI_API_KEY:
        from openai import OpenAI
        _openai_client = OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=httpx.Client(timeout=60.0, follow_redirects=True)
        )
    return _openai_client


def _get_groq():
    global _groq_client
    if _groq_client is None and GROQ_API_KEY:
        from groq import Groq
        _groq_client = Groq(
            api_key=GROQ_API_KEY,
            http_client=httpx.Client(timeout=60.0, follow_redirects=True)
        )
    return _groq_client


def _is_quota_error(e: Exception) -> bool:
    msg = str(e).lower()
    return any(kw in msg for kw in [
        "429", "quota", "rate_limit", "resource_exhausted",
        "rate limit", "too many requests", "insufficient_quota",
        "not_found", "404"
    ])


def generate(
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> tuple[str, str]:
    """
    Generate text — tries Gemini, then OpenAI, then Groq.
    Returns (response_text, provider_used)
    """

    # ── 1. Gemini ─────────────────────────────────────────────────
    gemini = _get_gemini()
    if gemini:
        try:
            from google.genai import types
            response = gemini.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            print(f"[llm] Used: {GEMINI_MODEL}")
            return response.text, "gemini"
        except Exception as e:
            print(f"[llm] Gemini failed ({type(e).__name__}), trying OpenAI...")

    # ── 2. OpenAI ─────────────────────────────────────────────────
    openai_client = _get_openai()
    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            print(f"[llm] Used: {OPENAI_MODEL}")
            return response.choices[0].message.content, "openai"
        except Exception as e:
            print(f"[llm] OpenAI failed ({type(e).__name__}), trying Groq...")

    # ── 3. Groq (free fallback) ───────────────────────────────────
    groq_client = _get_groq()
    if groq_client:
        try:
            response = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            print(f"[llm] Used: Groq {GROQ_MODEL}")
            return response.choices[0].message.content, "groq"
        except Exception as e:
            raise RuntimeError(f"Groq failed: {e}")

    raise RuntimeError(
        "No LLM available. Add at least one key to backend/.env:\n"
        "  GEMINI_API_KEY  → aistudio.google.com\n"
        "  OPENAI_API_KEY  → platform.openai.com\n"
        "  GROQ_API_KEY    → console.groq.com  (FREE)"
    )
