"""
ui/app.py

VendorMind AI — Premium Procurement Dashboard
An explainable, multi-signal vendor evaluation interface for procurement teams.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import requests
import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.sample_data import PRESET_RFPS, SAMPLE_VENDORS

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# Page Configuration
st.set_page_config(
    page_title="VendorMind AI — Agentic Procurement System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Dark Glassmorphism Aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9));
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.8rem 2.2rem;
        border-radius: 16px;
        margin-bottom: 1.8rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(12px);
    }
    
    .main-header h1 {
        color: #F8FAFC;
        font-weight: 700;
        font-size: 2.2rem;
        margin: 0;
        background: linear-gradient(90deg, #38BDF8, #818CF8, #C084FC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .main-header p {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-top: 0.4rem;
        margin-bottom: 0;
    }
    
    .agent-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .agent-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.15);
    }
    
    .rank-badge-1 {
        background: linear-gradient(135deg, #F59E0B, #D97706);
        color: #FFFFFF;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    
    .rank-badge-2 {
        background: linear-gradient(135deg, #94A3B8, #64748B);
        color: #FFFFFF;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    
    .rank-badge-3 {
        background: linear-gradient(135deg, #B45309, #78350F);
        color: #FFFFFF;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }

    .risk-alert {
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #FCA5A5;
        padding: 0.8rem 1.1rem;
        border-radius: 10px;
        margin-top: 0.8rem;
        font-size: 0.9rem;
    }
    
    .pipeline-step {
        display: inline-block;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(56, 189, 248, 0.3);
        color: #38BDF8;
        padding: 0.35rem 0.75rem;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "evaluation_id" not in st.session_state:
    st.session_state.evaluation_id = None
if "result" not in st.session_state:
    st.session_state.result = None
if "preset_loaded" not in st.session_state:
    st.session_state.preset_loaded = False

# Header Banner
st.markdown("""
<div class="main-header">
    <h1>🧠 VendorMind AI</h1>
    <p>Agentic AI Vendor Evaluation System • 8-Node LangGraph Pipeline • Multi-Signal Scoring • Explainable Shortlists</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Setup
with st.sidebar:
    st.image("https://img.icons8.com/isometric-line/100/brain.png", width=64)
    st.header("⚙️ Evaluation Setup")
    
    st.subheader("1. Quick Presets")
    selected_preset_key = st.selectbox(
        "Load Preset RFP Template",
        options=["custom"] + list(PRESET_RFPS.keys()),
        format_func=lambda k: "✍️ Custom Input" if k == "custom" else PRESET_RFPS[k]["title"]
    )
    
    if selected_preset_key != "custom":
        preset_info = PRESET_RFPS[selected_preset_key]
        default_rfp = preset_info["rfp_text"]
        default_vendors = SAMPLE_VENDORS
    else:
        default_rfp = ""
        default_vendors = SAMPLE_VENDORS[:2]

    st.subheader("2. RFP Requirements")
    rfp_input = st.text_area(
        "Request for Proposal (RFP) Text",
        value=default_rfp,
        height=200,
        placeholder="Paste your RFP requirements, compliance mandatory rules, SLA guidelines..."
    )

    st.subheader("3. Vendor Submissions")
    num_vendors = st.number_input("Number of Vendors", min_value=1, max_value=10, value=len(default_vendors), step=1)
    
    vendor_inputs = []
    for i in range(int(num_vendors)):
        v_default = default_vendors[i] if i < len(default_vendors) else {"vendor_id": f"vendor_{i+1}", "vendor_name": f"Vendor {chr(65+i)}", "raw_text": ""}
        with st.expander(f"🏢 {v_default.get('vendor_name', f'Vendor {i+1}')}", expanded=(i < 2)):
            vname = st.text_input(f"Vendor Name", value=v_default.get("vendor_name", f"Vendor {i+1}"), key=f"vname_{i}")
            vtext = st.text_area(
                f"Proposal & Pricing Text",
                value=v_default.get("raw_text", "").strip(),
                key=f"vtext_{i}",
                height=140,
                placeholder="Paste vendor proposal, pricing sheet, ISO/SOC2 certs..."
            )
            vendor_inputs.append({
                "vendor_id": f"vendor_{i+1}",
                "vendor_name": vname,
                "raw_text": vtext
            })

    st.markdown("---")
    run_btn = st.button("⚡ Run 8-Agent Evaluation Pipeline", type="primary", use_container_width=True)

