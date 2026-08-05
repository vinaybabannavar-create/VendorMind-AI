<div align="center">

# 🧠 VendorMind AI
### **Enterprise Procurement Intelligence Platform**
*Stateful 8-Agent LangGraph Pipeline · Gemma 3 27B-IT Edge Privacy Gate · Google A2A Protocol · Decoupled Cloud Pub/Sub Microservices*

[![Hackathon](https://img.shields.io/badge/HiDevs-National%20Finale%202026-00D4FF?style=for-the-badge&logo=googlecloud&logoColor=white)](https://hidevs.ai)
[![Track](https://img.shields.io/badge/Track-Vendor%20Evaluation-8B5CF6?style=for-the-badge)](https://hidevs.ai)
[![Stack](https://img.shields.io/badge/Google%20Stack-10%2F10%20Met-34D399?style=for-the-badge&logo=google)](https://github.com/vinaybabannavar-create/VendorMind-AI)
[![License](https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge)](./LICENSE)

<br/>

</div>

---

## 🚀 Executive Overview

**VendorMind AI** is an enterprise-grade AI procurement platform designed to transform slow, manual, spreadsheet-based Request for Proposal (RFP) evaluations into **explainable, compliant, and multi-signal AI decisions**. 

Engineered with an **8-node stateful agentic graph (LangGraph)**, **Google Cloud Pub/Sub decoupled microservices**, and **Gemma 3 27B-IT edge privacy filtering**, VendorMind AI evaluates complex RFP requirements against multi-vendor proposals in **under 45 seconds** — while guaranteeing strict **GDPR Article 5/13/14 privacy**, **EEOC 4/5ths Rule bias mitigation**, and **OWASP Top 10 API security**.

---

## 🏆 10/10 Mandatory Hackathon Stack Architecture

| Mandatory Stack Component | Architectural Role & Implementation |
|---|---|
| **Google AI Studio** | Primary API gateway endpoint for deep qualitative LLM reasoning. |
| **Gemini 1.5 Pro** | Core reasoning LLM for Criteria Extraction, Risk Analysis, and Explanation Generation. |
| **Gemma 3 27B-IT** | On-device lightweight model executing **edge PII redaction** at Node 1 (GDPR Article 5). |
| **Antigravity (AGY)** | AI-assisted development layer managing stateful graph transitions & 12-Factor App standards. |
| **Google ADK** | Agent Development Kit for structured agent scaffolding and tool registration. |
| **MCP (Model Context Protocol)** | Context injection & tool grounding for Gemini during criteria extraction. |
| **A2A Protocol** | Google's Agent-to-Agent spec for direct, decentralised Scoring ↔ Risk negotiation. |
| **Vertex AI** | Managed model serving, Vertex AI Vector Search (knowledge base), and Gemma hosting. |
| **Cloud Run** | 12-Factor App serverless container hosting for FastAPI gateway & Streamlit UI. |
| **BigQuery** | Immutable Audit & State Store (90-day TTL, complete A2A message logs, HITL decisions). |

---

## 📐 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 1 — CLIENT & UI (Streamlit Dashboard)                                              │
│   • Neural Glassmorphic Dashboard (Port 8516)                                           │
│   • GDPR Article 13/14 Vendor Consent Capture Checkbox                                   │
│   • 1-v-1 Cyber Duel Matrix · Enkrypt AI Telemetry Badges · Web Speech API Audio Engine │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │ (HTTPS / TLS 1.3 / OAuth2 Bearer JWT)
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 2 — SECURITY GATEWAY & CONSENT ENGINE (FastAPI / Cloud Run)                        │
│   • OAuth2 Bearer / JWT Token Authentication (`POST /token`)                            │
│   • GDPR Art. 13 Consent Capture & Art. 14 Transparency Disclosure (`POST /v1/consent`) │
│   • OWASP A03 Input Validation (Pydantic v2) & OWASP A07 Rate Limiting (100 req/min/IP)    │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 3 — EVENT BUS & DECOUPLED MICROSERVICES (Google Cloud Pub/Sub)                    │
│   Topics: `vendormind.rfp.ingested` · `vendormind.score.draft` · `vendormind.consent`   │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 4 — 8-NODE STATEFUL AGENTIC PIPELINE (LangGraph / AGY / ADK)                        │
│                                                                                         │
│   [Node 1: Intake & Privacy Agent]  ◄── Gemma 3 27B-IT Edge PII Scrubbing (GDPR Art. 5)│
│                 │                                                                       │
│                 ▼                                                                       │
│   [Node 2: Criteria Extraction]    ◄── Gemini 1.5 Pro + MCP Context Injection           │
│                 │                                                                       │
│                 ▼                                                                       │
│   [Node 3: Profile Retrieval]      ◄── Vertex AI Vector Search / Qdrant                   │
│                 │                                                                       │
│                 ▼                                                                       │
│   [Node 4: Multi-Signal Scoring]   ◄── 4-Signal Composite Scoring (Cost/Compliance/Fit)   │
│                 │                                                                       │
│                 │  ◄═════════════════════════════════════════════════════════════════►  │
│                 │  A2A PROTOCOL HANDSHAKE (Score Draft ⇄ EEOC Adverse Impact Veto)      │
│                 │  ◄═════════════════════════════════════════════════════════════════►  │
│                 ▼                                                                       │
│   [Node 5: Risk & Bias Agent]      ◄── Gemini 1.5 Pro + Enkrypt AI Toxicity Scan         │
│                 │                                                                       │
│                 ▼                                                                       │
│   [Node 6: Explanation Gen]        ◄── Gemini 1.5 Pro (EU AI Act Art. 13 CRISPE Prompt)  │
│                 │                                                                       │
│                 ▼                                                                       │
│   [Node 7: Comparison Agent]       ◄── Side-by-Side Ranked Pandas Matrix                  │
│                 │                                                                       │
│                 ▼                                                                       │
│   [Node 8: Output & HITL Agent]    ◄── Procurement Officer Approval + Web Speech Briefing  │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 5 — DATA, STORAGE & OBSERVABILITY                                                  │
│   • BigQuery Audit Store (90-Day Retention TTL, Immutable Event Logs)                  │
│   • Google Cloud Storage (Doc Storage) · OpenTelemetry Latency/Token Telemetry Endpoint     │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Detailed 8-Node Agentic Pipeline Breakdown

### **Node 1 — Intake & Privacy Agent (Gemma 3 27B-IT)**
* **Function**: Ingests PDF, TXT, DOCX, and JSON RFP and vendor proposal documents.
* **Privacy Gate**: Uses **Gemma 3 27B-IT** on-device to redact PII (SSNs, Emails, Phones, Addresses) *before* data leaves the local boundary, satisfying **GDPR Article 5 data minimisation**.
* **Output**: `parsed_rfp` and `parsed_vendors` state keys.

### **Node 2 — Criteria Extraction Agent (Gemini 1.5 Pro + MCP)**
* **Function**: Uses **Gemini 1.5 Pro** and **MCP** to extract explicit and implicit RFP criteria.
* **Bias Flagging**: Detects restrictive RFP phrasing that could create adverse impact on minority/SME vendors.
* **Output**: Structured `criteria_dict` containing validated cost, compliance, and timeline weights.

### **Node 3 — Vendor Profile Retrieval Agent (Vertex AI Vector Search)**
* **Function**: Queries historical vendor performance and reliability records using `sentence-transformers/all-MiniLM-L6-v2`.
* **Output**: `vendor_context` (retrieved historical scores and reliability history).

### **Node 4 — Multi-Signal Scoring Agent (Python + A2A Protocol)**
* **Function**: Computes a 4-signal weighted composite score:
  - 💰 **Cost Competitiveness** (40%)
  - 🛡️ **Compliance & SLA Completeness** (36%)
  - 🔍 **Semantic Capability Fit** (24%)
  - ⏱️ **Delivery Timeline Alignment**
* **A2A Initiation**: Submits `score_draft` to Node 5 via Google's A2A Protocol.

### **Node 5 — Risk & Bias Detection Agent (Enkrypt AI + EEOC 4/5ths Rule)**
* **A2A Veto Handshake**: Monitors the **EEOC 4/5ths Adverse Impact Ratio (AIR)**. If any vendor AIR < 0.80, Node 5 issues a `risk_veto` over A2A, applying an automated fairness floor before finalization.
* **Guardrail Layer**: Runs **Enkrypt AI** safety scanning to verify risk narratives for toxicity or bias.
* **Output**: `risk_flags`, `eeoc_report`, and `a2a_log`.

### **Node 6 — Explanation Generation Agent (Gemini 1.5 Pro CRISPE)**
* **Function**: Uses a CRISPE-structured prompt to generate a 3-sentence human-readable score justification per vendor.
* **Compliance**: Meets **EU AI Act Article 13** explainability mandates.

### **Node 7 — Comparison Agent (Python + Pandas)**
* **Function**: Assembles a side-by-side comparison matrix ranked by composite score, incorporating EEOC adjustment flags and A2A veto counts.
* **Output**: `comparison_table` state key.

### **Node 8 — Output & Human-in-the-Loop (HITL) Agent**
* **Function**: Presents recommendations to the Procurement Officer for mandatory approval/rejection.
* **Deliverables**: Generates print-ready HTML Executive Procurement Audit Reports and triggers AI Voice Executive Summaries via Web Speech API.
* **Audit Persistence**: Writes all decisions and A2A logs to BigQuery.

---

## 🔒 Security, Privacy & Regulatory Compliance

### **1. GDPR Compliance Engine**
- **Article 5 (Data Minimisation)**: Gemma 3 27B-IT redacts all PII prior to cloud LLM transmission.
- **Article 13 (Consent Capture)**: Explicit opt-in consent captured via `/v1/consent`.
- **Article 14 (Transparency Disclosures)**: Automated disclosure emails sent to vendor DPOs detailing Articles 15–22 data rights.
- **Article 17 (Right to Erasure)**: BigQuery 90-day automatic data retention TTL policy.
- **Article 22 (Automated Decision Rights)**: Human oversight preserved via Node 8 HITL approval gate.

### **2. EEOC Adverse Impact Monitoring**
- **4/5ths Rule Enforcement**: Scoring ↔ Risk A2A negotiation monitors adverse impact ratios across vendors.
- **Fairness Floor**: Automatic score re-calibration when AIR falls below 0.80.

### **3. OWASP Top 10 API Security**
- **A01 Broken Access Control**: OAuth2 Bearer / JWT token authentication (`POST /token`).
- **A02 Cryptographic Failures**: HSTS-enforced **TLS 1.3** in transit and **AES-256** at rest across Cloud Storage & BigQuery.
- **A03 Injection**: Pydantic v2 strict schema enforcement and XSS sanitization.
- **A07 Rate Limiting**: In-process rate limiting enforcing a max of **100 requests/min per IP**.

### **4. OpenTelemetry Observability**
- Exposes per-node latency (`latency_ms`), token counts (`token_usage`), and trace IDs via `GET /evaluation/{id}/telemetry`.

---

## 📋 IEEE 830 SRS Traceability Matrix

| Requirement ID | Component | Implementation File | Acceptance / Verification Metric |
|---|---|---|---|
| **FR-101** | Node 1 (Intake) | [`pipeline/gemma_filter.py`](./pipeline/gemma_filter.py) | 100% PII scrubbed via Gemma 3 27B-IT before egress |
| **FR-102** | GDPR Consent Engine | [`pipeline/gdpr_consent.py`](./pipeline/gdpr_consent.py) | Consent logged via `/v1/consent` & Art. 14 email dispatched |
| **FR-103** | Node 2 (Criteria) | [`pipeline/criteria_agent.py`](./pipeline/criteria_agent.py) | Gemini 1.5 Pro + MCP extracts validated criteria JSON |
| **FR-104** | Node 3 (Retrieval) | [`pipeline/retrieval_agent.py`](./pipeline/retrieval_agent.py) | Vertex Vector Search semantic similarity > 0.65 |
| **FR-105, 106** | Nodes 4 & 5 (A2A) | [`pipeline/a2a_protocol.py`](./pipeline/a2a_protocol.py) | A2A 3-step handshake; AIR < 0.80 triggers veto |
| **FR-107** | Node 6 (Explanation) | [`pipeline/explanation_agent.py`](./pipeline/explanation_agent.py) | EU AI Act Art. 13 compliant 3-sentence justification |
| **FR-108** | Node 7 (Comparison) | [`pipeline/comparison_agent.py`](./pipeline/comparison_agent.py) | Ranked side-by-side Pandas DataFrame |
| **FR-109** | Node 8 (HITL) | [`api/main.py`](./api/main.py) | Human approval recorded in BigQuery audit log |
| **FR-110** | Event Bus Decoupler | [`pipeline/pubsub_eventbus.py`](./pipeline/pubsub_eventbus.py) | Async event dispatch on Cloud Pub/Sub topics |
| **NFR-201** | Security (Auth) | [`api/main.py`](./api/main.py) | OAuth2 JWT token verification on all protected routes |
| **NFR-202** | Security (Encryption)| GCP Cloud Infrastructure | TLS 1.3 transit & AES-256 rest headers verified |
| **NFR-203** | Rate Limiting | [`api/main.py`](./api/main.py) | 101st request per minute returns HTTP 429 |
| **NFR-205** | Observability | `GET /evaluation/{id}/telemetry` | Returns OpenTelemetry latency & trace payload |

---

## 🎨 UI & Dashboard Experience

VendorMind AI features a **Futuristic Glassmorphic Interface** built in Streamlit:

- 🟢 **Live AI Control Center**: Real-time telemetry badges for Gemma 3 27B-IT, Gemini 1.5 Pro, and A2A Protocol.
- 🥊 **1-v-1 Cyber Duel**: Head-to-head battle card comparison tab for shortlisted candidates.
- 🛡️ **Enkrypt AI Safety Badges**: Visual indicators for real-time toxicity and fairness auditing.
- 🔊 **Voice Briefing Engine**: Integrated Web Speech API button generating verbal executive summaries.
- 📄 **Executive Audit Report**: One-click download of print-ready HTML procurement audit reports.

---

## ⚡ Quick Start & Local Run Guide

### 1. Clone Repository & Install Dependencies
```bash
git clone https://github.com/vinaybabannavar-create/VendorMind-AI.git
cd VendorMind-AI
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and set your API keys:
```bash
GEMINI_API_KEY="your-google-ai-studio-key"
ENKRYPT_API_KEY="your-enkrypt-key-optional"
```

### 3. Launch FastAPI Backend Server (Terminal 1)
```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8080 --reload
```
*API Documentation available at: `http://127.0.0.1:8080/docs`*

### 4. Launch Streamlit Dashboard (Terminal 2)
```bash
$env:API_BASE_URL="http://127.0.0.1:8080"
python -m streamlit run ui/app.py --server.port 8516
```
*Open `http://localhost:8516` in your browser to launch VendorMind AI.*

---

## 📄 Key Project Documentation

- 📘 [`PRD.md`](./PRD.md) — Formal IEEE 830 SRS Product Requirements Document
- 📐 [`ARCHITECTURE.md`](./ARCHITECTURE.md) — Architectural Specifications & Node Contracts
- 📜 [`LICENSE`](./LICENSE) — MIT Open Source License

---

<div align="center">

**VendorMind AI** · Built for the **HiDevs National AI Hackathon 2026**  
*Powered by Google AI Studio · Gemini 1.5 Pro · Gemma 3 27B-IT · LangGraph · Cloud Pub/Sub · Cloud Run*

</div>
