# VendorMind AI — System Architecture

## Overview

VendorMind AI is a stateful, multi-agent system orchestrated as a directed graph. It transforms raw RFP documents and vendor submissions into explainable, ranked shortlists through 8 specialized agents, each with a clearly defined responsibility. Every decision is auditable, every score is explainable, and a human must approve the final selection.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ TIER 1 — USER TIER                                              │
│   Procurement Manager (Web Browser)                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ TIER 2 — FRONTEND TIER                                          │
│   Procurement Dashboard (Streamlit, Python)                     │
│   - Upload RFP & vendor proposals                               │
│   - View ranked comparison & explanations                       │
│   - Human-in-the-loop approval interface                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP / REST API
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ TIER 3 — API GATEWAY TIER                                       │
│   VendorMind API Gateway (FastAPI, Python, Cloud Run)           │
│   - POST /v1/evaluate                                           │
│   - GET  /v1/status/{job_id}                                    │
│   - GET  /v1/comparison/{job_id}                                │
│   - POST /v1/approve                                            │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Internal API
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ TIER 4 — ORCHESTRATION TIER                                     │
│   Agent Orchestrator (LangGraph, Python, ADK)                   │
│   - Manages stateful agent pipeline and state transitions       │
│   - Dispatches tasks to each specialized agent node             │
│   - Persists state checkpoints to Audit & State Store           │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Internal API
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ TIER 5 — AGENTIC PIPELINE TIER (8-Node Vertical Chain)          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Node 1: Intake Agent                                    │   │
│  │ Tech: Python, PyPDF2, BeautifulSoup, MCP               │──────→ Document Storage (GCS)
│  │ Parses and normalizes RFP and vendor documents          │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │ Parsed Docs                       │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Node 2: Criteria Extraction Agent                       │   │
│  │ Tech: Python, LangGraph, Gemini 1.5 Pro                │──────→ Gemini LLM API
│  │ Extracts evaluation criteria into structured schema     │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │ Criteria Schema                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Node 3: Vendor Profile Retrieval Agent                  │   │
│  │ Tech: Python, Vertex AI Vector Search                   │──────→ Vendor Knowledge Base
│  │ Retrieves vendor history, certifications via vector     │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │ Vendor Context                    │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Node 4: Multi-Signal Scoring Agent                      │   │
│  │ Tech: Python, Gemini 1.5 Pro, NumPy                     │──────→ Gemini LLM API
│  │ Computes composite scores (cost, SLA, semantic fit)     │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │ Raw Scores                        │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Node 5: Risk & Bias Detection Agent                     │   │
│  │ Tech: Python, Gemini 1.5 Pro                            │──────→ Gemini LLM API
│  │ Flags dumping, compliance gaps, size bias               │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │ Risk Signals                      │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Node 6: Explanation Generation Agent                    │   │
│  │ Tech: Python, Gemini 1.5 Pro                            │──────→ Gemini LLM API
│  │ Generates human-readable score justifications           │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │ Justifications                    │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Node 7: Comparison Agent                                │   │
│  │ Tech: Python, Pandas                                    │   │
│  │ Generates side-by-side structured comparison matrix     │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │ Shortlist Data                    │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Node 8: Output & HITL Agent                             │   │
│  │ Tech: Python, LangGraph, Streamlit                      │──────→ Dashboard (HITL Approval)
│  │ Produces final report & awaits human approval           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                      │ Audit Logs & State
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ TIER 6 — DATA & LLM TIER                                        │
│                                                                 │
│   ┌─────────────────────┐   ┌──────────────────────────────┐   │
│   │  Gemini LLM API     │   │  Vendor Knowledge Base       │   │
│   │  Gemini 1.5 Pro     │   │  Vertex AI Vector Search     │   │
│   │  Vertex AI          │   │  ChromaDB                    │   │
│   └─────────────────────┘   └──────────────────────────────┘   │
│                                                                 │
│   ┌─────────────────────┐   ┌──────────────────────────────┐   │
│   │  Audit & State      │   │  Document Storage            │   │
│   │  Store              │   │  Google Cloud Storage        │   │
│   │  BigQuery, Cloud SQL│   │  (Raw RFP & Vendor PDFs)     │   │
│   └─────────────────────┘   └──────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Node Specifications

