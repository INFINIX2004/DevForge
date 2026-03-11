from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models import (
    AnalyzeRequest, AnalyzeResponse,
    GenerateRequest, GenerateResponse,
)
from scraper import scrape_docs
from extractor import extract_api_info
from generator import generate_wrapper
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(
    title="DevForge API",
    description="Smart API Integration Tool — extract, analyze, and generate code from API docs",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened per-env if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for blocking Gemini/scrape calls
executor = ThreadPoolExecutor(max_workers=4)


def run_in_thread(fn, *args):
    """Run a blocking function in a thread pool so FastAPI stays async."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(executor, fn, *args)


@app.get("/")
def root():
    return {"status": "DevForge backend running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """Step 1: Scrape docs URL and extract structured API info using Gemini."""
    try:
        scraped = await run_in_thread(scrape_docs, req.url, True)

        if not scraped["content"]:
            raise HTTPException(
                status_code=422,
                detail=f"Could not scrape content from {req.url}. Check the URL and try again."
            )

        extracted = await run_in_thread(extract_api_info, scraped["content"], req.use_case)
        return AnalyzeResponse(success=True, extracted=extracted)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[/analyze] Error: {e}")
        return AnalyzeResponse(success=False, error=str(e))


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """Step 2: Generate wrapper class from extracted API info."""
    try:
        code = await run_in_thread(generate_wrapper, req.extracted, req.use_case, req.language)
        return GenerateResponse(success=True, code=code)
    except Exception as e:
        print(f"[/generate] Error: {e}")
        return GenerateResponse(success=False, error=str(e))


@app.post("/analyze-and-generate")
async def analyze_and_generate(req: AnalyzeRequest):
    """Combined pipeline: scrape → extract → generate in one call."""
    try:
        scraped = await run_in_thread(scrape_docs, req.url, True)
        if not scraped["content"]:
            return {"success": False, "error": f"Could not scrape content from {req.url}"}

        extracted = await run_in_thread(extract_api_info, scraped["content"], req.use_case)
        code = await run_in_thread(generate_wrapper, extracted, req.use_case, req.language)

        return {
            "success": True,
            "extracted": extracted.model_dump(),
            "code": code.model_dump(),
            "pages_scraped": scraped["pages_scraped"]
        }

    except Exception as e:
        print(f"[/analyze-and-generate] Error: {e}")
        return {"success": False, "error": str(e)}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": f"Internal server error: {str(exc)}"}
    )
