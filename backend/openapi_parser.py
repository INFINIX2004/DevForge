"""
OpenAPI / Swagger Parser
Detects if a URL points to or contains an OpenAPI spec.
If found, parses it directly — no LLM needed for extraction.
Supports: swagger.json, openapi.yaml, swagger.yaml, openapi.json
Also detects spec links embedded in HTML doc pages.
"""

import re
import json
import requests
import yaml
from urllib.parse import urljoin, urlparse
from models import ExtractedAPI, AuthInfo, Endpoint, EndpointParam

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
}

# Common OpenAPI spec paths to probe
SPEC_PATHS = [
    "/openapi.json", "/openapi.yaml", "/openapi.yml",
    "/swagger.json", "/swagger.yaml", "/swagger.yml",
    "/api/openapi.json", "/api/swagger.json",
    "/api-docs", "/api-docs.json",
    "/v1/openapi.json", "/v2/openapi.json", "/v3/openapi.json",
    "/docs/openapi.json", "/spec/openapi.json",
]

# Patterns to find spec URLs embedded in HTML
SPEC_LINK_PATTERNS = [
    r'["\'](https?://[^"\']+(?:openapi|swagger)\.(?:json|yaml|yml))["\']',
    r'url:\s*["\']([^"\']+(?:openapi|swagger)[^"\']*)["\']',
    r'href=["\']([^"\']+(?:openapi|swagger)\.(?:json|yaml|yml))["\']',
]

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}