### Tier 1 — User Tier
| Node | Type | Description | Tech |
|------|------|-------------|------|
| Procurement Manager | Client | Primary user interacting with the dashboard | Web Browser |

### Tier 2 — Frontend Tier
| Node | Type | Description | Tech |
|------|------|-------------|------|
| Procurement Dashboard | Frontend | Streamlit UI for RFP upload, vendor ranking, drill-down explanations, and HITL approval | Streamlit, Python |

### Tier 3 — API Gateway Tier
| Node | Type | Description | Tech |
|------|------|-------------|------|
| VendorMind API Gateway | API Gateway | FastAPI gateway exposing evaluation, ranking, comparison, and approval endpoints | FastAPI, Python, Cloud Run |

### Tier 4 — Orchestration Tier
| Node | Type | Description | Tech |
|------|------|-------------|------|
| Agent Orchestrator | Service | Stateful LangGraph directed graph managing state transitions across all 8 agent nodes | LangGraph, Python, ADK |

### Tier 5 — Agentic Pipeline Tier
| Node | Agent | Responsibility | Tech |
|------|-------|---------------|------|
| Node 1 | Intake Agent | Parses and normalizes RFP and vendor documents (PDFs, pricing sheets, certificates) | Python, PyPDF2, BeautifulSoup, MCP |
| Node 2 | Criteria Extraction Agent | Extracts explicit and implicit evaluation criteria from RFP into a structured schema | Python, LangGraph, Gemini 1.5 Pro |
| Node 3 | Vendor Profile Retrieval Agent | Semantic vector search over vendor knowledge base for past performance and certifications | Python, Vertex AI Vector Search |
| Node 4 | Multi-Signal Scoring Agent | Computes composite scores from cost, compliance, timeline, semantic fit, and historical signals | Python, Gemini 1.5 Pro, NumPy |
| Node 5 | Risk & Bias Detection Agent | Flags single-vendor dependency, dumping risk, missing compliance documentation, and SME bias | Python, Gemini 1.5 Pro |
| Node 6 | Explanation Generation Agent | Generates human-readable justifications for each vendor's rank citing specific evidence | Python, Gemini 1.5 Pro |
| Node 7 | Comparison Agent | Produces a structured side-by-side matrix of top-N vendors across all scored dimensions | Python, Pandas |
| Node 8 | Output & HITL Agent | Produces the final ranked report and holds state pending human approval via the dashboard | Python, LangGraph, Streamlit |

### Tier 6 — Data & LLM Tier
| Node | Type | Description | Tech |
|------|------|-------------|------|
| Gemini LLM API | LLM Service | LLM reasoning and generation for Nodes 2, 4, 5, and 6 | Gemini 1.5 Pro, Vertex AI |
| Vendor Knowledge Base | Vector Database | Semantic storage for vendor profiles, past contracts, and history | Vertex AI Vector Search, ChromaDB |
| Audit & State Store | Database | Full audit trail of agent decisions, LLM prompts/responses, and state checkpoints | BigQuery, Cloud SQL |
| Document Storage | Object Storage | Raw RFP PDFs and vendor proposal documents | Google Cloud Storage |

---

## Data Flow

```
RFP Text + Vendor Proposals
        ↓
   Intake Agent       ──────→ Document Storage (GCS)
        ↓
Criteria Extraction   ──────→ Gemini LLM API
        ↓
 Vendor Retrieval     ──────→ Vendor Knowledge Base (Vector Search)
        ↓
 Multi-Signal Score   ──────→ Gemini LLM API
        ↓
Risk & Bias Audit     ──────→ Gemini LLM API
        ↓
Explanation Generation ─────→ Gemini LLM API
        ↓
  Comparison Matrix
        ↓
 Output & HITL        ──────→ Dashboard (Human Approval)
        ↓
  Audit & State Store (BigQuery) ← Agent Orchestrator
```

