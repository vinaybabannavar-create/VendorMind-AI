# Product Requirements Document (PRD): VendorMind AI

## 1. Executive Summary
VendorMind AI is a production-grade, enterprise-ready procurement intelligence platform designed for the HiDevs National AI Hackathon. The system automates the end-to-end evaluation of vendor Request for Proposal (RFP) submissions. By utilizing a stateful, 8-node multi-agent pipeline orchestrated via LangGraph, Google Cloud Pub/Sub decoupled microservices, and Google Cloud Platform, VendorMind AI replaces manual, spreadsheet-based comparisons with an explainable, multi-signal scoring engine that prioritizes security, fairness (EEOC), privacy (GDPR), and complete distributed observability.

## 2. Problem Statement
Procurement teams at mid-to-large organizations face significant bottlenecks when evaluating vendor proposals. Manual processes are:
*   **Slow and Inefficient:** Comparing dozens of vendors against complex RFP criteria takes weeks.
*   **Inconsistent:** Human evaluators apply criteria subjectively, leading to bias.
*   **Opaque:** Lack of a clear audit trail for why a specific vendor was selected or rejected.
*   **Compliance Risky:** Handling PII and ensuring EEOC fairness (4/5ths rule) is difficult to manage manually at scale.
*   **Audit Gaps:** Traditional LLM deployments lack strict prompt hashing, model versioning, and correlation tracing across asynchronous microservice boundaries.

## 3. Goals & Objectives
*   **Automate Evaluation:** Reduce manual evaluation time by at least 75% through agentic automation.
*   **Ensure Explainability:** Provide human-readable justifications for every score, compliant with EU AI Act Article 13.
*   **Guarantee Privacy:** Implement edge-based PII scrubbing using Gemma 3 27B-IT to ensure GDPR Article 5 compliance.
*   **Enforce Fairness:** Use an automated Agent-to-Agent (A2A) protocol to monitor and adjust for EEOC adverse impact.
*   **End-to-End Tracing:** Propagate standardized correlation IDs (`correlation_id`, `parent_span_id`, `span_id`) across all Cloud Pub/Sub microservice boundaries.
*   **LLM Drift Auditability:** Log SHA-256 `prompt_hash`, exact `model_version`, and `temperature` for every LLM invocation.
*   **Vector Consistency:** Enforce Write-Through + Periodic Batch Reconciliation between Vertex AI Vector Search and local Qdrant.
*   **Maintain Control:** Keep a "Human-in-the-Loop" (HITL) for final approval and selection.

## 4. Target Users / Stakeholders
*   **Procurement Managers:** Primary users who upload RFPs and review ranked shortlists.
*   **Business Operations Teams:** Stakeholders involved in vendor selection and contract management.
*   **Compliance & Legal Officers:** Users who monitor the audit trail for regulatory adherence (GDPR, EEOC, EU AI Act).
*   **Enterprise Security Auditors:** Technical auditors evaluating distributed telemetry, prompt drift, and encryption standards.
*   **Vendors:** Data subjects whose proposals are being evaluated.

