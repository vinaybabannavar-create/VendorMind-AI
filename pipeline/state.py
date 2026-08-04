"""
pipeline/state.py

Shared state object passed between every node in the LangGraph pipeline.
Each agent reads what it needs and writes its own output key — nothing
is overwritten, so the full audit trail survives to the Output & HITL
Agent (and from there, to the Audit & State Store).
"""

from typing import TypedDict, List, Dict, Any, Optional


class VendorRecord(TypedDict, total=False):
    vendor_id: str
    vendor_name: str
    raw_text: str


class VendorMindState(TypedDict, total=False):
    # --- Input ---
    rfp_text: str
    vendors: List[VendorRecord]

    # --- 1. Intake Agent output ---
    parsed_rfp: Dict[str, Any]
    parsed_vendors: List[Dict[str, Any]]

    # --- 2. Criteria Extraction Agent output ---
    criteria: Dict[str, Any]

    # --- 3. Vendor Profile Retrieval Agent output ---
    vendor_context: Dict[str, Any]          # vendor_id -> retrieved profile/history

    # --- 4. Multi-Signal Scoring Agent output ---
    scores: Dict[str, Any]                  # vendor_id -> {cost, compliance, timeline, semantic, composite}

    # --- 5. Risk & Bias Detection Agent output ---
    risk_flags: Dict[str, Any]              # vendor_id -> [flags]

    # --- 6. Explanation Generation Agent output ---
    explanations: Dict[str, str]            # vendor_id -> human-readable justification

    # --- 7. Comparison Agent output ---
    comparison_table: List[Dict[str, Any]]  # ranked, side-by-side rows

    # --- 8. Output & HITL Agent output ---
    final_report: Dict[str, Any]
    hitl_approved: Optional[bool]

    # --- bookkeeping ---
    errors: List[str]