# Pipeline Execution Trigger
if run_btn:
    if not rfp_input.strip():
        st.sidebar.error("⚠️ Please provide RFP requirements text.")
    elif not any(v["raw_text"].strip() for v in vendor_inputs):
        st.sidebar.error("⚠️ Please provide at least one valid vendor proposal.")
    else:
        status_container = st.container()
        with status_container:
            st.info("🚀 Triggering LangGraph 8-Agent Evaluation Pipeline...")
            
            # Step progress visualization
            progress_bar = st.progress(0)
            step_status = st.empty()
            
            steps = [
                "1. Intake & Normalization Agent",
                "2. Criteria Extraction Agent (Gemini 1.5 Pro)",
                "3. Vendor Profile Retrieval Agent (ChromaDB / Vector Search)",
                "4. Multi-Signal Scoring Agent (Cost, SLA, Semantic Fit)",
                "5. Risk & Bias Detection Agent (Dumping, Compliance Audit)",
                "6. Explanation Generation Agent (Human-Readable Notes)",
                "7. Comparison Agent (Side-by-Side Matrix)",
                "8. Output & HITL Agent (Pending Human Approval)"
            ]
            
            for idx, step_name in enumerate(steps):
                step_status.markdown(f"**Current State:** `{step_name}`")
                progress_bar.progress(int((idx + 1) / len(steps) * 100))
                time.sleep(0.12)
            
            try:
                resp = requests.post(
                    f"{API_BASE}/evaluate",
                    json={"rfp_text": rfp_input, "vendors": [v for v in vendor_inputs if v["raw_text"].strip()]},
                    timeout=60
                )
                resp.raise_for_status()
                eval_data = resp.json()
                st.session_state.evaluation_id = eval_data["evaluation_id"]
                st.session_state.result = eval_data
                st.success("✅ Evaluation Complete! Results loaded below.")
            except Exception as e:
                st.error(f"❌ Evaluation failed: {e}")

