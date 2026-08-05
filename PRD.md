# Product Requirements Document (PRD): VendorMind AI
## IEEE 830 SRS Standard · Enterprise Procurement Intelligence Platform

---

## 1. Executive Summary
VendorMind AI is a production-grade, enterprise procurement intelligence platform designed for the HiDevs National AI Hackathon. The system automates end-to-end Request for Proposal (RFP) evaluations using an 8-node stateful multi-agent pipeline orchestrated via LangGraph, decoupled Cloud Run microservices communicating asynchronously over Cloud Pub/Sub, and Gemini 1.5 Pro reasoning paired with Gemma 3 27B-IT edge PII scrubbing.

---

## 2. Problem Statement
Procurement teams evaluate vendor bids manually in spreadsheets:
* **Slow & Costly:** Evaluation cycles take 3–6 weeks per RFP.
* **Subjective Bias:** Evaluators apply non-standardized criteria, risking EEOC compliance.
* **Opaque & Unauditable:** Lacks verifiable audit trails justifying decision rationale.
* **Privacy Risks:** Uploading vendor proposals to cloud LLMs violates GDPR Article 5 without edge PII scrubbing.

---

## 3. Goals & Key Performance Indicators
* **KPI-1 (Speed):** Reduce RFP evaluation cycle time from 3 weeks to < 2 minutes (95% reduction).
* **KPI-2 (Explainability):** 100% of generated scores accompanied by EU AI Act Article 13 compliant justifications.
* **KPI-3 (Fairness):** 100% of vendor comparisons pass the automated EEOC 4/5ths Rule via A2A negotiation.
* **KPI-4 (Privacy):** Zero PII unscrubbed before cloud LLM transmission (GDPR Article 5 & 13/14 compliance).
* **KPI-5 (Security):** 100% OWASP Top 10 API coverage with OAuth2/JWT authentication and TLS 1.3/AES-256 encryption.

---

## 4. Formal Functional Requirements (IEEE 830 Standard)

| Req ID | Component / Node | Functional Description | Acceptance Criteria |
|---|---|---|---|
| **FR-101** | Node 1: Intake Agent | Gemma 3 27B-IT edge PII detection & redaction (Names, Emails, SSNs, Aadhaar). | 100% of detected PII replaced with `[TYPE_REDACTED]` prior to cloud API calls. |
| **FR-102** | Node 2: Criteria Extraction | Gemini 1.5 Pro + MCP extracts explicit & implicit criteria into structured JSON. | Valid JSON containing `cost_weight`, `compliance_requirements`, `timeline_days`, `technical_specs`. |
| **FR-103** | Node 3: Profile Retrieval | Semantic vector search over historical vendor performance via Vertex AI Vector Search / Qdrant. | Top-5 relevant historical records retrieved with similarity score > 0.65. |
| **FR-104** | Node 4: Multi-Signal Scoring | 4-signal composite scoring: Cost (40%), Compliance (36%), Semantic (24%), Timeline. | Composite score bounded strictly `[0.0, 1.0]`, normalized against benchmark. |
| **FR-105** | Node 5: Risk & Bias Detection | EEOC 4/5ths Adverse Impact Ratio monitoring via Scoring-to-Risk A2A handshake. | If AIR < 0.80, `risk_veto` issued; fairness floor applied; logged in `state["a2a_log"]`. |
| **FR-106** | Node 6: Explanation Gen | Gemini 1.5 Pro generates 3-sentence justification per vendor (CRISPE prompt). | Justification cites cost, compliance, semantic fit, and risk flags in < 150 words. |
| **FR-107** | Node 7: Comparison Agent | Ranked Pandas comparison matrix generated with rank order and composite score. | Matrix sorted descending by `composite_score`; ranks assigned `1..N`. |
| **FR-108** | Node 8: Output & HITL | Streamlit dashboard HITL approval gate; generates Executive Audit Report HTML. | Approval status (`approved`/`rejected`) & note persisted to BigQuery audit store. |
| **FR-109** | GDPR Consent Engine | Captures explicit consent (Art. 13) & sends automated transparency notice (Art. 14). | Vendor consent captured via `/v1/consent` & notice dispatched via Pub/Sub. |
| **FR-110** | Event Bus Decoupler | Heavy agents (Intake, Risk) run as independent Cloud Run microservices on Cloud Pub/Sub. | Asynchronous event dispatch on `vendormind.rfp.ingested` and `vendormind.score.draft`. |

---

## 5. Non-Functional Requirements & Security Specifications

