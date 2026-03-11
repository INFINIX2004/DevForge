import json
import re
from llm_client import generate
from models import ExtractedAPI, AuthInfo, Endpoint, EndpointParam

# Lean prompt — fewer tokens in = more free tier headroom
EXTRACT_PROMPT = """Extract API info from this documentation. Reply ONLY with JSON, no extra text.

JSON format:
{{"api_name":"string","base_url":"string","auth":{{"type":"api_key|oauth|bearer|basic|none","header":"string or null","description":"string"}},"endpoints":[{{"method":"GET|POST|PUT|DELETE|PATCH","path":"string","description":"string","params":[{{"name":"string","type":"string","required":true,"description":"string"}}]}}],"raw_summary":"string"}}

Rules: max 8 endpoints, all fields required, guess base_url from domain if missing.

Use case: {use_case}

Docs:
{content}"""


def extract_json(text: str) -> dict:
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
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not parse JSON from response:\n{text[:300]}")


def extract_api_info(scraped_content: str, use_case: str) -> ExtractedAPI:
    prompt = EXTRACT_PROMPT.format(use_case=use_case, content=scraped_content)
    print(f"[extractor] Prompt size: {len(prompt)} chars")

    raw_text, provider = generate(prompt, temperature=0.1, max_tokens=2048)
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
            EndpointParam(name=p["name"], type=p["type"],
                         required=p["required"], description=p["description"])
            for p in ep.get("params", [])
        ]
        endpoints.append(Endpoint(
            method=ep["method"], path=ep["path"],
            description=ep["description"], params=params
        ))

    return ExtractedAPI(
        api_name=data["api_name"], base_url=data["base_url"],
        auth=auth, endpoints=endpoints, raw_summary=data["raw_summary"]
    )
