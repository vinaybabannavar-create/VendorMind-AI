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


@app.get("/evaluation/{evaluation_id}/report")
def get_audit_report(evaluation_id: str):
    """Returns a print-ready Executive Procurement Audit Report HTML string."""
    result = _evaluations.get(evaluation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    from datetime import datetime, timezone
    final_report = result.get("final_report", {})
    ranking = result.get("comparison_table", [])
    explanations = result.get("explanations", {})
    risk_flags = result.get("risk_flags", {})
    hitl_status = "Approved ✅" if result.get("hitl_approved") else ("Rejected ❌" if result.get("hitl_approved") is False else "Pending Approval ⏳")
    approver_note = result.get("approver_note", "N/A")

    rows_html = ""
    for r in ranking:
        vid = r.get("vendor_id")
        name = r.get("vendor_name", vid)
        rank = r.get("rank", 0)
        comp = r.get("composite_score", 0)
        expl = explanations.get(vid, "N/A")
        flags = risk_flags.get(vid, [])
        flags_str = "<br>• ".join(flags) if flags else "Clean audit (No flags)"

        rows_html += f"""
        <tr style="border-bottom:1px solid #334155;">
            <td style="padding:12px;font-weight:bold;color:#00D4FF;">#{rank}</td>
            <td style="padding:12px;font-weight:bold;">{name}</td>
            <td style="padding:12px;color:#34D399;font-weight:bold;">{comp:.2f} / 1.0</td>
            <td style="padding:12px;font-size:0.9em;color:#CBD5E1;">{expl}</td>
            <td style="padding:12px;font-size:0.85em;color:#F87171;">{flags_str}</td>
        </tr>
        """

    report_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>VendorMind AI — Executive Audit Report ({evaluation_id})</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:#0B1120; color:#F1F5F9; padding:40px; margin:0; }}
            .header {{ border-bottom: 2px solid #00D4FF; padding-bottom: 20px; margin-bottom: 30px; display:flex; justify-content:space-between; align-items:center; }}
            .title {{ font-size: 28px; font-weight: 800; background: linear-gradient(135deg, #00D4FF, #818CF8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .meta {{ font-size: 14px; color: #94A3B8; text-align:right; }}
            .card {{ background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 24px; margin-bottom: 24px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th {{ text-align: left; padding: 12px; background: #0F172A; color: #38BDF8; font-size: 14px; border-bottom: 2px solid #334155; }}
            .badge {{ display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 13px; background: rgba(0, 212, 255, 0.15); color: #00D4FF; border: 1px solid #00D4FF; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <div class="title">VendorMind AI — Executive Procurement Audit Report</div>
                <div style="color:#A5B4FC; margin-top:5px; font-weight:600;">Evaluation ID: {evaluation_id}</div>
            </div>
            <div class="meta">
                <div>Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
                <div>Status: <span class="badge">{hitl_status}</span></div>
            </div>
        </div>

        <div class="card">
            <h3 style="color:#00D4FF; margin-top:0;">🏆 Top Recommendation</h3>
            <p style="font-size:18px; margin:5px 0;">Winning Vendor: <strong>{final_report.get('recommended_vendor', 'N/A')}</strong></p>
            <p style="color:#94A3B8; font-size:14px;">Human Approval Decision: <strong>{hitl_status}</strong> (Note: <em>{approver_note}</em>)</p>
        </div>

        <div class="card">
            <h3 style="color:#38BDF8; margin-top:0;">📊 Vendor Comparison Matrix & AI Justifications</h3>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Vendor Name</th>
                        <th>Composite Score</th>
                        <th>AI Score Rationale (Gemini 2.0)</th>
                        <th>Risk & Bias Audit Flags</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>

        <div style="text-align:center; color:#64748B; font-size:12px; margin-top:40px;">
            VendorMind AI · 8-Node LangGraph Pipeline · Powered by Gemini 2.0 & Enkrypt AI Guardrails
        </div>
    </body>
    </html>
    """
    return {"evaluation_id": evaluation_id, "html": report_html}

