from pydantic import BaseModel
from typing import Optional


class AnalyzeRequest(BaseModel):
    url: str
    use_case: str
    language: str = "python"  # python | javascript


class EndpointParam(BaseModel):
    name: str
    type: str
    required: bool
    description: str


class Endpoint(BaseModel):
    method: str        # GET, POST, etc.
    path: str
    description: str
    params: list[EndpointParam] = []


class AuthInfo(BaseModel):
    type: str          # api_key | oauth | bearer | basic | none
    header: Optional[str] = None
    description: str


class ExtractedAPI(BaseModel):
    api_name: str
    base_url: str
    auth: AuthInfo
    endpoints: list[Endpoint]
    raw_summary: str


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
