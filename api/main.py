"""
api/main.py

VendorMind API Gateway
FastAPI gateway serving evaluation, ranking, comparison, and human
approval endpoints. Internal-only in the Render deployment (bound to
127.0.0.1) — the Streamlit dashboard is the public surface.
Tech: FastAPI, Pydantic, Uvicorn
"""

import sys
import os
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from pipeline.orchestrator import run_pipeline

app = FastAPI(title="VendorMind AI API", version="1.0.0")

# In-memory store of the last evaluation per session — swap for a real
# DB (e.g. the Audit & State Store / BigQuery) in production.
_evaluations: dict = {}


class VendorInput(BaseModel):
    vendor_id: str
    vendor_name: Optional[str] = None
    raw_text: str


class EvaluateRequest(BaseModel):
    rfp_text: str
    vendors: List[VendorInput]


class ApprovalRequest(BaseModel):
    evaluation_id: str
    approved: bool
    approver_note: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/evaluate")
def evaluate(req: EvaluateRequest):
    if not req.vendors:
        raise HTTPException(status_code=400, detail="At least one vendor is required")

    vendors_payload = [v.model_dump() for v in req.vendors]
    result = run_pipeline(rfp_text=req.rfp_text, vendors=vendors_payload)

    evaluation_id = f"eval_{len(_evaluations) + 1}"
    _evaluations[evaluation_id] = result

    return {
        "evaluation_id": evaluation_id,
        "final_report": result.get("final_report"),
        "comparison_table": result.get("comparison_table"),
    }


@app.get("/evaluation/{evaluation_id}")
def get_evaluation(evaluation_id: str):
    result = _evaluations.get(evaluation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return result


@app.get("/evaluation/{evaluation_id}/comparison")
def get_comparison(evaluation_id: str):
    result = _evaluations.get(evaluation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return {"comparison_table": result.get("comparison_table", [])}


@app.get("/evaluation/{evaluation_id}/explain/{vendor_id}")
def explain_vendor(evaluation_id: str, vendor_id: str):
    result = _evaluations.get(evaluation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    explanation = result.get("explanations", {}).get(vendor_id)
    if explanation is None:
        raise HTTPException(status_code=404, detail="Vendor not found in this evaluation")
    return {"vendor_id": vendor_id, "explanation": explanation}


@app.post("/evaluation/approve")
def approve(req: ApprovalRequest):
    """Human-in-the-loop approval endpoint — called from the
    Procurement Dashboard, closing the loop shown in the architecture
    diagram from Output & HITL Agent back to the frontend."""
    result = _evaluations.get(req.evaluation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    result["hitl_approved"] = req.approved
    result["approver_note"] = req.approver_note
    return {
        "evaluation_id": req.evaluation_id,
        "hitl_approved": req.approved,
        "message": "Approval recorded",
    }
