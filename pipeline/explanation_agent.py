"""
pipeline/explanation_agent.py

Node 6 — Explanation Generation Agent
Generates a human-readable justification for each vendor's score and
rank, citing specific evidence (e.g. "Ranked #1 due to 15% lower cost
and complete ISO compliance, but flagged for shorter track record").
Tech: Python, Gemini 1.5 Pro
"""

from pipeline.state import VendorMindState
from pipeline.llm_client import gemini_generate

_PROMPT_TEMPLATE = """You are explaining a vendor evaluation ranking to a
procurement manager. Be concise (2-3 sentences), specific, and cite the
actual numbers given. Do not invent facts not present below.

Vendor: {vendor_name}
Composite score: {composite}
Cost score: {cost} | Compliance score: {compliance} | Semantic fit: {semantic}
Risk flags: {flags}

Write the justification now:"""


def _rule_based_explanation(vendor_name: str, s: dict, flags: list) -> str:
    """Deterministic fallback explanation if the LLM is unavailable —
    still evidence-based, just less fluent."""
    parts = [
        f"{vendor_name} scored {s.get('composite_score', 0):.2f} overall",
        f"(cost {s.get('cost_score', 0):.2f}, compliance {s.get('compliance_score', 0):.2f}, "
        f"fit {s.get('semantic_score', 0):.2f}).",
    ]
    if flags:
        parts.append("Flags raised: " + "; ".join(flags) + ".")
    else:
        parts.append("No risk flags raised.")
    return " ".join(parts)


def run_explanation_agent(state: VendorMindState) -> VendorMindState:
    parsed_vendors = state.get("parsed_vendors", [])
    scores = state.get("scores", {})
    risk_flags = state.get("risk_flags", {})

    explanations = {}
    for v in parsed_vendors:
        vid = v["vendor_id"]
        s = scores.get(vid, {})
        flags = risk_flags.get(vid, [])

        prompt = _PROMPT_TEMPLATE.format(
            vendor_name=v.get("vendor_name", vid),
            composite=s.get("composite_score", 0),
            cost=s.get("cost_score", 0),
            compliance=s.get("compliance_score", 0),
            semantic=s.get("semantic_score", 0),
            flags=", ".join(flags) if flags else "none",
        )
        text = gemini_generate(prompt)

        if text.startswith("[LLM unavailable"):
            text = _rule_based_explanation(v.get("vendor_name", vid), s, flags)

        explanations[vid] = text

    state["explanations"] = explanations
    return state