| NFR ID | Category | Specification | Measurable Target |
|---|---|---|---|
| **NFR-201** | Security (OWASP A01) | OAuth2 Bearer / JWT token authentication enforced on API gateway. | 401 Unauthorized returned for unauthenticated API access requests. |
| **NFR-202** | Security (OWASP A02) | Transport & At-Rest Encryption standards across all GCP services. | TLS 1.3 enforced in transit; AES-256 enforced at rest in BigQuery & Cloud Storage. |
| **NFR-203** | Security (OWASP A07) | API Rate Limiting to prevent denial of service and brute force. | Max 100 requests per minute per IP; HTTP 429 status returned on breach. |
| **NFR-204** | Privacy (GDPR Art. 17) | Right to Erasure & Data Retention policy in BigQuery state store. | Evaluation data auto-purged after 90-day TTL; manual erasure endpoint supported. |
| **NFR-205** | Observability (OTel) | Structured OpenTelemetry latency, token counts, and trace logging. | Latency per node in ms & trace ID exposed via `/evaluation/{id}/telemetry`. |
| **NFR-206** | Deployment (12-Factor) | Stateless Cloud Run microservices deployment with env var configuration. | 100% stateless execution; zero local disk reliance; environment secrets. |

---

## 6. IEEE 830 Traceability Matrix

| Requirement ID | Architectural Component | Implementation File / Service | Verification Command / Metric |
|---|---|---|---|
| **FR-101** | Node 1 (Intake) | `pipeline/gemma_filter.py` | Unit test: `gemma_preprocess()` scrubs SSN/Email |
| **FR-102** | Node 2 (Criteria) | `pipeline/criteria_agent.py` | MCP JSON schema validation test |
| **FR-103** | Node 3 (Retrieval) | `pipeline/retrieval_agent.py` | Qdrant / Vertex Vector Search top-k test |
| **FR-104, FR-105** | Nodes 4 & 5 (Scoring/Risk) | `pipeline/a2a_protocol.py` | A2A handshake test: AIR < 0.80 triggers veto |
| **FR-106** | Node 6 (Explanation) | `pipeline/explanation_agent.py` | CRISPE output structure & length check |
| **FR-107** | Node 7 (Comparison) | `pipeline/comparison_agent.py` | Pandas DataFrame sort & rank test |
| **FR-108** | Node 8 (HITL) | `api/main.py` (`/evaluation/approve`) | POST request records approval in BigQuery |
| **FR-109** | GDPR Consent | `pipeline/gdpr_consent.py` | POST `/v1/consent` records Art 13/14 log |
| **FR-110** | Event Bus Decoupler | `pipeline/pubsub_eventbus.py` | Cloud Pub/Sub message publish test |
| **NFR-201** | Security (Auth) | `api/main.py` (`verify_token`) | OAuth2 Bearer token validation check |
| **NFR-202** | Security (Crypto) | GCP Cloud Run / BigQuery | TLS 1.3 / AES-256 header verification |
| **NFR-203** | Security (Rate Limit)| `api/main.py` (`security_headers`) | 101st request returns HTTP 429 |
| **NFR-205** | Observability | `api/main.py` (`/telemetry`) | GET `/telemetry` returns latency_ms dict |

---

## 7. Decoupled Microservices Architecture (Cloud Pub/Sub)

```
[Procurement Dashboard - Streamlit]
               │
               ▼  (HTTPS / TLS 1.3 / OAuth2 JWT)
[VendorMind API Gateway - Cloud Run / FastAPI]
               │
               ├───► Publish: vendormind.rfp.ingested
               │
               ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   CLOUD PUB/SUB ASYNCHRONOUS EVENT BUS                 │
└──────┬──────────────────────┬───────────────────┬──────────────────────┘
       │                      │                   │
       ▼                      ▼                   ▼
┌──────────────┐      ┌──────────────┐    ┌──────────────┐
│ INTAKE SERVICE│      │RISK SERVICE  │    │CONSENT SERVICE│
│ (Cloud Run)  │      │ (Cloud Run)  │    │ (Cloud Run)  │
│ Gemma 3 27B  │      │ Gemini 1.5   │    │ GDPR Art 13/14│
└──────────────┘      └──────────────┘    └──────────────┘
```

---

## 8. Technology Stack & Mandatory Cloud Components
* **LLM & Reasoning:** Gemini 1.5 Pro (Google AI Studio / Vertex AI).
* **Edge Privacy Gate:** Gemma 3 27B-IT (Vertex AI / local on-device).
* **Agentic Orchestration:** LangGraph, Antigravity (AGY), Google ADK.
* **Context & Communication:** MCP (Model Context Protocol), A2A Protocol.
* **Event Bus Decoupling:** Google Cloud Pub/Sub.
* **Security & Auth:** OAuth2 / JWT, Pydantic v2, SlowAPI Rate Limiting.
* **Audit & Storage:** BigQuery (Audit/State), Vertex AI Vector Search / Qdrant.
* **Deployment:** Google Cloud Run (12-Factor App stateless containers).
