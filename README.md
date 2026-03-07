# SkipTheTerms

> **TL;DR for legal nonsense.** A Chrome Extension that scrapes Terms of Service pages and returns brutally honest, sarcastic bullet-point summaries — powered by Groq (LLaMA 3.3).

---

## Project Structure

```
SkipTheTerms/
├── backend/                  # FastAPI server
│   ├── main.py               # API routes (/summarize)
│   ├── database.py           # Supabase client setup
│   ├── groq_service.py       # Groq LLM integration
│   └── requirements.txt      # Python dependencies
│
├── extension/                # Chrome Extension (Manifest V3)
│   ├── manifest.json         # Extension config & permissions
│   ├── popup.html            # Popup UI
│   ├── popup.js              # Summarize button logic
│   └── content.js            # Page text scraper
│
├── .env                      # 🔒 Secret keys (never commit)
├── .env.example              # Template for environment variables
└── .gitignore
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Extension | Chrome MV3, Vanilla JS, CSS |
| Backend | FastAPI + Uvicorn |
| LLM | Groq API — LLaMA 3.3 70B |
| Cache | Supabase (PostgreSQL) |

---

## Getting Started

### 1. Clone & set up the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
GROQ_API_KEY=your_groq_api_key
```

### 3. Run the backend

```bash
cd backend
uvicorn main:app --reload
```

The API will be live at `http://localhost:8000`.

### 4. Load the Chrome Extension

1. Open `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** → select the `extension/` folder
4. Pin the extension and navigate to any Terms of Service page

---

## API Reference

### `POST /summarize`

**Request body:**
```json
{
  "url": "https://example.com/terms",
  "text": "<scraped page text>"
}
```

**Response:**
```json
{
  "url": "https://example.com/terms",
  "summary": "• They own your content permanently.\n• Your data is sold to partners.\n• ...",
  "cached": false
}
```

Responses are cached by URL in Supabase — repeat visits return instantly.

---

## Supabase Schema

```sql
create table termscache (
  id      bigint generated always as identity primary key,
  url     text unique not null,
  summary text not null
);
```

---

*Built with ☕ and deep distrust of legal documents.*
