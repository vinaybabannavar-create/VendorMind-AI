"""
pipeline/comparison_agent.py

Node 7 — Comparison Agent
Generates a side-by-side structured comparison of shortlisted vendors
across all scored dimensions, ranked by composite score.
Tech: Python, Pandas
"""

from pipeline.state import VendorMindState


def run_comparison_agent(state: VendorMindState) -> VendorMindState:
    parsed_vendors = state.get("parsed_vendors", [])
    scores = state.get("scores", {})
    risk_flags = state.get("risk_flags", {})
    explanations = state.get("explanations", {})

    rows = []
    for i, v in enumerate(parsed_vendors):
        vid = v.get("vendor_id", f"vendor_{i+1}")
        s = scores.get(vid, {})
        rows.append({
            "vendor_id": vid,
            "vendor_name": v.get("vendor_name", vid),
            "composite_score": s.get("composite_score", 0),
            "cost_score": s.get("cost_score", 0),
            "compliance_score": s.get("compliance_score", 0),
            "semantic_score": s.get("semantic_score", 0),
            "risk_flag_count": len(risk_flags.get(vid, [])),
            "risk_flags": risk_flags.get(vid, []),
            "explanation": explanations.get(vid, ""),
        })

    rows.sort(key=lambda r: r["composite_score"], reverse=True)
    for i, row in enumerate(rows, start=1):
        row["rank"] = i

    state["comparison_table"] = rows
    return state
