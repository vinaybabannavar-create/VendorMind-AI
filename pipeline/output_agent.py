"""
pipeline/output_agent.py

Node 8 — Output & HITL Agent
Produces the final ranked shortlist + report and sets hitl_approved to
None (pending) — the actual approval happens as a separate user action
in the Procurement Dashboard, which is the "loop-back" edge to the
frontend shown in the architecture diagram. This node does NOT
auto-approve anything; a human must act.
Tech: Python, LangGraph
"""

from datetime import datetime, timezone
from pipeline.state import VendorMindState


def run_output_agent(state: VendorMindState) -> VendorMindState:
    comparison_table = state.get("comparison_table", [])
    top_vendor = comparison_table[0] if comparison_table else None

    state["final_report"] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "recommended_vendor": top_vendor.get("vendor_name") if top_vendor else None,
        "recommended_vendor_id": top_vendor.get("vendor_id") if top_vendor else None,
        "ranking": comparison_table,
        "criteria_used": state.get("criteria", {}),
        "total_vendors_evaluated": len(comparison_table),
    }
    # Explicitly pending until a human approves via the dashboard —
    # this is the human-in-the-loop gate, not a rubber stamp.
    state["hitl_approved"] = None
    return state
