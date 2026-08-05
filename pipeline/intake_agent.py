"""
pipeline/intake_agent.py

Node 1 — Intake Agent
Parses and normalizes the RFP text and raw vendor submission documents
into structured fields the rest of the pipeline can work with.

Enhanced with Gemma PII Filter:
  - All text passes through Gemma (or regex fallback) BEFORE any cloud
    API call. This ensures GDPR Article 5 data minimisation at the
    system ingestion boundary.
  - Gemma model: gemma-3-27b-it (Google AI Studio)
Tech: Python, Gemma 3 (Google), regex
"""

import re
import time
from typing import Dict, Any, List
from pipeline.state import VendorMindState
from pipeline.gemma_filter import gemma_preprocess


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def _extract_basic_fields(text: str) -> Dict[str, Any]:
    """Lightweight structured extraction — looks for common patterns
    like price mentions, dates, and certifications without requiring
    an LLM call at this stage (kept cheap/fast; deep extraction
    happens in the Criteria Extraction Agent)."""
    price_match = re.search(r"\$\s?[\d,]+(?:\.\d{2})?", text)
    cert_matches = re.findall(
        r"\b(ISO\s?\d{4,5}|SOC\s?2|GDPR|HIPAA|PCI[- ]?DSS)\b", text, re.IGNORECASE
    )
    return {
        "price_mentioned": price_match.group(0) if price_match else None,
        "certifications_mentioned": sorted(set(c.upper() for c in cert_matches)),
        "word_count": len(text.split()),
    }


def run_intake_agent(state: VendorMindState) -> VendorMindState:
    t0 = time.monotonic()

    rfp_raw = _clean_text(state.get("rfp_text", ""))
    vendors: List[Dict[str, Any]] = state.get("vendors", [])

    # ── Gemma PII Filter: RFP ────────────────────────────────────────────────
    # All text passes through Gemma BEFORE any Gemini API call.
    # Satisfies GDPR Article 5 (data minimisation) and mandatory Gemma
    # hackathon stack requirement.
    rfp_gemma = gemma_preprocess(rfp_raw)
    rfp_cleaned = rfp_gemma["cleaned_text"]

    # ── Gemma PII Filter: Each Vendor Proposal ───────────────────────────────
    gemma_vendor_results = []
    parsed_vendors = []
    for v in vendors:
        raw = _clean_text(v.get("raw_text", ""))
        vendor_gemma = gemma_preprocess(raw)
        gemma_vendor_results.append({
            "vendor_id": v.get("vendor_id"),
            **vendor_gemma,
        })
        cleaned = vendor_gemma["cleaned_text"]
        parsed_vendors.append({
            "vendor_id": v.get("vendor_id"),
            "vendor_name": v.get("vendor_name", v.get("vendor_id")),
            "cleaned_text": cleaned,
            "extracted": _extract_basic_fields(cleaned),
            "language": vendor_gemma.get("language", "en"),
            "pii_detected": vendor_gemma.get("pii_detected", False),
            "gemma_model": vendor_gemma.get("model", "regex-fallback"),
        })

    state["parsed_rfp"] = {
        "cleaned_text": rfp_cleaned,
        "extracted": _extract_basic_fields(rfp_cleaned),
        "language": rfp_gemma.get("language", "en"),
        "pii_detected": rfp_gemma.get("pii_detected", False),
        "gemma_model": rfp_gemma.get("model", "regex-fallback"),
    }
    state["parsed_vendors"] = parsed_vendors
    state["gemma_rfp_result"] = rfp_gemma
    state["gemma_pii_results"] = gemma_vendor_results

    # OpenTelemetry latency tracking
    elapsed = round((time.monotonic() - t0) * 1000, 2)
    latency = state.get("latency_ms", {})
    latency["intake"] = elapsed
    state["latency_ms"] = latency

    return state

