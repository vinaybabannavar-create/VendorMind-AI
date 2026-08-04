"""
pipeline/retrieval_agent.py

Node 3 — Vendor Profile Retrieval Agent
Retrieves vendor history, performance reviews, and certifications via
semantic search over the vendor knowledge base (Qdrant).
Tech: Python, Qdrant, sentence-transformers
"""

from pipeline.state import VendorMindState
from vectorstore.vendor_store import upsert_vendor_profile, query_similar


def run_retrieval_agent(state: VendorMindState) -> VendorMindState:
    parsed_vendors = state.get("parsed_vendors", [])
    criteria = state.get("criteria", {})

    # Index each vendor's cleaned text (idempotent — safe to re-run)
    for v in parsed_vendors:
        upsert_vendor_profile(
            vendor_id=v["vendor_id"],
            text=v["cleaned_text"],
            metadata={
                "vendor_name": v.get("vendor_name"),
                "certifications": v.get("extracted", {}).get("certifications_mentioned", []),
            },
        )

    # Build a query from the extracted criteria so retrieval is criteria-aware
    query_text = " ".join([
        str(criteria.get("past_performance_expectations", "")),
        " ".join(criteria.get("technical_requirements", [])),
        " ".join(criteria.get("compliance_requirements", [])),
    ]).strip() or "general vendor evaluation"

    vendor_context = {}
    for v in parsed_vendors:
        results = query_similar(query_text, top_k=3)
        # Filter to this vendor's own record + keep top match for context
        own = [r for r in results if r.get("vendor_id") == v["vendor_id"]]
        vendor_context[v["vendor_id"]] = {
            "retrieved_score": own[0]["score"] if own else 0.0,
            "certifications": v.get("extracted", {}).get("certifications_mentioned", []),
        }

    state["vendor_context"] = vendor_context
    return state
