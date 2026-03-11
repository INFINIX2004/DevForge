from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import (
    AnalyzeRequest, AnalyzeResponse,
    GenerateRequest, GenerateResponse,
)
from scraper import scrape_docs
from extractor import extract_api_info
from generator import generate_wrapper

app = FastAPI(
    title="DevForge API",
    description="Smart API Integration Tool — extracts, analyzes, and generates code from API docs",
    version="1.0.0"
)

# Allow React frontend (localhost:5173 for Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "DevForge backend running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    """
    Step 1: Scrape the docs URL and extract structured API info using Gemini.
    """
    try:
        # Scrape docs
        scraped = scrape_docs(req.url, recursive=True)

        if not scraped["content"]:
            raise HTTPException(
                status_code=422,
                detail=f"Could not scrape content from {req.url}. Check the URL and try again."
            )

        # Extract structured info via Gemini
        extracted = extract_api_info(scraped["content"], req.use_case)

        return AnalyzeResponse(success=True, extracted=extracted)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[/analyze] Error: {e}")
        return AnalyzeResponse(success=False, error=str(e))


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    """
    Step 2: Generate a wrapper class in the target language from extracted API info.
    """
    try:
        code = generate_wrapper(req.extracted, req.use_case, req.language)
        return GenerateResponse(success=True, code=code)

    except Exception as e:
        print(f"[/generate] Error: {e}")
        return GenerateResponse(success=False, error=str(e))


@app.post("/analyze-and-generate")
def analyze_and_generate(req: AnalyzeRequest):
    """
    Combined endpoint: scrape → extract → generate in one call.
    Useful for the frontend to do everything in a single request.
    """
    try:
        # Step 1: Scrape
        scraped = scrape_docs(req.url, recursive=True)
        if not scraped["content"]:
            return {
                "success": False,
                "error": f"Could not scrape content from {req.url}"
            }

        # Step 2: Extract
        extracted = extract_api_info(scraped["content"], req.use_case)

        # Step 3: Generate
        code = generate_wrapper(extracted, req.use_case, req.language)

        return {
            "success": True,
            "extracted": extracted.model_dump(),
            "code": code.model_dump(),
            "pages_scraped": scraped["pages_scraped"]
        }

    except Exception as e:
        print(f"[/analyze-and-generate] Error: {e}")
        return {"success": False, "error": str(e)}
