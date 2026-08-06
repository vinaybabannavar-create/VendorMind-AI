"""
pipeline/retrieval_agent.py

Node 3 — Vendor Profile Retrieval Agent
Retrieves vendor history, performance reviews, and certifications via
semantic search over the vendor knowledge base.

Step 2 update: vendor upserts now flow through VectorSyncManager
(Write-Through: Vertex AI primary → Qdrant mirror) and reads use the
fallback chain (Vertex AI → Qdrant → in-memory).  The existing
vendor_store functions are kept as a final safety net.

Tech: Python, Vertex AI Vector Search, Qdrant, sentence-transformers
"""

from pipeline.state import VendorMindState
from vectorstore.vendor_store import upsert_vendor_profile, query_similar

# Wire in the Write-Through + Batch-Reconciliation sync manager
try:
    from pipeline.vector_sync import vector_sync  # singleton VectorSyncManager
    _SYNC_AVAILABLE = True
except Exception:
    _SYNC_AVAILABLE = False


def run_retrieval_agent(state: VendorMindState) -> VendorMindState:
    parsed_vendors = state.get("parsed_vendors", [])
    criteria = state.get("criteria", {})

    # Index each vendor's cleaned text via Write-Through sync (Vertex AI → Qdrant)
    for v in parsed_vendors:
        meta = {
            "vendor_name": v.get("vendor_name"),
            "certifications": v.get("extracted", {}).get("certifications_mentioned", []),
        }
        if _SYNC_AVAILABLE:
            try:
                vector_sync.upsert_vendor(
                    vendor_id=v["vendor_id"],
                    text=v["cleaned_text"],
                    metadata=meta,
                )
            except Exception:
                # Fallback to vendor_store if sync manager errors
                upsert_vendor_profile(vendor_id=v["vendor_id"], text=v["cleaned_text"], metadata=meta)
        else:
            upsert_vendor_profile(vendor_id=v["vendor_id"], text=v["cleaned_text"], metadata=meta)

    # Build a query from the extracted criteria so retrieval is criteria-aware
    query_text = " ".join([
        str(criteria.get("past_performance_expectations", "")),
        " ".join(criteria.get("technical_requirements", [])),
        " ".join(criteria.get("compliance_requirements", [])),
    ]).strip() or "general vendor evaluation"

    vendor_context = {}
    for v in parsed_vendors:
        # Use Vertex AI → Qdrant fallback chain; fall back to vendor_store on error
        if _SYNC_AVAILABLE:
            try:
                results = vector_sync.query_similar(query_text, top_k=3)
            except Exception:
                results = query_similar(query_text, top_k=3)
        else:
            results = query_similar(query_text, top_k=3)

        own = [r for r in results if r.get("vendor_id") == v["vendor_id"]]
        vendor_context[v["vendor_id"]] = {
            "retrieved_score": own[0]["score"] if own else 0.0,
            "certifications": v.get("extracted", {}).get("certifications_mentioned", []),
            "vector_sync_active": _SYNC_AVAILABLE,
        }

    state["vendor_context"] = vendor_context
    return state