## 5. Functional Requirements
| Req ID | Component | Description | Implementation File |
| :--- | :--- | :--- | :--- |
| **FR-101** | Intake Agent | Ingests RFP/Proposals; uses Gemma 3 27B-IT to redact PII before cloud egress (GDPR Art. 5). | [`pipeline/gemma_filter.py`](./pipeline/gemma_filter.py) |
| **FR-102** | Consent Service | Captures explicit vendor opt-in (GDPR Art. 13) and sends DPO notifications (Art. 14). | [`pipeline/gdpr_consent.py`](./pipeline/gdpr_consent.py) |
| **FR-103** | Criteria Extraction | Extracts explicit/implicit criteria via Gemini 1.5 Pro; flags potential bias in RFP language using MCP. | [`pipeline/criteria_agent.py`](./pipeline/criteria_agent.py) |
| **FR-104** | Profile Retrieval & Vector Sync | Semantic vector search via Vertex AI Vector Search with Write-Through + 300s Batch Reconciliation to Qdrant. | [`pipeline/vector_sync.py`](./pipeline/vector_sync.py) |
| **FR-105** | Scoring Agent | Computes 4-signal composite scores (Cost, Compliance, Semantic, Timeline). | [`pipeline/scoring_agent.py`](./pipeline/scoring_agent.py) |
| **FR-106** | A2A Protocol | Executes 3-step handshake (`score_draft` -> `risk_veto` -> `score_final`) between Scoring & Risk agents over Pub/Sub. | [`pipeline/a2a_protocol.py`](./pipeline/a2a_protocol.py) |
| **FR-107** | Risk & Bias Agent | Monitors EEOC 4/5ths rule; uses Enkrypt AI to scan risk narratives for toxicity/bias. | [`pipeline/risk_agent.py`](./pipeline/risk_agent.py) |
| **FR-108** | Explanation Gen | Generates 3-sentence justifications per vendor citing specific evidence (EU AI Act Art. 13). | [`pipeline/explanation_agent.py`](./pipeline/explanation_agent.py) |
| **FR-109** | Comparison Agent | Generates a side-by-side ranked matrix using Pandas. | [`pipeline/comparison_agent.py`](./pipeline/comparison_agent.py) |
| **FR-110** | HITL Dashboard | Streamlit interface for human approval, rejection, and voice-enabled executive briefings. | [`ui/app.py`](./ui/app.py) |
| **FR-111** | Distributed Tracing Envelope | Propagates `correlation_id`, `parent_span_id`, `span_id`, and `timestamp_utc` across all Pub/Sub topic hops. | [`pipeline/correlation_tracing.py`](./pipeline/correlation_tracing.py) |
| **FR-112** | Event Bus Decoupler | Asynchronous event dispatch via Google Cloud Pub/Sub topics (`vendormind.rfp.ingested`, `vendormind.score.draft`). | [`pipeline/pubsub_eventbus.py`](./pipeline/pubsub_eventbus.py) |

## 6. Non-Functional Requirements
| Req ID | Category | Requirement | Verification Method |
| :--- | :--- | :--- | :--- |
| **NFR-201** | Security | OAuth2/JWT Auth (`POST /token`), HSTS TLS 1.3 in transit, AES-256 at rest, Pydantic v2 XSS input validation. | OWASP A01, A02, A03 Headers & Schema Tests |
| **NFR-202** | Performance | End-to-end evaluation of 10 vendors in < 45 seconds; Pub/Sub state caching reduces A2A latency overhead. | OpenTelemetry `/v1/telemetry/{id}` |
| **NFR-203** | Scalability | Decoupled serverless microservices on Cloud Run; auto-scaling 0 to 50 concurrent requests. | Cloud Run Load Testing |
| **NFR-204** | Reliability | 12-Factor App compliance; fault-tolerant async event bus via Cloud Pub/Sub. | Fault-injection & Retry Logic |
| **NFR-205** | Observability & Auditability | OpenTelemetry tracing capturing `correlation_id`, `prompt_hash` (SHA-256), exact `model_version`, and `temperature`. | `GET /v1/telemetry/{id}` API Response |
| **NFR-206** | Compliance | GDPR Art. 17 data retention (90-day TTL in BigQuery); EEOC 4/5ths Rule Adverse Impact Ratio (AIR >= 0.80). | BigQuery TTL Policy & EEOC Report |

## 7. System Architecture Overview
The system follows a **Decoupled Microservices Architecture** orchestrated by **LangGraph** and **Google Cloud Pub/Sub**.
1.  **Client Tier:** Streamlit Dashboard with Neural Glassmorphic UI & Distributed Trace Tab (`ui/app.py`).
2.  **Gateway Tier:** OWASP-hardened FastAPI Gateway managing JWT authentication (`/token`), Rate Limiting (100 req/min/IP), and GDPR Consent Service (`/v1/consent`).
3.  **Event Bus Tier:** Cloud Pub/Sub adapter delivering standardized OpenTelemetry trace envelopes across topic boundaries.
4.  **Agentic Pipeline Tier:** 8 specialized agents (Intake, Criteria, Retrieval, Scoring, Risk, Explanation, Comparison, Output).
5.  **Vector Sync Tier:** Write-Through + Periodic Batch Reconciliation (300s daemon) between Vertex AI Vector Search and local Qdrant.
6.  **AI Tier:** Gemini 1.5 Pro (Reasoning), Gemma 3 27B-IT (Edge Privacy), Enkrypt AI (Guardrails).
7.  **Storage & Audit Tier:** BigQuery (Immutable Audit & State Store with 90-day TTL), Vertex AI Vector Search, Google Cloud Storage.

