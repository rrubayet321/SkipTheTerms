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

# Allow all origins so the Chrome extension can reach this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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

    if not url:
        raise HTTPException(status_code=400, detail="A URL is required.")
    if not text:
        raise HTTPException(status_code=400, detail="Terms text cannot be empty.")

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
