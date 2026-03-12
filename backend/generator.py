import re
from llm_client import generate
from models import ExtractedAPI, GeneratedCode

SUPPORTED_LANGUAGES = ["python", "javascript", "typescript", "curl"]

PYTHON_PROMPT = """You are a senior Python engineer. Generate a clean Python wrapper class.

API: {api_name} | Base: {base_url} | Auth: {auth_type} via {auth_header}
Use case: {use_case}

Endpoints:
{endpoints}

Requirements: requests library, class {class_name}Client, constructor takes api_key,
type hints, docstrings, try/except error handling, return parsed JSON.
After the class write: # Example usage
ONLY Python code, no markdown fences."""

JS_PROMPT = """You are a senior JavaScript engineer. Generate a clean JS wrapper class.

API: {api_name} | Base: {base_url} | Auth: {auth_type} via {auth_header}
Use case: {use_case}

Endpoints:
{endpoints}

Requirements: fetch API only, class {class_name}Client, constructor takes apiKey,
async methods, JSDoc comments, try/catch error handling, return parsed JSON.
After the class write: // Example usage
ONLY JavaScript code, no markdown fences."""

TS_PROMPT = """You are a senior TypeScript engineer. Generate a clean TypeScript wrapper class.

API: {api_name} | Base: {base_url} | Auth: {auth_type} via {auth_header}
Use case: {use_case}

Endpoints:
{endpoints}

Requirements: fetch API only, typed interfaces for request/response, class {class_name}Client,
constructor takes apiKey: string, async methods, JSDoc, try/catch, generics where appropriate.
After the class write: // Example usage
ONLY TypeScript code, no markdown fences."""

CURL_PROMPT = """You are a developer advocate. Generate practical curl examples for this API.

API: {api_name} | Base: {base_url} | Auth: {auth_type} via {auth_header}
Use case: {use_case}

Endpoints:
{endpoints}

Write one curl command per endpoint with a comment above explaining what it does.
Use realistic placeholder values and proper auth headers.
ONLY shell commands and # comments, no markdown fences."""

PROMPT_MAP = {
    "python": PYTHON_PROMPT,
    "javascript": JS_PROMPT,
    "typescript": TS_PROMPT,
    "curl": CURL_PROMPT,
}

EXAMPLE_MARKERS = {
    "python":     ["# Example usage", "if __name__", "# Usage"],
    "javascript": ["// Example usage", "// Usage"],
    "typescript": ["// Example usage", "// Usage"],
    "curl":       [],
}


def format_endpoints(extracted: ExtractedAPI) -> str:
    lines = []
    for ep in extracted.endpoints:
        lines.append(f"  {ep.method} {ep.path} — {ep.description}")
        for p in ep.params[:3]:
            req = "required" if p.required else "optional"
            lines.append(f"    • {p.name} ({p.type}, {req})")
    return "\n".join(lines)


def make_class_name(api_name: str) -> str:
    words = re.sub(r"[^a-zA-Z0-9 ]", " ", api_name).split()
    return "".join(w.capitalize() for w in words if w)


def generate_wrapper(extracted: ExtractedAPI, use_case: str, language: str) -> GeneratedCode:
    if language not in SUPPORTED_LANGUAGES:
        language = "python"

    class_name = make_class_name(extracted.api_name)
    prompt = PROMPT_MAP[language].format(
        api_name=extracted.api_name,
        base_url=extracted.base_url,
        auth_type=extracted.auth.type,
        auth_header=extracted.auth.header or "Authorization",
        use_case=use_case,
        endpoints=format_endpoints(extracted),
        class_name=class_name,
    )

    print(f"[generator] Generating {language} for {extracted.api_name}...")
    full_code, provider = generate(prompt, temperature=0.3, max_tokens=4096)
    print(f"[generator] Done via {provider} ({len(full_code)} chars)")

    full_code = full_code.strip()
    full_code = re.sub(r"^```[a-z]*\n?", "", full_code)
    full_code = re.sub(r"\n?```$", "", full_code)

    wrapper_class = full_code
    usage_example = ""

    for marker in EXAMPLE_MARKERS.get(language, []):
        idx = full_code.find(marker)
        if idx != -1:
            wrapper_class = full_code[:idx].strip()
            usage_example = full_code[idx:].strip()
            break

    if not usage_example:
        if language == "python":
            usage_example = f"# Example usage\nclient = {class_name}Client(api_key='YOUR_KEY')"
        elif language in ("javascript", "typescript"):
            usage_example = f"// Example usage\nconst client = new {class_name}Client('YOUR_KEY');"
        else:
            usage_example = "# Replace YOUR_API_KEY with your actual key"

    return GeneratedCode(language=language, wrapper_class=wrapper_class, usage_example=usage_example)
