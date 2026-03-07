// popup.js — orchestrates scraping → API call → UI rendering

const BACKEND_URL = "http://localhost:8000/summarize";

const summarizeBtn = document.getElementById("summarize-btn");
const spinnerWrap = document.getElementById("spinner-wrap");
const resultsArea = document.getElementById("results-area");
const errorBanner = document.getElementById("error-banner");
const errorText = document.getElementById("error-text");

/** Show/hide helpers */
function showSpinner() { spinnerWrap.classList.add("visible"); }
function hideSpinner() { spinnerWrap.classList.remove("visible"); }
function showError(msg) {
    errorText.textContent = msg;
    errorBanner.classList.add("visible");
}
function hideError() { errorBanner.classList.remove("visible"); }

/** Render bullet points returned by the API */
function renderBullets(points) {
    resultsArea.innerHTML = "";

    if (!points || points.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "Hmm, nothing juicy found. Maybe this page is actually honest? 🤔";
        resultsArea.appendChild(empty);
    } else {
        points.forEach((point, i) => {
            const item = document.createElement("div");
            item.className = "bullet-item";
            item.style.animationDelay = `${i * 0.07}s`;
            item.innerHTML = `
                <span class="bullet-dot">•</span>
                <span class="bullet-text">${escapeHtml(point)}</span>
            `;
            resultsArea.appendChild(item);
        });
    }

    resultsArea.classList.add("visible");
}

/** Basic HTML escaper to avoid XSS from API response */
function escapeHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/** Main click handler */
summarizeBtn.addEventListener("click", async () => {
    // Reset UI state
    hideError();
    resultsArea.classList.remove("visible");
    resultsArea.innerHTML = "";
    showSpinner();
    summarizeBtn.disabled = true;

    try {
        // 1. Get the active tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab || !tab.id) {
            throw new Error("Couldn't find the active tab. Please try again.");
        }

        // 2. Inject content.js to scrape page text
        const injectionResults = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ["content.js"],
        });

        const pageText = injectionResults?.[0]?.result;

        if (!pageText || pageText.trim().length === 0) {
            throw new Error("The page appears to be empty or couldn't be read.");
        }

        // 3. Send scraped text to FastAPI backend
        // Use AbortController to enforce a 15s timeout — without this the fetch
        // hangs forever if the backend is not running.
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15_000);

        let response;
        try {
            response = await fetch(BACKEND_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: tab.url,
                    text: pageText,
                }),
                signal: controller.signal,
            });
        } catch (fetchErr) {
            if (fetchErr.name === "AbortError") {
                throw new Error("Backend didn't respond in time. Is `uvicorn` running in the `/backend` folder?");
            }
            throw new Error("Can't reach the backend. Make sure uvicorn is running: cd backend && uvicorn main:app --reload");
        } finally {
            clearTimeout(timeoutId);
        }

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(
                errData?.detail || `Backend returned ${response.status}: ${response.statusText}`
            );
        }

        const data = await response.json();

        // 4. Render the sarcastic bullet points.
        // The backend returns summary as a plain string with • characters.
        // Split it into an array so renderBullets can iterate over it.
        const raw = data.summary ?? data.points ?? data.bullets ?? "";
        const points = Array.isArray(raw)
            ? raw
            : raw.split("•").map((s) => s.trim()).filter(Boolean);

        renderBullets(points);

    } catch (err) {
        console.error("[SkipTheTerms] Error:", err);
        showError(err.message || "Something went wrong. Is the backend running?");
    } finally {
        hideSpinner();
        summarizeBtn.disabled = false;
    }
});