---

## Edge Connections (from Architecture Copilot JSON)

| Edge ID | Source | Target | Protocol |
|---------|--------|--------|----------|
| user-to-dash | Procurement Manager | Procurement Dashboard | HTTP |
| dash-to-gw | Procurement Dashboard | VendorMind API Gateway | HTTP |
| gw-to-orch | VendorMind API Gateway | Agent Orchestrator | Internal API |
| orch-to-intake | Agent Orchestrator | Intake Agent | Internal API |
| intake-to-criteria | Intake Agent | Criteria Extraction Agent | Internal API |
| criteria-to-retrieval | Criteria Extraction Agent | Vendor Profile Retrieval Agent | Internal API |
| retrieval-to-scoring | Vendor Profile Retrieval Agent | Multi-Signal Scoring Agent | Internal API |
| scoring-to-risk | Multi-Signal Scoring Agent | Risk & Bias Detection Agent | Internal API |
| risk-to-explanation | Risk & Bias Detection Agent | Explanation Generation Agent | Internal API |
| explanation-to-comp | Explanation Generation Agent | Comparison Agent | Internal API |
| comp-to-output | Comparison Agent | Output & HITL Agent | Internal API |
| hitl-to-dashboard | Output & HITL Agent | Procurement Dashboard | HTTP (HITL Approval) |
| orch-to-audit | Agent Orchestrator | Audit & State Store | Database |
| intake-to-gcs | Intake Agent | Document Storage | Database |
| retrieval-to-vector | Vendor Profile Retrieval Agent | Vendor Knowledge Base | Database |
| criteria-to-llm | Criteria Extraction Agent | Gemini LLM API | gRPC |
| scoring-to-llm | Multi-Signal Scoring Agent | Gemini LLM API | gRPC |
| risk-to-llm | Risk & Bias Detection Agent | Gemini LLM API | gRPC |
| explanation-to-llm | Explanation Generation Agent | Gemini LLM API | gRPC |

---

## Technology Stack Summary

| Layer | Technology |
|-------|------------|
| LLM & Reasoning | Gemini 1.5 Pro (Vertex AI / Google AI Studio) |
| Agent Orchestration | LangGraph, Agent Development Kit (ADK) |
| Tooling Protocol | Model Context Protocol (MCP) |
| Backend API | FastAPI, Python, Pydantic |
| Frontend | Streamlit, Python |
| Vector Search | Vertex AI Vector Search, ChromaDB |
| Deployment | Cloud Run (Serverless Docker containers) |
| Audit & State Storage | BigQuery, Cloud SQL |
| Document Storage | Google Cloud Storage (GCS) |

---

## Key Differentiators

- **Full Explainability**: Every ranking decision is accompanied by a human-readable justification citing specific evidence (e.g. cost delta %, compliance status, track record years).
- **Built-in Risk & Bias Detection**: Automated guardrails flag dumping risk, single-vendor dependency, missing ISO/SOC2 compliance, and criteria that unfairly disadvantage smaller vendors.
- **Human-in-the-Loop Final Approval**: The Output & HITL Agent explicitly holds the final state pending a Procurement Manager's Go/No-Go decision via the dashboard — the system never auto-selects a winner.
- **Full Audit Trail**: Every agent decision, LLM prompt, and evaluation step is persisted in BigQuery for compliance and reproducibility.

---

## Architecture Diagram ID
- **Diagram ID**: `12b1f6c1-82d5-4c3d-9f2d-e69e126c7261`
- **Version**: 1.0
- **Cloud Provider**: Google Cloud Platform (GCP)
