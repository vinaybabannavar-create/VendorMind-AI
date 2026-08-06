"""
pipeline/state.py

Shared state object passed between every node in the LangGraph pipeline.
Each agent reads what it needs and writes its own output key — nothing
is overwritten, so the full audit trail survives to the Output & HITL
Agent (and from there, to the Audit & State Store).

Extended with:
  - Gemma PII filter results (GDPR data minimisation at intake boundary)
  - A2A Protocol log (Google A2A spec, Scoring <-> Risk negotiation)
  - EEOC fairness telemetry (adverse impact ratios)
  - OpenTelemetry trace IDs and token usage (LLM observability)
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

    # --- Gemma PII Filter output (Intake pre-processing) ---
    # Populated by pipeline/gemma_filter.py BEFORE any Gemini API call.
    # Ensures GDPR Article 5 data minimisation at the system boundary.
    gemma_pii_results: List[Dict[str, Any]]   # per-vendor Gemma scan result
    gemma_rfp_result: Dict[str, Any]          # RFP Gemma scan result

    # --- A2A Protocol log (Scoring <-> Risk negotiation) ---
    # Full audit trail of Agent-to-Agent messages (Google A2A spec).
    # Messages are exchanged between scoring_agent and risk_agent during
    # the EEOC fairness vetting handshake.
    a2a_log: List[Dict[str, Any]]

    # --- EEOC / Fairness Telemetry ---
    # Adverse impact ratios computed during A2A handshake.
    eeoc_report: Dict[str, Any]               # adverse impact ratios per vendor

    # --- OpenTelemetry Observability & Distributed Tracing ---
    # Trace IDs, correlation IDs, prompt hashes, and token counts for LLM observability dashboards.
    correlation_id: Optional[str]
    otel_trace_id: Optional[str]
    llm_invocation_audit: List[Dict[str, Any]] # per-node LLM audit log (prompt_hash, model_version, temp, span_id)
    token_usage: Dict[str, Any]               # node_name -> {prompt_tokens, completion_tokens}
    latency_ms: Dict[str, float]              # node_name -> elapsed milliseconds

    # --- bookkeeping ---
    errors: List[str]
    _enkrypt_guardrail: Dict[str, Any]        # Enkrypt AI guardrail result (risk_agent)
