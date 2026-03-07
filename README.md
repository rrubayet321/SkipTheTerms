# SkipTheTerms

A browser extension and backend service designed to automatically read, analyze, and summarize complex Terms of Service (ToS) agreements into readable, concise bullet points using Large Language Models.

## Overview

Reading Terms of Service is often tedious and time-consuming, leading many users to blindly accept potentially harmful agreements. SkipTheTerms solves this by providing a Manifest V3 Chrome Extension that extracts legal text from the current page and delegates the summarization workload to a FastAPI backend powered by the Groq API (LLaMA 3.3). Summaries are cached in a Supabase PostgreSQL database to ensure instant retrieval for subsequent requests, optimizing both speed and API costs.

## Key Features

- **Automated Summarization:** Instantly distills lengthy legal jargon into clear, comprehensible bullet points.
- **Intelligent Caching System:** Uses a PostgreSQL database to cache previously generated summaries by URL, significantly reducing latency and LLM token usage.
- **User Feedback Loop:** Incorporates a helpful/unhelpful rating system to track summary quality and user satisfaction.
- **Seamless Browser Integration:** Built as a lightweight Manifest V3 Chrome Extension for a frictionless user experience.
- **RESTful API Architecture:** Clean, well-documented FastAPI backend for handling requests, database operations, and external API integrations.

## System Architecture

The application follows a client-server architecture with external API integrations.

1. **Client (Chrome Extension):**
   - **Content Script:** Extracts the raw textual content from the active webpage.
   - **Popup UI:** Provides the user interface to trigger the summarization and display results.
   - **Background/Popup Logic:** Communicates with the FastAPI backend via REST.

2. **Server (FastAPI Backend):**
   - **API Router:** Exposes endpoints for summarization (`/summarize`) and rating (`/rate`).
   - **Database Client:** Interfaces with Supabase (PostgreSQL) for reading and writing cached summaries and ratings.
   - **LLM Service:** Integrates with the Groq API to generate summaries when cache misses occur.

3. **Data Storage & LLM:**
   - **Supabase (PostgreSQL):** Persistent storage for summaries and user feedback.
   - **Groq API:** Provides high-speed LLM inference (LLaMA 3.3).

## Technology Stack

- **Frontend:** HTML, CSS, Vanilla JavaScript, Chrome Extension APIs (Manifest V3)
- **Backend:** Python 3, FastAPI, Uvicorn, Pydantic
- **Database:** Supabase (PostgreSQL), Supabase Python Client
- **AI/LLM:** Groq API (LLaMA 3.3 70B)

## Getting Started

### Prerequisites

- Python 3.8+
- Google Chrome or Chromium-based browser
- Supabase Account and Project
- Groq API Key

### Backend Setup

1. **Clone the repository and navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Duplicate the `.env.example` file and rename it to `.env`. Fill in your credentials:
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   GROQ_API_KEY=your_groq_api_key
   ```

5. **Start the FastAPI server:**
   ```bash
   uvicorn main:app --reload
   ```
   The backend will start at `http://localhost:8000`. API documentation (Swagger UI) is available at `http://localhost:8000/docs`.

### Extension Setup

1. Open Chrome and navigate to `chrome://extensions`.
2. Enable **Developer mode** via the toggle in the top right corner.
3. Click **Load unpacked** and select the `extension/` directory from this repository.
4. Pin the extension to your toolbar.
5. Navigate to any terms of service page and click the extension icon to generate a summary.

## API Reference

### 1. Generate Summary
**Endpoint:** `POST /summarize`

**Request:**
```json
{
  "url": "https://example.com/terms",
  "text": "The raw terms of service text extracted from the page..."
}
```

**Response:**
```json
{
  "url": "https://example.com/terms",
  "summary": "- First point\n- Second point",
  "cached": false
}
```

### 2. Rate Summary
**Endpoint:** `POST /rate`

**Request:**
```json
{
  "url": "https://example.com/terms",
  "vote": "up"  // or "down"
}
```

**Response:**
```json
{
  "url": "https://example.com/terms",
  "thumbs_up": 15,
  "thumbs_down": 2
}
```

## Database Schema

```sql
CREATE TABLE termscache (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    summary TEXT NOT NULL,
    thumbs_up INTEGER DEFAULT 0,
    thumbs_down INTEGER DEFAULT 0
);
```

## License

This project is licensed under the MIT License.
