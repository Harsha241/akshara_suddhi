/**
 * API Client with debouncing
 * ==========================
 * Central HTTP client for all backend calls.
 * Every function returns structured JSON.
 */

const API_BASE = "http://127.0.0.1:8000";

async function post(endpoint, body) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${endpoint} failed: ${res.status} — ${err}`);
  }
  return res.json();
}

/* ── Public API functions ─────────────────────────────────────────────── */

export async function spellcheck(word, context = null) {
  return post("/spellcheck", { word, context });
}

export async function autocomplete(prefix) {
  return post("/autocomplete", { prefix });
}

export async function grammarCheck(sentence) {
  return post("/grammar", { sentence });
}

export async function autocorrect(sentence) {
  return post("/autocorrect", { sentence });
}

export async function transliterate(text) {
  return post("/transliterate", { text });
}

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}
