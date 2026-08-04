"""
pipeline/criteria_agent.py

Node 2 — Criteria Extraction Agent
Uses Gemini to extract explicit and implicit evaluation criteria from
the RFP text into a structured schema (cost, timeline, compliance,
technical capability, past-performance expectations).
Tech: Python, LangGraph, Gemini 1.5 Pro, MCP (tool-call framing)
"""

import json
from pipeline.state import VendorMindState
from pipeline.llm_client import gemini_generate

_PROMPT_TEMPLATE = """You are a procurement analyst. Extract structured evaluation
criteria from the RFP text below. Return ONLY valid JSON, no prose, matching
this schema exactly:

{{
  "cost_weight": <0-1 float>,
  "compliance_requirements": [<string>, ...],
  "delivery_timeline_days": <int or null>,
  "technical_requirements": [<string>, ...],
  "past_performance_expectations": <string>
}}

RFP TEXT:
\"\"\"{rfp_text}\"\"\"
"""

_DEFAULT_CRITERIA = {
    "cost_weight": 0.4,
    "compliance_requirements": [],
    "delivery_timeline_days": None,
    "technical_requirements": [],
    "past_performance_expectations": "Not specified",
}


def _safe_parse_json(text: str) -> dict:
    try:
        # Strip markdown code fences if present
        cleaned = text.strip().strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        return json.loads(cleaned)
    except Exception:
        return dict(_DEFAULT_CRITERIA)


def run_criteria_agent(state: VendorMindState) -> VendorMindState:
    rfp_text = state.get("parsed_rfp", {}).get("cleaned_text", "")
    if not rfp_text:
        state["criteria"] = dict(_DEFAULT_CRITERIA)
        return state

    prompt = _PROMPT_TEMPLATE.format(rfp_text=rfp_text[:6000])
    raw = gemini_generate(prompt, expect_json=True)
    criteria = _safe_parse_json(raw)

    # Fill in any missing keys with defaults rather than trusting the LLM blindly
    for key, default in _DEFAULT_CRITERIA.items():
        criteria.setdefault(key, default)

    state["criteria"] = criteria
    return state
