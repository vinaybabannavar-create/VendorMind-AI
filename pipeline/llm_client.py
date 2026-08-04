"""
pipeline/llm_client.py

Thin wrapper around the Gemini API (Google AI Studio / Vertex AI).
Centralized here so every agent calls the same function instead of
re-initializing the SDK. If GEMINI_API_KEY is missing or the call
fails, callers get a clearly-marked fallback string instead of a
crash — important during a live demo where network hiccups happen.
"""

import os
import json
from typing import Optional

_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
_client = None
_client_error: Optional[str] = None


def _get_client():
    """Lazily initialize the Gemini client so importing this module
    never fails even if the SDK or API key isn't set up yet."""
    global _client, _client_error
    if _client is not None or _client_error is not None:
        return _client

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        _client_error = "GEMINI_API_KEY not set"
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _client = genai.GenerativeModel(_MODEL_NAME)
        return _client
    except Exception as e:  # pragma: no cover
        _client_error = f"Gemini client init failed: {e}"
        return None


def gemini_generate(prompt: str, expect_json: bool = False) -> str:
    """
    Send a prompt to Gemini and return the text response.
    On any failure, returns a safe fallback so the pipeline keeps running.
    """
    client = _get_client()
    if client is None:
        return _fallback(prompt, expect_json, reason=_client_error or "no client")

    try:
        response = client.generate_content(prompt)
        text = (response.text or "").strip()
        if not text:
            return _fallback(prompt, expect_json, reason="empty response")
        return text
    except Exception as e:  # pragma: no cover
        return _fallback(prompt, expect_json, reason=str(e))


def _fallback(prompt: str, expect_json: bool, reason: str) -> str:
    """Deterministic, clearly-labeled fallback so a missing API key
    never silently produces a wrong answer during a demo."""
    note = f"[LLM unavailable — {reason}]"
    if expect_json:
        return json.dumps({"_fallback": True, "note": note})
    return note
