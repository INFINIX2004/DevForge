import json
import re
from llm_client import generate
from models import ExtractedAPI, AuthInfo, Endpoint, EndpointParam

EXTRACT_PROMPT = """
You are an expert API analyst. Below is the scraped content of an API documentation website.

Your job is to extract structured information from it.

Respond ONLY with a valid JSON object. No markdown, no explanation, no code fences.

JSON schema to follow exactly:
{{
  "api_name": "string — name of the API",
  "base_url": "string — base URL like https://api.example.com/v1",
  "auth": {{
    "type": "one of: api_key | oauth | bearer | basic | none",
    "header": "string — header name like Authorization or X-API-Key, or null",
    "description": "string — brief explanation of how auth works"
  }},
  "endpoints": [
    {{
      "method": "GET | POST | PUT | DELETE | PATCH",
      "path": "string — like /users or /payments/{{id}}",
      "description": "string — what this endpoint does",
      "params": [
        {{
          "name": "string",
          "type": "string | integer | boolean | object | array",
          "required": true or false,
          "description": "string"
        }}
      ]
    }}
  ],
  "raw_summary": "string — 2-3 sentence plain English summary of this API and what it does"
}}

Rules:
- Include up to 10 most important endpoints only
- If you cannot find a base URL, make a reasonable guess from the domain
- If auth type is unclear, use "api_key" as default
- Endpoints array must have at least 1 item
- Every field is required

Use case context (what the user wants to build): {use_case}

--- DOCUMENTATION CONTENT BELOW ---
{content}
"""


def extract_json(text: str) -> dict:
    """Robustly extract JSON from model response."""
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from model response:\n{text[:500]}")


def extract_api_info(scraped_content: str, use_case: str) -> ExtractedAPI:
    """Send scraped docs to LLM and return structured ExtractedAPI."""
    prompt = EXTRACT_PROMPT.format(use_case=use_case, content=scraped_content)

    print("[extractor] Sending to LLM for extraction...")
    raw_text, provider = generate(prompt, temperature=0.1, max_tokens=4096)
    print(f"[extractor] Got response from {provider} ({len(raw_text)} chars)")

    data = extract_json(raw_text)

    auth = AuthInfo(
        type=data["auth"]["type"],
        header=data["auth"].get("header"),
        description=data["auth"]["description"]
    )

    endpoints = []
    for ep in data.get("endpoints", []):
        params = [
            EndpointParam(
                name=p["name"],
                type=p["type"],
                required=p["required"],
                description=p["description"]
            )
            for p in ep.get("params", [])
        ]
        endpoints.append(Endpoint(
            method=ep["method"],
            path=ep["path"],
            description=ep["description"],
            params=params
        ))

    return ExtractedAPI(
        api_name=data["api_name"],
        base_url=data["base_url"],
        auth=auth,
        endpoints=endpoints,
        raw_summary=data["raw_summary"]
    )
