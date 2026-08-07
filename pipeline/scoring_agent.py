"""
pipeline/scoring_agent.py

Node 4 — Multi-Signal Scoring Agent
Computes a composite score per vendor combining structured signals
(cost, compliance completeness, delivery timeline fit) with the
semantic retrieval score from the Vendor Profile Retrieval Agent.

Enhanced with A2A Protocol:
  - After computing draft scores, submits them to the Risk & Bias Agent
    via Agent-to-Agent (A2A) negotiation for EEOC adverse impact vetting.
  - If the Risk Agent issues a veto (adverse impact ratio < 0.80), the
    fairness floor adjustment is automatically applied before final scores
    are written to state.
Tech: Python, Gemini 1.5 Pro (for qualitative signal), A2A Protocol
"""

import re
import time
from typing import Dict, Any
from pipeline.state import VendorMindState
from pipeline.a2a_protocol import scoring_to_risk_handshake


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
    t0 = time.monotonic()

    parsed_vendors = state.get("parsed_vendors", [])
    criteria = state.get("criteria", {})
    vendor_context = state.get("vendor_context", {})

    prices = {
        v.get("vendor_id", f"vendor_{i+1}"): _extract_price(v.get("cleaned_text") or v.get("raw_text") or "")
        for i, v in enumerate(parsed_vendors)
    }
    finite_prices = [p for p in prices.values() if p != float("inf")]
    min_price = min(finite_prices) if finite_prices else 1.0

    cost_weight = float(criteria.get("cost_weight", 0.4) or 0.4)
    required_certs = criteria.get("compliance_requirements", [])

    # ── Step 1: Compute draft scores ─────────────────────────────────────────
    draft_scores: Dict[str, Any] = {}
    for i, v in enumerate(parsed_vendors):
        vid = v.get("vendor_id", f"vendor_{i+1}")
        price = prices.get(vid, float("inf"))

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

        draft_scores[vid] = {
            "cost_score": round(cost_score, 3),
            "compliance_score": round(compliance, 3),
            "semantic_score": round(semantic, 3),
            "composite_score": round(composite, 3),
        }

    # ── Step 2: A2A Handshake with Risk Agent (EEOC Fairness Vetting) ────────
    # Scoring Agent submits draft scores to Risk Agent via A2A protocol.
    # Risk Agent checks EEOC adverse impact ratios and may veto/adjust scores.
    # Final scores are returned after any fairness floor adjustments.
    final_scores = scoring_to_risk_handshake(state, draft_scores)

    # Build EEOC report for UI display
    top = max((s.get("composite_score", 0) for s in final_scores.values()), default=1.0)
    eeoc_report = {}
    for vid, s in final_scores.items():
        ratio = round(s.get("composite_score", 0) / top, 3) if top > 0 else 1.0
        eeoc_report[vid] = {
            "adverse_impact_ratio": ratio,
            "passes_4_5ths_rule": ratio >= 0.80,
            "eeoc_adjusted": s.get("eeoc_adjusted", False),
        }

    state["scores"] = final_scores
    state["eeoc_report"] = eeoc_report

    # OpenTelemetry latency tracking
    elapsed = round((time.monotonic() - t0) * 1000, 2)
    latency = state.get("latency_ms", {})
    latency["scoring"] = elapsed
    state["latency_ms"] = latency

    return state

