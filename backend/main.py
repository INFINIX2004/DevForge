from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models import AnalyzeRequest, AnalyzeResponse, GenerateRequest, GenerateResponse
from scraper import scrape_docs
from extractor import extract_api_info
from generator import generate_wrapper
from openapi_parser import detect_openapi, parse_openapi_spec
from sdk_detector import detect_sdk
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(
    title="DevForge API",
    description="Smart API Integration Tool",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=4)


def run_in_thread(fn, *args):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(executor, fn, *args)


@app.get("/")
def root():
    return {"status": "DevForge backend running", "version": "2.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    try:
        # Try OpenAPI first
        spec = await run_in_thread(detect_openapi, req.url)
        if spec:
            extracted = await run_in_thread(parse_openapi_spec, spec)
            extracted.source = "openapi"
        else:
            scraped = await run_in_thread(scrape_docs, req.url, True)
            if not scraped["content"]:
                raise HTTPException(status_code=422, detail=f"Could not scrape {req.url}")
            extracted = await run_in_thread(extract_api_info, scraped["content"], req.use_case)
            extracted.source = "llm"

        # SDK detection (non-blocking, best effort)
        try:
            sdk_info = await run_in_thread(detect_sdk, extracted.api_name, req.url)
            extracted.sdk_info = sdk_info
        except Exception:
            pass

        return AnalyzeResponse(success=True, extracted=extracted)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[/analyze] Error: {e}")
        return AnalyzeResponse(success=False, error=str(e))


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    try:
        code = await run_in_thread(generate_wrapper, req.extracted, req.use_case, req.language)
        return GenerateResponse(success=True, code=code)
    except Exception as e:
        print(f"[/generate] Error: {e}")
        return GenerateResponse(success=False, error=str(e))


@app.post("/analyze-and-generate")
async def analyze_and_generate(req: AnalyzeRequest):
    try:
        # Step 1: OpenAPI or scrape
        spec = await run_in_thread(detect_openapi, req.url)
        if spec:
            print("[main] OpenAPI spec detected — skipping LLM extraction")
            extracted = await run_in_thread(parse_openapi_spec, spec)
            extracted.source = "openapi"
            pages_scraped = 0
        else:
            scraped = await run_in_thread(scrape_docs, req.url, True)
            if not scraped["content"]:
                return {"success": False, "error": f"Could not scrape {req.url}"}
            extracted = await run_in_thread(extract_api_info, scraped["content"], req.use_case)
            extracted.source = "llm"
            pages_scraped = scraped["pages_scraped"]

        # Step 2: SDK detection
        try:
            sdk_info = await run_in_thread(detect_sdk, extracted.api_name, req.url)
            extracted.sdk_info = sdk_info
        except Exception:
            sdk_info = None

        # Step 3: Generate code
        code = await run_in_thread(generate_wrapper, extracted, req.use_case, req.language)

        return {
            "success": True,
            "extracted": extracted.model_dump(),
            "code": code.model_dump(),
            "pages_scraped": pages_scraped,
            "source": extracted.source,
        }

    except Exception as e:
        print(f"[/analyze-and-generate] Error: {e}")
        return {"success": False, "error": str(e)}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc)}
    )
