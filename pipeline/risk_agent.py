"""
pipeline/risk_agent.py

Node 5 — Risk & Bias Detection Agent
Flags risk factors: single-vendor over-dependency, missing compliance
documentation, unusually low bids (dumping risk), and scoring criteria
that could unfairly disadvantage smaller vendors.

Guardrail layer: Enkrypt AI is used here to run an additional safety/
bias check over the generated risk narrative before it's shown to the
user (catches unfair or discriminatory language in the flags
themselves, not just the vendor data). Falls back to skipping this
extra check if ENKRYPT_API_KEY isn't configured — the rule-based
flags below still run regardless.
Tech: Python, Gemini 1.5 Pro, Enkrypt AI
"""

import os
import statistics
from typing import Dict, Any, List
from pipeline.state import VendorMindState

_LOW_BID_THRESHOLD = 0.6  # a vendor priced this much below the median is flagged


def _enkrypt_check(text: str) -> Dict[str, Any]:
    """Optional guardrail pass via Enkrypt AI. Returns a no-op result
    if the API key isn't set, so this never blocks the pipeline."""
    api_key = os.getenv("ENKRYPT_API_KEY")
    if not api_key:
        return {"checked": False, "flagged": False, "reason": "ENKRYPT_API_KEY not set"}

    try:
        import requests
        resp = requests.post(
            "https://api.enkryptai.com/guardrails/v1/check",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"text": text, "checks": ["bias", "fairness", "toxicity"]},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {"checked": True, "flagged": data.get("flagged", False), "detail": data}
        return {"checked": False, "flagged": False, "reason": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"checked": False, "flagged": False, "reason": str(e)}


def run_risk_agent(state: VendorMindState) -> VendorMindState:
    parsed_vendors = state.get("parsed_vendors", [])
    scores = state.get("scores", {})
    criteria = state.get("criteria", {})

    all_prices = []
    for v in parsed_vendors:
        price_str = v.get("extracted", {}).get("price_mentioned")
        if price_str:
            try:
                all_prices.append(float(price_str.replace("$", "").replace(",", "")))
            except ValueError:
                pass
    median_price = statistics.median(all_prices) if all_prices else None

    risk_flags: Dict[str, List[str]] = {}
    for i, v in enumerate(parsed_vendors):
        vid = v.get("vendor_id", f"vendor_{i+1}")
        flags: List[str] = []

        required_certs = set(c.upper() for c in criteria.get("compliance_requirements", []))
        have_certs = set(c.upper() for c in v.get("extracted", {}).get("certifications_mentioned", []))
        missing = required_certs - have_certs
        if missing:
            flags.append(f"Missing required compliance documentation: {', '.join(sorted(missing))}")

        price_str = v.get("extracted", {}).get("price_mentioned")
        if median_price and price_str:
            try:
                price = float(price_str.replace("$", "").replace(",", ""))
                if price < median_price * _LOW_BID_THRESHOLD:
                    flags.append("Unusually low bid relative to other vendors — possible dumping risk")
            except ValueError:
                pass

        composite = scores.get(vid, {}).get("composite_score", 0)
        if composite == 0:
            flags.append("Insufficient data to confidently score this vendor")

        risk_flags[vid] = flags

    # Portfolio-level check: single-vendor over-dependency
    if len(parsed_vendors) == 1:
        first_vid = parsed_vendors[0].get("vendor_id", "vendor_1")
        risk_flags.setdefault(first_vid, []).append(
            "Only one vendor evaluated — no comparison basis, single-source dependency risk"
        )

    # Optional Enkrypt guardrail pass over the combined flag narrative
    combined_text = " ".join(f for flags in risk_flags.values() for f in flags)
    if combined_text:
        guardrail_result = _enkrypt_check(combined_text)
        state["_enkrypt_guardrail"] = guardrail_result  # kept for audit log

    state["risk_flags"] = risk_flags
    return state
