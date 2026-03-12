"""
SDK Detector
Checks if an official SDK already exists for a given API.
Uses LLM to reason about it — fast, single prompt.
"""

from llm_client import generate

SDK_PROMPT = """You are a developer tools expert. Given this API name and URL, check if an official SDK exists.

API Name: {api_name}
URL: {url}

Reply ONLY with JSON:
{{"has_sdk": true or false, "sdks": [{{"language": "Python", "package": "stripe", "install": "pip install stripe", "docs": "https://..."}}], "note": "short explanation"}}

Rules:
- Only include OFFICIAL SDKs (maintained by the API provider)
- Include Python and JavaScript SDKs if they exist
- If no official SDK exists, return has_sdk: false and empty sdks array
- Be accurate — only list SDKs you are confident exist
"""


def detect_sdk(api_name: str, url: str) -> dict:
    """
    Returns SDK info dict:
    { has_sdk: bool, sdks: [...], note: str }
    """
    import json, re

    prompt = SDK_PROMPT.format(api_name=api_name, url=url)
    try:
        text, _ = generate(prompt, temperature=0.1, max_tokens=512)
        # Parse JSON from response
        text = text.strip()
        text = re.sub(r'^```(?:json)?\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
    except Exception as e:
        print(f"[sdk_detector] Failed: {e}")

    return {"has_sdk": False, "sdks": [], "note": "Could not determine SDK availability"}
