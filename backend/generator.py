import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from models import ExtractedAPI, GeneratedCode

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro")


PYTHON_PROMPT = """
You are a senior Python engineer. Generate a clean, production-ready Python wrapper class for this API.

API Details:
- Name: {api_name}
- Base URL: {base_url}
- Auth Type: {auth_type}
- Auth Header: {auth_header}
- Auth Description: {auth_description}

Endpoints to implement:
{endpoints_list}

Use case the user wants to build: {use_case}

Requirements:
1. Use the `requests` library
2. Class name should be {class_name}Client
3. Constructor takes api_key as parameter
4. Each endpoint becomes a method
5. Include proper docstrings
6. Handle errors with try/except, raise descriptive exceptions
7. Return parsed JSON responses
8. Include type hints

After the class, write a short usage example showing how to use it for: {use_case}

Respond with ONLY the Python code. No markdown fences, no explanation.
"""


JS_PROMPT = """
You are a senior JavaScript engineer. Generate a clean, modern JavaScript wrapper class for this API.

API Details:
- Name: {api_name}
- Base URL: {base_url}
- Auth Type: {auth_type}
- Auth Header: {auth_header}
- Auth Description: {auth_description}

Endpoints to implement:
{endpoints_list}

Use case the user wants to build: {use_case}

Requirements:
1. Use fetch API (no external dependencies)
2. Class name should be {class_name}Client
3. Constructor takes apiKey as parameter
4. Each endpoint becomes an async method
5. Include JSDoc comments
6. Handle errors with try/catch, throw descriptive errors
7. Return parsed JSON responses

After the class, write a short usage example showing how to use it for: {use_case}

Respond with ONLY the JavaScript code. No markdown fences, no explanation.
"""


def format_endpoints_list(extracted: ExtractedAPI) -> str:
    """Format endpoints into a readable list for the prompt."""
    lines = []
    for ep in extracted.endpoints:
        lines.append(f"  {ep.method} {ep.path} — {ep.description}")
        for p in ep.params:
            req = "required" if p.required else "optional"
            lines.append(f"    • {p.name} ({p.type}, {req}): {p.description}")
    return "\n".join(lines)


def make_class_name(api_name: str) -> str:
    """Convert API name to PascalCase class name."""
    words = re.sub(r"[^a-zA-Z0-9 ]", " ", api_name).split()
    return "".join(w.capitalize() for w in words if w)


def generate_wrapper(extracted: ExtractedAPI, use_case: str, language: str) -> GeneratedCode:
    """
    Generate a wrapper class for the given extracted API info.
    Supports 'python' and 'javascript'.
    """
    class_name = make_class_name(extracted.api_name)
    endpoints_list = format_endpoints_list(extracted)

    template_vars = dict(
        api_name=extracted.api_name,
        base_url=extracted.base_url,
        auth_type=extracted.auth.type,
        auth_header=extracted.auth.header or "Authorization",
        auth_description=extracted.auth.description,
        endpoints_list=endpoints_list,
        use_case=use_case,
        class_name=class_name,
    )

    if language == "javascript":
        prompt = JS_PROMPT.format(**template_vars)
    else:
        prompt = PYTHON_PROMPT.format(**template_vars)

    print(f"[generator] Generating {language} wrapper for {extracted.api_name}...")
    response = model.generate_content(prompt)
    full_code = response.text.strip()

    # Strip accidental code fences if model adds them
    full_code = re.sub(r"^```[a-z]*\n?", "", full_code)
    full_code = re.sub(r"\n?```$", "", full_code)

    # Split wrapper class from usage example
    # Look for common usage example separators
    split_markers = [
        "# Example usage",
        "# Usage example",
        "# Usage:",
        "# Example:",
        "// Example usage",
        "// Usage example",
        "// Usage:",
        "if __name__",
    ]

    wrapper_class = full_code
    usage_example = ""

    for marker in split_markers:
        idx = full_code.find(marker)
        if idx != -1:
            wrapper_class = full_code[:idx].strip()
            usage_example = full_code[idx:].strip()
            break

    if not usage_example:
        usage_example = f"# See the class above for usage\nclient = {class_name}Client(api_key='YOUR_KEY')"

    print(f"[generator] Done. Wrapper: {len(wrapper_class)} chars")

    return GeneratedCode(
        language=language,
        wrapper_class=wrapper_class,
        usage_example=usage_example
    )