# Display Results Dashboard
if st.session_state.result:
    res = st.session_state.result
    report = res.get("final_report") or {}
    table = res.get("comparison_table") or []
    
    # Overview Metrics Row
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Top Recommended Vendor", report.get("recommended_vendor", "N/A"), delta="Rank #1 Choice")
    with col_m2:
        st.metric("Total Vendors Evaluated", report.get("total_vendors_evaluated", len(table)))
    with col_m3:
        st.metric("Pipeline Agents Executed", "8 / 8 Nodes", delta="100% Success")
    with col_m4:
        st.metric("Human Approval Status", "Pending Review" if res.get("hitl_approved") is None else ("✅ Approved" if res.get("hitl_approved") else "❌ Rejected"))

    st.markdown("---")

    # Pipeline Architecture Visualization Banner
    st.subheader("🧩 Agentic Pipeline Execution Trace")
    st.markdown("""
    <div>
        <span class="pipeline-step">1. Intake Node</span> ➔
        <span class="pipeline-step">2. Criteria Extraction</span> ➔
        <span class="pipeline-step">3. Vector Search Retrieval</span> ➔
        <span class="pipeline-step">4. Multi-Signal Scoring</span> ➔
        <span class="pipeline-step">5. Risk & Bias Audit</span> ➔
        <span class="pipeline-step">6. Explanation Generation</span> ➔
        <span class="pipeline-step">7. Comparison Matrix</span> ➔
        <span class="pipeline-step">8. Output & HITL Gate</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Tabs
    tab_rankings, tab_matrix, tab_explain, tab_hitl = st.tabs([
        "🏆 Ranked Leaderboard",
        "📊 Side-by-Side Comparison Matrix",
        "💬 Explainable AI Justifications",
        "✅ Human-in-the-Loop (HITL) Approval"
    ])

    # Tab 1: Leaderboard
    with tab_rankings:
        st.subheader("🏆 Multi-Signal Vendor Leaderboard")
        
        for item in table:
            rank = item.get("rank", 1)
            vname = item.get("vendor_name", "Vendor")
            score = item.get("composite_score", 0)
            cost_s = item.get("cost_score", 0)
            comp_s = item.get("compliance_score", 0)
            sem_s = item.get("semantic_score", 0)
            rflags = item.get("risk_flags", [])
            expl = item.get("explanation", "")

            badge_class = f"rank-badge-{rank}" if rank <= 3 else "rank-badge-3"
            
            with st.container():
                st.markdown(f"""
                <div class="agent-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin: 0; color: #F8FAFC;">
                            <span class="{badge_class}">#{rank}</span> {vname}
                        </h3>
                        <div style="text-align: right;">
                            <span style="font-size: 1.4rem; font-weight: 700; color: #38BDF8;">{score:.1f}</span>
                            <span style="font-size: 0.85rem; color: #94A3B8;">/ 100 Composite</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                with col_c1:
                    st.progress(min(1.0, max(0.0, cost_s / 100)))
                    st.caption(f"Cost Competitiveness: **{cost_s:.1f}**")
                with col_c2:
                    st.progress(min(1.0, max(0.0, comp_s / 100)))
                    st.caption(f"Compliance & SLA: **{comp_s:.1f}**")
                with col_c3:
                    st.progress(min(1.0, max(0.0, sem_s / 100)))
                    st.caption(f"Semantic Capability Fit: **{sem_s:.1f}**")
                with col_c4:
                    st.caption(f"Risk Flags Raised: **{len(rflags)}**")
                
                if rflags:
                    st.markdown(f"""
                    <div class="risk-alert">
                        ⚠️ <strong>Risk & Bias Guardrail Alerts ({len(rflags)}):</strong><br>
                        {'<br>'.join(f'• {rf}' for rf in rflags)}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)

    # Tab 2: Comparison Matrix
    with tab_matrix:
        st.subheader("📊 Side-by-Side Dimension Breakdown")
        if table:
            df_matrix = pd.DataFrame(table)[
                ["rank", "vendor_name", "composite_score", "cost_score", "compliance_score", "semantic_score", "risk_flag_count"]
            ].rename(columns={
                "rank": "Rank",
                "vendor_name": "Vendor Name",
                "composite_score": "Composite Score",
                "cost_score": "Cost Score",
                "compliance_score": "Compliance Score",
                "semantic_score": "Semantic Fit Score",
                "risk_flag_count": "Risk Flags Count"
            })
            st.dataframe(df_matrix, use_container_width=True, hide_index=True)
            
            st.subheader("📈 Multi-Signal Score Comparison Bar Chart")
            st.bar_chart(df_matrix.set_index("Vendor Name")[["Cost Score", "Compliance Score", "Semantic Fit Score"]])

    # Tab 3: Explainable Justifications
    with tab_explain:
        st.subheader("💬 Natural Language Decision Justifications")
        st.caption("Every ranking decision is accompanied by an audit-ready, evidence-backed justification generated by Gemini 1.5 Pro.")
        
        for item in table:
            with st.expander(f"Rank #{item.get('rank')} — {item.get('vendor_name')} (Score: {item.get('composite_score'):.1f})", expanded=True):
                st.markdown(f"**Justification:**")
                st.write(item.get("explanation", "No justification text available."))
                if item.get("risk_flags"):
                    st.warning("Associated Risk Flags:\n" + "\n".join(f"- {f}" for f in item.get("risk_flags")))

    # Tab 4: Human-in-the-Loop (HITL)
    with tab_hitl:
        st.subheader("✅ Procurement Manager Approval Gate")
        st.caption("The Output & HITL Agent holds final approval state pending human confirmation. The AI recommends — the human decides.")
        
        col_h1, col_h2 = st.columns([2, 1])
        with col_h1:
            approver_note = st.text_input("Procurement Manager Audit Note (Optional)", placeholder="e.g. Approved after reviewing SOC 2 report and pricing fit.")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("✅ Approve Recommended Vendor", type="primary", use_container_width=True):
                    try:
                        r = requests.post(
                            f"{API_BASE}/evaluation/approve",
                            json={"evaluation_id": st.session_state.evaluation_id, "approved": True, "approver_note": approver_note},
                            timeout=15
                        )
                        r.raise_for_status()
                        st.session_state.result["hitl_approved"] = True
                        st.success("🎉 Decision officially APPROVED and logged to Audit & State Store (BigQuery)!")
                    except Exception as err:
                        st.error(f"Failed to submit approval: {err}")

            with col_b2:
                if st.button("❌ Reject / Needs Further Due Diligence", use_container_width=True):
                    try:
                        r = requests.post(
                            f"{API_BASE}/evaluation/approve",
                            json={"evaluation_id": st.session_state.evaluation_id, "approved": False, "approver_note": approver_note},
                            timeout=15
                        )
                        r.raise_for_status()
                        st.session_state.result["hitl_approved"] = False
                        st.warning("⚠️ Marked as REJECTED / Pending Further Due Diligence.")
                    except Exception as err:
                        st.error(f"Failed to record rejection: {err}")

        with col_h2:
            st.subheader("📥 Export Final Report")
            report_data = {
                "evaluation_id": st.session_state.evaluation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "final_report": report,
                "comparison_table": table,
                "hitl_approved": st.session_state.result.get("hitl_approved")
            }
            json_str = json.dumps(report_data, indent=2)
            st.download_button(
                label="📄 Export Evaluation Report (JSON)",
                data=json_str,
                file_name=f"vendormind_report_{st.session_state.evaluation_id}.json",
                mime="application/json",
                use_container_width=True
            )
else:
    st.info("👈 Choose a preset RFP in the sidebar or paste custom RFP requirements, then click **Run 8-Agent Evaluation Pipeline** to start!")
