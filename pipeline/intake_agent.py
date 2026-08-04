"""
pipeline/intake_agent.py

Node 1 — Intake Agent
Parses and normalizes the RFP text and raw vendor submission documents
into structured fields the rest of the pipeline can work with.
Tech: Python, PyPDF2 (for real PDF uploads), BeautifulSoup (HTML/text cleanup)
"""

import re
from typing import Dict, Any, List
from pipeline.state import VendorMindState


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
    rfp_text = _clean_text(state.get("rfp_text", ""))
    vendors: List[Dict[str, Any]] = state.get("vendors", [])

    parsed_vendors = []
    for v in vendors:
        raw = _clean_text(v.get("raw_text", ""))
        parsed_vendors.append({
            "vendor_id": v.get("vendor_id"),
            "vendor_name": v.get("vendor_name", v.get("vendor_id")),
            "cleaned_text": raw,
            "extracted": _extract_basic_fields(raw),
        })

    state["parsed_rfp"] = {
        "cleaned_text": rfp_text,
        "extracted": _extract_basic_fields(rfp_text),
    }
    state["parsed_vendors"] = parsed_vendors
    return state
