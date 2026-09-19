import json
import urllib.error
import urllib.request

from .config import GEMINI_API_KEY, GEMINI_MODEL

SYSTEM_PROMPT = """You are Datazoic AI, a professional business and invoice assistant.

Rules:
- Answer normal general questions using your Gemini knowledge and reasoning. Do NOT require the company's knowledge base for general questions.
- When application data or knowledge-base context is supplied, use it as the source of truth for company-specific facts.
- Never invent invoice, customer, payment, dispute, sales, or company records.
- Never claim an invoice action succeeded unless the application result says success.
- If company-specific information is missing, clearly say that the company-specific information is unavailable, but still answer any general part of the user's question when possible.
- Be concise, useful, and professional.
"""


def _history_to_contents(history):
    contents = []
    for item in (history or [])[-12:]:
        role = item.get("role")
        text = item.get("content")
        if role not in {"user", "model", "assistant"} or not text:
            continue
        contents.append({
            "role": "model" if role == "assistant" else role,
            "parts": [{"text": str(text)}],
        })
    return contents


def generate(message, history=None, context=None):
    """Generate a Gemini response using Google's REST API.

    Returns None only when Gemini is not configured or the provider request fails.
    The exception is intentionally not swallowed internally so the caller can expose
    a useful diagnostic in development while keeping the UI fallback friendly.
    """
    if not GEMINI_API_KEY:
        return None

    context = context or ""
    user_prompt = str(message)
    if context:
        user_prompt = (
            "Application context (authoritative for company-specific data):\n"
            f"{context}\n\n"
            "User request:\n"
            f"{message}"
        )

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": _history_to_contents(history) + [
            {"role": "user", "parts": [{"text": user_prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1024,
        },
    }
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini HTTP {exc.code}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Gemini network error: {exc.reason}") from exc

    candidates = data.get("candidates") or []
    if not candidates:
        feedback = data.get("promptFeedback") or {}
        raise RuntimeError(f"Gemini returned no candidates: {feedback}")

    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if p.get("text"))
    return text.strip() or None