def _fetch(url: str) -> tuple[str | None, str]:
    """Fetch URL, return (content, content_type)."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        ct = r.headers.get("content-type", "")
        return r.text, ct
    except Exception:
        return None, ""


def _parse_spec(text: str, url: str) -> dict | None:
    """Try to parse text as JSON or YAML OpenAPI spec."""
    # Try JSON
    try:
        data = json.loads(text)
        if _is_openapi(data):
            return data
    except json.JSONDecodeError:
        pass
    # Try YAML
    try:
        data = yaml.safe_load(text)
        if isinstance(data, dict) and _is_openapi(data):
            return data
    except yaml.YAMLError:
        pass
    return None


def _is_openapi(data: dict) -> bool:
    """Check if dict looks like an OpenAPI/Swagger spec."""
    if not isinstance(data, dict):
        return False
    return (
        "openapi" in data or
        "swagger" in data or
        ("paths" in data and "info" in data)
    )


def detect_openapi(url: str) -> dict | None:
    """
    Try to find and fetch an OpenAPI spec for the given URL.
    Returns raw spec dict if found, None otherwise.
    """
    # 1. Direct URL — maybe it IS the spec
    content, ct = _fetch(url)
    if content:
        spec = _parse_spec(content, url)
        if spec:
            print(f"[openapi] Direct spec found at {url}")
            return spec

        # 2. Scan HTML for embedded spec URLs
        for pattern in SPEC_LINK_PATTERNS:
            matches = re.findall(pattern, content)
            for match in matches:
                spec_url = urljoin(url, match)
                spec_content, _ = _fetch(spec_url)
                if spec_content:
                    spec = _parse_spec(spec_content, spec_url)
                    if spec:
                        print(f"[openapi] Spec found via HTML link: {spec_url}")
                        return spec

    # 3. Probe common spec paths on the same domain
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    for path in SPEC_PATHS:
        spec_url = base + path
        spec_content, _ = _fetch(spec_url)
        if spec_content:
            spec = _parse_spec(spec_content, spec_url)
            if spec:
                print(f"[openapi] Spec found at probed path: {spec_url}")
                return spec

    return None


def _extract_auth(spec: dict) -> AuthInfo:
    """Extract auth info from OpenAPI securitySchemes."""
    components = spec.get("components", {})
    security_schemes = components.get("securitySchemes", {})

    # Also check Swagger 2.0 securityDefinitions
    if not security_schemes:
        security_schemes = spec.get("securityDefinitions", {})

    if not security_schemes:
        return AuthInfo(type="none", header=None, description="No authentication required")

    # Take the first scheme
    name, scheme = next(iter(security_schemes.items()))

    scheme_type = scheme.get("type", "").lower()
    if scheme_type == "apikey":
        location = scheme.get("in", "header")
        header_name = scheme.get("name", "X-API-Key")
        return AuthInfo(
            type="api_key",
            header=header_name if location == "header" else None,
            description=f"API key passed via {location} as '{header_name}'"
        )
    elif scheme_type == "http":
        http_scheme = scheme.get("scheme", "bearer").lower()
        return AuthInfo(
            type="bearer" if http_scheme == "bearer" else "basic",
            header="Authorization",
            description=f"HTTP {http_scheme.capitalize()} authentication via Authorization header"
        )
    elif scheme_type == "oauth2":
        return AuthInfo(
            type="oauth",
            header="Authorization",
            description="OAuth 2.0 — obtain access token and pass as Bearer in Authorization header"
        )
    else:
        return AuthInfo(
            type="api_key",
            header="Authorization",
            description=scheme.get("description", f"Authentication via {name}")
        )


def _extract_endpoints(spec: dict, max_endpoints: int = 10) -> list[Endpoint]:
    """Extract endpoints from OpenAPI paths."""
    paths = spec.get("paths", {})
    endpoints = []

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                continue

            # Description
            description = (
                operation.get("summary") or
                operation.get("description") or
                f"{method.upper()} {path}"
            )
            if len(description) > 120:
                description = description[:120] + "..."

            # Parameters
            params = []
            for param in operation.get("parameters", []):
                if not isinstance(param, dict):
                    continue
                schema = param.get("schema", {})
                param_type = schema.get("type", "string") if schema else "string"
                params.append(EndpointParam(
                    name=param.get("name", "param"),
                    type=param_type,
                    required=param.get("required", False),
                    description=param.get("description", "")[:100]
                ))

            # Request body params
            req_body = operation.get("requestBody", {})
            if req_body:
                content = req_body.get("content", {})
                for media_type, media in content.items():
                    schema = media.get("schema", {})
                    properties = schema.get("properties", {})
                    required_fields = schema.get("required", [])
                    for prop_name, prop_schema in list(properties.items())[:4]:
                        params.append(EndpointParam(
                            name=prop_name,
                            type=prop_schema.get("type", "string"),
                            required=prop_name in required_fields,
                            description=prop_schema.get("description", "")[:80]
                        ))
                    break  # only first media type

            endpoints.append(Endpoint(
                method=method.upper(),
                path=path,
                description=description,
                params=params[:6]  # cap params per endpoint
            ))

            if len(endpoints) >= max_endpoints:
                return endpoints

    return endpoints


def parse_openapi_spec(spec: dict) -> ExtractedAPI:
    """Convert raw OpenAPI spec dict into ExtractedAPI model."""
    info = spec.get("info", {})
    api_name = info.get("title", "API")
    description = info.get("description", "")

    # Base URL
    servers = spec.get("servers", [])
    if servers and isinstance(servers[0], dict):
        base_url = servers[0].get("url", "")
    else:
        # Swagger 2.0
        host = spec.get("host", "")
        base_path = spec.get("basePath", "/")
        scheme = (spec.get("schemes") or ["https"])[0]
        base_url = f"{scheme}://{host}{base_path}" if host else ""

    if not base_url:
        base_url = "https://api.example.com"

    version = info.get("version", "")
    raw_summary = f"{api_name} v{version}. {description}"[:300] if description else f"{api_name} API"

    auth = _extract_auth(spec)
    endpoints = _extract_endpoints(spec)

    print(f"[openapi] Parsed: {api_name} | {len(endpoints)} endpoints | auth: {auth.type}")

    return ExtractedAPI(
        api_name=api_name,
        base_url=base_url.rstrip("/"),
        auth=auth,
        endpoints=endpoints,
        raw_summary=raw_summary
    )
