"""
Unit tests for the SkipTheTerms FastAPI backend.

Stub modules for `database` and `groq_service` are injected into
sys.modules *before* main is imported so that no live Supabase or Groq
credentials are required to run the test suite.

Run from the backend/ directory:
    pytest test_main.py -v
"""
import sys
from unittest.mock import MagicMock, patch

# -----------------------------------------------------------------------
# Inject dependency stubs before importing main.py
# -----------------------------------------------------------------------
# This bypasses the startup-time validation in database.py and
# groq_service.py that would raise ValueError without real credentials.
sys.modules["database"] = MagicMock()
sys.modules["groq_service"] = MagicMock()

from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402  # triggers the from-imports inside main.py

client = TestClient(main.app)


def _supabase_select_stub(rows: list) -> MagicMock:
    """Return a Supabase stub whose .table().select().eq().limit().execute().data == rows."""
    stub = MagicMock()
    (
        stub.table.return_value
        .select.return_value
        .eq.return_value
        .limit.return_value
        .execute.return_value
        .data
    ) = rows
    return stub


# -----------------------------------------------------------------------
# Health check
# -----------------------------------------------------------------------


def test_health_check():
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "SkipTheTerms" in body["message"]


# -----------------------------------------------------------------------
# POST /summarize — input validation (no DB / LLM calls needed)
# -----------------------------------------------------------------------


def test_summarize_rejects_empty_url():
    resp = client.post("/summarize", json={"url": "  ", "text": "some terms text"})
    assert resp.status_code == 400
    assert "URL" in resp.json()["detail"]


def test_summarize_rejects_empty_text():
    resp = client.post("/summarize", json={"url": "https://example.com/tos", "text": "   "})
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_summarize_rejects_oversized_text():
    resp = client.post(
        "/summarize",
        json={"url": "https://example.com/tos", "text": "x" * 50_001},
    )
    assert resp.status_code == 400
    assert "50,000" in resp.json()["detail"]


# -----------------------------------------------------------------------
# POST /summarize — cache hit (LLM must NOT be called)
# -----------------------------------------------------------------------


def test_summarize_returns_cached_result():
    cached_summary = "• Cached point one\n• Cached point two"

    with (
        patch("main.supabase", _supabase_select_stub([{"summary": cached_summary}])),
        patch("main.summarize_terms") as mock_llm,
    ):
        resp = client.post(
            "/summarize",
            json={"url": "https://example.com/tos", "text": "Some legal text here"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["cached"] is True
    assert body["summary"] == cached_summary
    mock_llm.assert_not_called()


# -----------------------------------------------------------------------
# POST /summarize — cache miss (LLM must be called, result cached)
# -----------------------------------------------------------------------


def test_summarize_calls_llm_on_cache_miss():
    llm_output = "• They own your soul\n• You can't sue them"

    with (
        patch("main.supabase", _supabase_select_stub([])),
        patch("main.summarize_terms", return_value=llm_output) as mock_llm,
    ):
        resp = client.post(
            "/summarize",
            json={"url": "https://example.com/tos", "text": "Some legal text here"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["cached"] is False
    assert body["summary"] == llm_output
    mock_llm.assert_called_once()


# -----------------------------------------------------------------------
# POST /rate — input validation
# -----------------------------------------------------------------------


def test_rate_rejects_invalid_vote():
    resp = client.post(
        "/rate",
        json={"url": "https://example.com/tos", "vote": "sideways"},
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert "up" in detail or "down" in detail


# -----------------------------------------------------------------------
# POST /rate — URL not in cache → 404
# -----------------------------------------------------------------------


def test_rate_returns_404_for_uncached_url():
    with patch("main.supabase", _supabase_select_stub([])):
        resp = client.post(
            "/rate",
            json={"url": "https://never-cached.com/tos", "vote": "up"},
        )

    assert resp.status_code == 404
    assert "No cached entry" in resp.json()["detail"]
