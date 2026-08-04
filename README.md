# 🧠 VendorMind AI

> **Agentic AI Vendor Evaluation System for Procurement Teams**  
> *AI Agent Builder Series 2026 — National Finale (HiDevs × AI House)*

VendorMind AI automates complex, spreadsheet-based vendor evaluation for procurement teams. Utilizing an **8-node stateful LangGraph agent pipeline**, the system transforms raw RFP requirements and vendor submission documents into structured, explainable, and risk-aware shortlists.

---

## 🌟 Key Features

- **Explainable AI**: Every vendor ranking comes with a human-readable justification citing specific evidence.
- **Multi-Signal Scoring**: Combines cost competitiveness, compliance/SLA completeness, timeline fit, semantic capability match, and historical track record.
- **Automated Risk & Bias Guardrails**: Flags dumping risk (unusually low bids), single-vendor over-dependency, missing ISO/SOC2 certs, and SME size bias.
- **Human-in-the-Loop (HITL) Gate**: The AI recommends — the procurement manager approves or requests further due diligence.
- **Audit-Ready Logging**: Every agent step, prompt, and score checkpoint is logged.

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│ TIER 1 — USER INTERFACE                                 │
│   Procurement Manager (Web Browser)                     │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│ TIER 2 — FRONTEND DASHBOARD                             │
│   Procurement Dashboard (Streamlit, Python)             │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│ TIER 3 — API GATEWAY                                    │
│   VendorMind API Gateway (FastAPI, Cloud Run)           │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│ TIER 4 — AGENT ORCHESTRATION                            │
│   Agent Orchestrator (LangGraph Stateful Graph)         │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│ TIER 5 — 8-NODE VERTICAL AGENTIC PIPELINE WORKERS       │
│                                                         │
│   1. Intake Agent (Parsing PDFs/RFP/Submissions)        │
│        ↓                                                │
│   2. Criteria Extraction Agent (Gemini 1.5 Pro)         │
│        ↓                                                │
│   3. Vendor Profile Retrieval Agent (Vector Search)     │
│        ↓                                                │
│   4. Multi-Signal Scoring Agent (Composite Rules)       │
│        ↓                                                │
│   5. Risk & Bias Detection Agent (Guardrail Audit)      │
│        ↓                                                │
│   6. Explanation Generation Agent (Gemini 1.5 Pro)      │
│        ↓                                                │
│   7. Comparison Agent (Side-by-Side Matrix)             │
│        ↓                                                │
│   8. Output & HITL Agent (Pending Human Approval)       │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│ TIER 6 — DATA & PERSISTENCE LAYER                       │
│   - Gemini 1.5 Pro API (Vertex AI)                      │
│   - Vendor Knowledge Base (Vertex AI Vector Search)     │
│   - Audit & State Store (BigQuery)                      │
│   - Document Storage (Google Cloud Storage)             │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

- **LLM & Reasoning**: Gemini 1.5 Pro (Google AI Studio / Vertex AI)
- **Agent Orchestration**: LangGraph, Agent Development Kit (ADK)
- **Tooling Protocol**: Model Context Protocol (MCP)
- **Backend API**: FastAPI, Python 3.11+, Pydantic
- **Frontend**: Streamlit
- **Vector Search**: Vertex AI Vector Search / ChromaDB
- **Deployment**: Docker, Cloud Run
- **Audit & Persistence**: BigQuery, Cloud Storage

---

## 🚀 Quick Start (Local Run)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables (Optional)
```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

### 3. Run FastAPI Backend
```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### 4. Run Streamlit Dashboard
```bash
streamlit run ui/app.py
```

Open `http://localhost:8501` in your browser to launch the dashboard.

---

## 📄 Key Documentation Files

- [`PRD.md`](./PRD.md) — Complete Product Requirements Document
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — System Architecture & Node Specs
- Diagram ID: `12b1f6c1-82d5-4c3d-9f2d-e69e126c7261` (National Finale Arena Submission)

---

## 🏆 National Finale Submission Checklist

- [x] Step 1: Architecture Copilot Submission (Saved & Submitted)
- [x] Step 2: Dr. Agent Repository Audit Ready
- [x] 8-Node LangGraph Agent Pipeline Executable
- [x] Explainable AI Decision Justifications Included
- [x] Risk & Bias Detection Guardrails Active
- [x] Human-in-the-Loop Approval Workflow Integrated
