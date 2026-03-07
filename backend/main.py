from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import supabase
from groq_service import summarize_terms

app = FastAPI(
    title="SkipTheTerms API",
    description="Summarizes Terms of Service pages so you don't have to suffer.",
    version="1.0.0",
)

# Allow all origins so the Chrome extension can reach this server.
# allow_credentials must be False when allow_origins=["*"] — the CORS spec
# forbids credentialed requests with a wildcard origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Request / Response models
# -------------------------------------------------------------------

class SummarizeRequest(BaseModel):
    url: str
    text: str  # The raw legal text scraped by the extension


class SummarizeResponse(BaseModel):
    url: str
    summary: str
    cached: bool


class RateRequest(BaseModel):
    url: str
    vote: str  # "up" or "down"


class RateResponse(BaseModel):
    url: str
    thumbs_up: int
    thumbs_down: int


# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------

@app.get("/")
def health_check():
    return {"status": "ok", "message": "SkipTheTerms backend is running."}


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    url = request.url.strip()
    text = request.text.strip()

    MAX_TEXT_LENGTH = 50_000  # ~10x the LLM window; guards against abusive payloads

    if not url:
        raise HTTPException(status_code=400, detail="A URL is required.")
    if not text:
        raise HTTPException(status_code=400, detail="Terms text cannot be empty.")
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Text payload exceeds the {MAX_TEXT_LENGTH:,} character limit.",
        )

    # 1. Check the cache first
    try:
        cache_result = (
            supabase.table("termscache")
            .select("summary")
            .eq("url", url)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database lookup failed: {str(e)}")

    if cache_result.data:
        # Cache hit — return the stored summary
        return SummarizeResponse(
            url=url,
            summary=cache_result.data[0]["summary"],
            cached=True,
        )

    # 2. Cache miss — call Groq
    try:
        summary = summarize_terms(text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq API call failed: {str(e)}")

    # 3. Save the result to Supabase
    try:
        supabase.table("termscache").insert({"url": url, "summary": summary}).execute()
    except Exception as e:
        # Non-fatal: return the summary even if caching fails
        print(f"Warning: failed to cache result for {url}: {e}")

    return SummarizeResponse(url=url, summary=summary, cached=False)


@app.post("/rate", response_model=RateResponse)
async def rate(request: RateRequest):
    url = request.url.strip()
    vote = request.vote.strip().lower()

    if not url:
        raise HTTPException(status_code=400, detail="A URL is required.")
    if vote not in ("up", "down"):
        raise HTTPException(status_code=400, detail="vote must be 'up' or 'down'.")

    column = "thumbs_up" if vote == "up" else "thumbs_down"

    # Fetch the current row
    try:
        fetch_result = (
            supabase.table("termscache")
            .select("thumbs_up, thumbs_down")
            .eq("url", url)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database lookup failed: {str(e)}")

    if not fetch_result.data:
        raise HTTPException(status_code=404, detail="No cached entry found for this URL.")

    row = fetch_result.data[0]
    new_value = (row.get(column) or 0) + 1

    # Write the incremented value back
    try:
        update_result = (
            supabase.table("termscache")
            .update({column: new_value})
            .eq("url", url)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database update failed: {str(e)}")

    updated_row = update_result.data[0] if update_result.data else {}
    return RateResponse(
        url=url,
        thumbs_up=updated_row.get("thumbs_up", row.get("thumbs_up") or 0),
        thumbs_down=updated_row.get("thumbs_down", row.get("thumbs_down") or 0),
    )
