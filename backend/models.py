from pydantic import BaseModel
from typing import Optional

class AnalyzeRequest(BaseModel):
    url: str
    use_case: str
    language: str = "python"  # python | javascript | typescript | curl

class EndpointParam(BaseModel):
    name: str
    type: str
    required: bool
    description: str

class Endpoint(BaseModel):
    method: str
    path: str
    description: str
    params: list[EndpointParam] = []

class AuthInfo(BaseModel):
    type: str
    header: Optional[str] = None
    description: str

class SDKInfo(BaseModel):
    language: str
    package: str
    install: str
    docs: str

class ExtractedAPI(BaseModel):
    api_name: str
    base_url: str
    auth: AuthInfo
    endpoints: list[Endpoint]
    raw_summary: str
    source: str = "llm"           # "llm" | "openapi"
    sdk_info: Optional[dict] = None

class GenerateRequest(BaseModel):
    extracted: ExtractedAPI
    use_case: str
    language: str = "python"

class GeneratedCode(BaseModel):
    language: str
    wrapper_class: str
    usage_example: str

class AnalyzeResponse(BaseModel):
    success: bool
    extracted: Optional[ExtractedAPI] = None
    error: Optional[str] = None

class GenerateResponse(BaseModel):
    success: bool
    code: Optional[GeneratedCode] = None
    error: Optional[str] = None