## 8. Tech Stack — Implementation Status

| Component | Status | Notes |
| :--- | :---: | :--- |
| Gemini 1.5 Pro (`gemini-1.5-pro-002`), via Google AI Studio | ✅ Live | Core reasoning LLM, used in `criteria_agent.py`, `scoring_agent.py`, `risk_agent.py`, `explanation_agent.py` |
| Gemma 3 27B-IT | ✅ Live | On-device PII redaction, `pipeline/gemma_filter.py` |
| LangGraph (`langgraph==0.2.14`) | ✅ Live | Real `StateGraph` orchestration, `pipeline/orchestrator.py`, verified against 70-test suite |
| A2A Protocol | ✅ Live | 3-step Scoring ↔ Risk handshake, `pipeline/a2a_protocol.py` |
| Correlation Tracing | ✅ Live | `correlation_id` threaded through every node, `pipeline/correlation_tracing.py` |
| FastAPI, Pydantic v2, PyJWT | ✅ Live | `api/main.py` |
| Streamlit, Web Speech API | ✅ Live | `ui/app.py` |
| Cloud Run, Docker | ✅ Live | `Dockerfile`, `start.sh` |
| Vertex AI Vector Search | 🔄 Dev-mode | SDK call gated behind `VERTEX_AI_ENABLED`; falls back to local Qdrant, `pipeline/vector_sync.py` |
| Google Cloud Pub/Sub | 🔄 Dev-mode | Real `pubsub_v1.PublisherClient` attempted; falls back to in-process dispatch without live GCP credentials, `pipeline/pubsub_eventbus.py` |
| MCP (Model Context Protocol) | 🔄 Dev-mode | Context injection applied directly in `criteria_agent.py`; standalone MCP server/client is a roadmap item |
| Google ADK | 🔄 Dev-mode | Agent scaffolding patterns informed by ADK design; no direct SDK integration yet |
| Antigravity (AGY) | 🔄 Dev-mode | Used as an AI-assisted development aid during build; not a runtime dependency |
| BigQuery | 🔄 Dev-mode | Schema defined in `api/main.py`; evaluation store currently in-memory, explicitly commented as a placeholder for BigQuery/Firestore |

> **Legend:** ✅ Live = exercised by the test suite and the real request path · 🔄 Dev-mode = implemented with a working local fallback, gated behind config, or not yet wired to the live GCP service

## 9. Data Requirements & Telemetry Schema
### 9.1 Pub/Sub Message Envelope Schema
```json
{
  "trace_context": {
    "correlation_id": "uuid4-root-trace-id-across-all-hops",
    "parent_span_id": "uuid4-upstream-node-span-id",
    "span_id": "uuid4-current-node-span-id",
    "node_name": "scoring_agent",
    "timestamp_utc": "2026-08-05T21:22:00Z"
  },
  "llm_audit": {
    "model_version": "gemini-1.5-pro-002",
    "prompt_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "temperature": 0.1,
    "latency_ms": 342.5
  },
  "payload": { "evaluation_id": "eval_101", "scores": {} }
}
```

### 9.2 Audit & Retention
*   **Audit Logs:** Every A2A handshake message, HITL decision, correlation ID, SHA-256 prompt hash, and model version is logged to BigQuery.
*   **Retention:** 90-day TTL on all evaluation tables to satisfy GDPR Article 17 ("Right to Erasure").

