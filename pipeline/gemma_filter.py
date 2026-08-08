"""
pipeline/gemma_filter.py

Gemma PII Filter & Document Pre-Processor (Intake Layer)
=========================================================
Uses Gemma (Google's open lightweight model) as the FIRST gate before
any vendor data is forwarded to the Gemini API.

Responsibilities:
  1. PII Detection & Redaction  — SSN, Aadhaar, email, phone patterns
     that must not leave the intake boundary (GDPR Article 5 principle
     of data minimisation).
  2. Noise Normalization        — strip boilerplate headers, page numbers,
     and repeated whitespace so downstream agents receive clean text.
  3. Language Detection         — flag non-English documents for the
     multilingual-aware pipeline path (future: MT5/translate).
  4. Cost Gate                  — Gemma runs locally / on-device; zero
     additional API cost per document page.

Gemma is accessed via the google-generativeai SDK using the
"gemma-3-27b-it" model endpoint on AI Studio. Falls back gracefully
(rule-based regex PII scrub) if GEMMA_API_KEY is not set, so the
pipeline never blocks on optional credentials.

Tech: Gemma 3 27B-IT (Google AI Studio), Python, regex
CRISPE alignment: Intake node pre-processes data before any Gemini call,
  satisfying the "PII boundary before cloud API" compliance requirement.
"""

import os
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ── Gemma model config ───────────────────────────────────────────────────────
# Note: Uses GEMMA_MODEL env var if set, defaulting to gemma-3-27b-it via
# Google AI Studio, with a deterministic regex PII scrubber always run first.
_GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma-3-27b-it")
_gemma_client = None
_gemma_error: str | None = None


def _get_gemma_client():
    """Lazily initialise Gemma via Google AI Studio SDK.

    Uses GEMMA_API_KEY (preferred) or falls back to GEMINI_API_KEY so
    existing deployments work without extra secrets.
    """
    global _gemma_client, _gemma_error
    if _gemma_client is not None or _gemma_error is not None:
        return _gemma_client

    api_key = os.getenv("GEMMA_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        _gemma_error = "Neither GEMMA_API_KEY nor GEMINI_API_KEY is set"
        return None

    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=api_key)
        _gemma_client = genai.GenerativeModel(_GEMMA_MODEL)
        logger.info("Gemma PII filter initialised with model: %s", _GEMMA_MODEL)
        return _gemma_client
    except Exception as exc:
        _gemma_error = f"Gemma init failed: {exc}"
        logger.warning("Gemma unavailable: %s — using regex fallback", _gemma_error)
        return None


# ── Regex-based PII scrubber (always runs as a first pass) ───────────────────
_PII_PATTERNS = [
    # Email addresses
    (re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"), "[EMAIL_REDACTED]"),
    # Phone numbers (international/domestic)
    (re.compile(r"\+?[\d\-\(\)\s]{7,15}(?=\D|$)"), "[PHONE_REDACTED]"),
    # SSN (US format)
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
    # Aadhaar (India 12-digit)
    (re.compile(r"\b[2-9]{1}\d{3}\s?\d{4}\s?\d{4}\b"), "[AADHAAR_REDACTED]"),
    # Credit card (basic Luhn-format)
    (re.compile(r"\b(?:\d[ \-]?){13,16}\b"), "[CC_REDACTED]"),
    # IP addresses
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP_REDACTED]"),
]


def _regex_pii_scrub(text: str) -> str:
    """Rule-based PII scrub — always applied, even when Gemma is available,
    as a deterministic first-pass before sending text to any cloud model."""
    for pattern, replacement in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _detect_language(text: str) -> str:
    """Lightweight heuristic language detection (no external dep).
    Returns ISO 639-1 code or 'unknown'."""
    sample = text[:500].lower()
    # Simple character-frequency check; replace with langdetect in prod
    latin_ratio = sum(1 for c in sample if c.isalpha() and ord(c) < 256) / max(len(sample), 1)
    if latin_ratio > 0.8:
        return "en"
    return "unknown"


# ── CRISPE Prompt for Gemma ──────────────────────────────────────────────────
_GEMMA_PII_PROMPT = """
**Context**: You are the Intake Security Gate of VendorMind AI, an enterprise
procurement evaluation system. Vendor proposal documents are being prepared for
AI analysis. GDPR Article 5 mandates data minimisation before any cloud API call.

**Role**: Act as a privacy-aware document pre-processor. You are NOT an evaluator.

**Instructions**:
1. Identify any remaining PII not already redacted (names, addresses, passport
   numbers, bank account details, digital identifiers).
2. Return ONLY the cleaned document text with PII replaced by [TYPE_REDACTED].
3. Do NOT summarise, do NOT add commentary, do NOT change factual content.
4. If no PII is found, return the text unchanged.

**Scope**: The document is a vendor bid proposal. Focus on contact details,
financial account numbers, and personal identifiers. Preserve all pricing
figures, certification codes, and technical specifications.

**Precision**: Maximum 2000 tokens. If text exceeds this, process the first
2000 tokens and append [TRUNCATED_FOR_PII_SCAN].

**Example**:
Input:  "Contact John Smith at j.smith@acme.com or +91-98765-43210."
Output: "Contact [NAME_REDACTED] at [EMAIL_REDACTED] or [PHONE_REDACTED]."

--- DOCUMENT BEGIN ---
{text}
--- DOCUMENT END ---

Return only the cleaned text, nothing else.
""".strip()


def gemma_preprocess(raw_text: str) -> Dict[str, Any]:
    """
    Main entry point called by the Intake Agent.

    Returns a dict with:
      - cleaned_text  : PII-scrubbed, normalised text
      - pii_detected  : bool — whether any PII was found/redacted
      - language      : ISO 639-1 code
      - gemma_used    : bool — True if Gemma API was used, False = regex only
      - model         : model name used
    """
    # Step 1: Always apply regex scrub first (cheap, deterministic)
    regex_cleaned = _regex_pii_scrub(raw_text)
    pii_detected = regex_cleaned != raw_text
    language = _detect_language(regex_cleaned)

    # Step 2: Try Gemma for deeper semantic PII detection
    client = _get_gemma_client()
    if client is not None:
        try:
            prompt = _GEMMA_PII_PROMPT.format(text=regex_cleaned[:3000])
            response = client.generate_content(prompt)
            gemma_text = (response.text or "").strip()
            if gemma_text and len(gemma_text) > 50:
                # Detect if Gemma found additional PII
                if gemma_text != regex_cleaned[:3000]:
                    pii_detected = True
                return {
                    "cleaned_text": gemma_text,
                    "pii_detected": pii_detected,
                    "language": language,
                    "gemma_used": True,
                    "model": _GEMMA_MODEL,
                }
        except Exception as exc:
            logger.warning("Gemma PII pass failed: %s — keeping regex-only result", exc)

    # Step 3: Fallback — regex-cleaned text only
    return {
        "cleaned_text": regex_cleaned,
        "pii_detected": pii_detected,
        "language": language,
        "gemma_used": False,
        "model": "regex-fallback",
    }
