"""
LLM Client with automatic fallback: Gemini → OpenAI
- Tries Gemini first (cheaper, faster)
- Falls back to OpenAI gpt-4o-mini on 429/quota errors
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

_gemini_client = None
_openai_client = None


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
        # Pass explicit httpx client to avoid proxies kwarg conflict
        # between openai SDK and httpx>=0.28
        _openai_client = OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=httpx.Client(
                timeout=60.0,
                follow_redirects=True,
            )
        )
    return _openai_client


def _is_quota_error(e: Exception) -> bool:
    msg = str(e).lower()
    return any(kw in msg for kw in [
        "429", "quota", "rate_limit", "resource_exhausted",
        "rate limit", "too many requests"
    ])


def generate(
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 8192,
) -> tuple[str, str]:
    """
    Generate text with automatic Gemini → OpenAI fallback.
    Returns (response_text, provider_used)
    """
    # ── Try Gemini first ──────────────────────────────────────────
    gemini = _get_gemini()
    if gemini:
        try:
            from google.genai import types
            response = gemini.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            print("[llm] Used: Gemini 2.0 Flash")
            return response.text, "gemini"
        except Exception as e:
            if _is_quota_error(e):
                print(f"[llm] Gemini quota hit, falling back to OpenAI...")
            else:
                print(f"[llm] Gemini error ({e}), falling back to OpenAI...")
    else:
        print("[llm] No Gemini key found, trying OpenAI...")

    # ── Fallback: OpenAI ─────────────────────────────────────────
    openai_client = _get_openai()
    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            print("[llm] Used: OpenAI gpt-4o-mini")
            return response.choices[0].message.content, "openai"
        except Exception as e:
            raise RuntimeError(f"OpenAI failed: {e}")

    raise RuntimeError(
        "No LLM available. Add GEMINI_API_KEY and/or OPENAI_API_KEY to backend/.env"
    )