## 10. API Specifications
*   `POST /token`: OAuth2/JWT token issuance.
*   `POST /v1/consent`: GDPR Article 13/14 consent capture and transparency notice dispatch.
*   `POST /evaluate`: Initiates the 8-node agentic pipeline and returns `evaluation_id`.
*   `GET /evaluation/{id}`: Returns evaluation state and shortlist recommendations.
*   `GET /evaluation/{id}/comparison`: Returns side-by-side comparison matrix.
*   `GET /evaluation/{id}/explain/{vendor_id}`: Returns EU AI Act Art. 13 score justification.
*   `GET /evaluation/{id}/telemetry`: Extended OpenTelemetry endpoint returning `correlation_id`, `distributed_trace` spans, `llm_audit_log` (`prompt_hash`, `model_version`, `temperature`), `a2a_log`, `eeoc_report`, and `gemma_pii_summary`.
*   `POST /evaluation/approve`: Submits Procurement Manager HITL approval/rejection note.
*   `GET /evaluation/{id}/report`: Generates print-ready Executive Audit Report HTML.

## 11. Security & Regulatory Compliance Requirements
*   **GDPR Article 5 (Data Minimisation):** Gemma 3 27B-IT scrubs all PII at Node 1 before cloud LLM transmission.
*   **GDPR Article 13/14 (Consent & Transparency):** Explicit vendor consent capture `/v1/consent` and automated DPO transparency notices.
*   **GDPR Article 17 (Right to Erasure):** BigQuery 90-day automatic data retention TTL policy.
*   **GDPR Article 22 (Automated Decision Rights):** Human oversight preserved via Node 8 HITL approval gate.
*   **EEOC 4/5ths Rule Monitoring:** Automatic A2A negotiation applies fairness floors if Adverse Impact Ratio (AIR) < 0.80.
*   **EU AI Act Article 13:** CRISPE-prompted 3-sentence explainable score rationale citing specific evidence.
*   **OWASP Top 10 Security:** OAuth2 JWT auth (A01), TLS 1.3/AES-256 (A02), Pydantic v2 input validation (A03), Strict CORS & HSTS (A05), 100 req/min IP rate limiting (A07).

## 12. Deployment & Infrastructure
*   **Containerization:** All services packaged as Docker containers adhering to 12-Factor App standards.
*   **Hosting:** Serverless deployment on Google Cloud Run.
*   **CI/CD:** Automated pipeline via Google Cloud Build with blue/green deployment strategy.
*   **Secrets:** Managed via Google Secret Manager; zero hardcoded credentials.

## 13. Success Metrics
*   **Efficiency:** Average evaluation time for 10 vendors < 45 seconds (75% time reduction).
*   **Privacy:** 100% PII scrubbed at Node 1 edge boundary.
*   **Fairness:** 0% EEOC violations in final reports (enforced by A2A veto).
*   **Tracing Coverage:** 100% of Pub/Sub messages carry valid `correlation_id` trace envelopes.
*   **Auditability:** 100% of LLM calls record SHA-256 `prompt_hash`, `model_version`, and `temperature`.

## 14. Timeline & Milestones
*   **Phase 1 (Foundation):** Setup Cloud Run, FastAPI Gateway, and Gemma 3 27B-IT PII scrubbing.
*   **Phase 2 (Intelligence & Sync):** Implement Criteria Extraction, Vertex AI ↔ Qdrant Write-Through Sync, and Gemini 1.5 Pro scoring.
*   **Phase 3 (Compliance & A2A):** Integrate Pub/Sub Event Bus, A2A Protocol for EEOC monitoring, and Enkrypt AI guardrails.
*   **Phase 4 (Observability & Tracing):** Implement Correlation ID tracing envelope, LLM prompt hash audit log, Streamlit Tab 6 UI, and BigQuery audit reporting.

## 15. Resolved Architectural Recommendations (Evaluator Feedback)
1.  **Distributed Tracing Across Pub/Sub (Resolved):** Standardized trace envelope (`correlation_id`, `parent_span_id`, `span_id`) implemented in `pipeline/correlation_tracing.py` and wrapped around all `pubsub_eventbus.py` messages.
2.  **LLM Telemetry Audit Log (Resolved):** Telemetry endpoint extended in `api/main.py` to return SHA-256 `prompt_hash`, exact `model_version` (e.g. `gemini-1.5-pro-002`, `gemma-3-27b-it`), and `temperature` setting.
3.  **Vector Search Synchronization (Resolved):** Write-Through + 300s Periodic Batch Reconciliation protocol implemented in `pipeline/vector_sync.py` between Vertex AI Vector Search and local Qdrant.
