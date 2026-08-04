"""
pipeline/scoring_agent.py

Node 4 — Multi-Signal Scoring Agent
Computes a composite score per vendor combining structured signals
(cost, compliance completeness, delivery timeline fit) with the
semantic retrieval score from the Vendor Profile Retrieval Agent.
Tech: Python, Gemini 1.5 Pro (for qualitative signal), NumPy-free scoring
"""

import re
from typing import Dict, Any
from pipeline.state import VendorMindState


def _extract_price(text: str) -> float:
    match = re.search(r"\$\s?([\d,]+(?:\.\d{2})?)", text or "")
    if not match:
        return float("inf")  # unknown price scores worst on cost
    return float(match.group(1).replace(",", ""))


def _compliance_score(vendor_certs: list, required_certs: list) -> float:
    if not required_certs:
        return 1.0
    required = set(c.upper() for c in required_certs)
    have = set(c.upper() for c in vendor_certs)
    if not required:
        return 1.0
    return len(required & have) / len(required)


def run_scoring_agent(state: VendorMindState) -> VendorMindState:
    parsed_vendors = state.get("parsed_vendors", [])
    criteria = state.get("criteria", {})
    vendor_context = state.get("vendor_context", {})

    prices = {v["vendor_id"]: _extract_price(v["cleaned_text"]) for v in parsed_vendors}
    finite_prices = [p for p in prices.values() if p != float("inf")]
    min_price = min(finite_prices) if finite_prices else 1.0

    cost_weight = float(criteria.get("cost_weight", 0.4) or 0.4)
    required_certs = criteria.get("compliance_requirements", [])

    scores: Dict[str, Any] = {}
    for v in parsed_vendors:
        vid = v["vendor_id"]
        price = prices[vid]

        # Lower price -> higher cost score (normalized against cheapest vendor)
        cost_score = (min_price / price) if price not in (0, float("inf")) else 0.0
        cost_score = max(0.0, min(1.0, cost_score))

        compliance = _compliance_score(
            v.get("extracted", {}).get("certifications_mentioned", []),
            required_certs,
        )

        semantic = vendor_context.get(vid, {}).get("retrieved_score", 0.0)
        semantic = max(0.0, min(1.0, float(semantic)))

        # Weighted composite: cost per criteria weight, remaining split
        # between compliance and semantic fit
        remaining = max(0.0, 1.0 - cost_weight)
        composite = (
            cost_weight * cost_score
            + (remaining * 0.6) * compliance
            + (remaining * 0.4) * semantic
        )

        scores[vid] = {
            "cost_score": round(cost_score, 3),
            "compliance_score": round(compliance, 3),
            "semantic_score": round(semantic, 3),
            "composite_score": round(composite, 3),
        }

    state["scores"] = scores
    return state
