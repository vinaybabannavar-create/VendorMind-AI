# Product Requirements Document (PRD): VendorMind AI

## 1. Executive Summary
VendorMind AI is a production-grade, enterprise-ready procurement intelligence platform designed for the HiDevs National AI Hackathon. The system automates the end-to-end evaluation of vendor Request for Proposal (RFP) submissions. By utilizing a stateful, 8-node multi-agent pipeline orchestrated via LangGraph and Google Cloud, VendorMind AI replaces manual, spreadsheet-based comparisons with an explainable, multi-signal scoring engine that prioritizes security, fairness (EEOC), and privacy (GDPR).

## 2. Problem Statement
Procurement teams at mid-to-large organizations face significant bottlenecks when evaluating vendor proposals. Manual processes are:
*   **Slow and Inefficient:** Comparing dozens of vendors against complex RFP criteria takes weeks.
*   **Inconsistent:** Human evaluators apply criteria subjectively, leading to bias.
*   **Opaque:** Lack of a clear audit trail for why a specific vendor was selected or rejected.
*   **Compliance Risky:** Handling PII and ensuring EEOC fairness (4/5ths rule) is difficult to manage manually at scale.

## 3. Goals & Objectives
*   **Automate Evaluation:** Reduce manual evaluation time by at least 75% through agentic automation.
*   **Ensure Explainability:** Provide human-readable justifications for every score, compliant with EU AI Act Article 13.
*   **Guarantee Privacy:** Implement edge-based PII scrubbing using Gemma 3 27B-IT to ensure GDPR Article 5 compliance.
*   **Enforce Fairness:** Use an automated Agent-to-Agent (A2A) protocol to monitor and adjust for EEOC adverse impact.
*   **Maintain Control:** Keep a "Human-in-the-Loop" (HITL) for final approval and selection.

## 4. Target Users / Stakeholders
*   **Procurement Managers:** Primary users who upload RFPs and review ranked shortlists.
*   **Business Operations Teams:** Stakeholders involved in vendor selection and contract management.
*   **Compliance & Legal Officers:** Users who monitor the audit trail for regulatory adherence (GDPR, EEOC).
*   **Vendors:** Data subjects whose proposals are being evaluated.

## 5. Functional Requirements
| Req ID | Component | Description |
| :--- | :--- | :--- |
| **FR-101** | Intake Agent | Ingests RFP/Proposals; uses Gemma 3 27B-IT to redact PII before cloud egress. |
| **FR-102** | Consent Service | Captures explicit vendor opt-in (GDPR Art. 13) and sends DPO notifications (Art. 14). |
| **FR-103** | Criteria Extraction | Extracts explicit/implicit criteria via Gemini 1.5 Pro; flags potential bias in RFP language. |
| **FR-104** | Profile Retrieval | Performs semantic search over historical vendor data using Vertex AI Vector Search. |
| **FR-105** | Scoring Agent | Computes 4-signal composite scores (Cost, Compliance, Semantic, Timeline). |
| **FR-106** | A2A Protocol | Executes a 3-step handshake (score_draft -> risk_veto -> score_final) between Scoring and Risk agents. |
| **FR-107** | Risk & Bias Agent | Monitors EEOC 4/5ths rule; uses Enkrypt AI to scan risk narratives for toxicity/bias. |
| **FR-108** | Explanation Gen | Generates 3-sentence justifications per vendor citing specific evidence. |
| **FR-109** | Comparison Agent | Generates a side-by-side ranked matrix using Pandas. |
| **FR-110** | HITL Dashboard | Streamlit interface for human approval, rejection, and voice-enabled executive briefings. |

## 6. Non-Functional Requirements
| Req ID | Category | Requirement |
| :--- | :--- | :--- |
| **NFR-201** | Security | OAuth2/JWT Auth, TLS 1.3 in transit, AES-256 at rest. |
| **NFR-202** | Performance | End-to-end evaluation of 10 vendors in < 45 seconds. |
| **NFR-203** | Scalability | Stateless microservices on Cloud Run; auto-scaling from 0 to 50 concurrent requests. |
| **NFR-204** | Reliability | 12-Factor App compliance; asynchronous communication via Cloud Pub/Sub. |
| **NFR-205** | Observability | OpenTelemetry tracing; per-node latency and token usage tracking. |
| **NFR-206** | Compliance | GDPR Art. 17 data retention (90-day TTL in BigQuery). |

## 7. System Architecture Overview
The system follows a **Decoupled Microservices Architecture** orchestrated by **LangGraph**.
1.  **Client Tier:** Streamlit Dashboard for user interaction.
2.  **Gateway Tier:** FastAPI Gateway managing authentication and the GDPR Consent Service.
3.  **Event Bus:** Cloud Pub/Sub handles asynchronous communication between nodes.
4.  **Agentic Pipeline:** 8 specialized agents (Intake, Criteria, Retrieval, Scoring, Risk, Explanation, Comparison, Output).
5.  **AI Tier:** Gemini 1.5 Pro (Reasoning), Gemma 3 27B-IT (Edge Privacy), Enkrypt AI (Guardrails).
6.  **Storage Tier:** BigQuery (Audit), Vertex AI Vector Search (Knowledge Base), GCS (Documents).

## 8. Tech Stack
*   **LLM & Reasoning:** Gemini 1.5 Pro (via Google AI Studio), Gemma 3 27B-IT (Vertex AI).
*   **Orchestration:** LangGraph, Antigravity (AGY), Google ADK.
*   **Protocols:** MCP (Model Context Protocol), A2A (Agent-to-Agent).
*   **Backend:** FastAPI, Python, Cloud Pub/Sub.
*   **Frontend:** Streamlit, Web Speech API.
*   **Infrastructure:** Cloud Run, Google Cloud Build (CI/CD).
*   **Data/Vector:** BigQuery, Vertex AI Vector Search, Qdrant.

## 9. Data Requirements
*   **Input Data:** PDF/Text RFPs and Vendor Proposals.
*   **State Management:** LangGraph state stores `parsed_rfp`, `criteria_dict`, `vendor_context`, `final_scores`, and `a2a_log`.
*   **Audit Logs:** Every A2A message, HITL decision, and LLM token count is persisted to BigQuery.
*   **Retention:** 90-day TTL on all evaluation data to satisfy GDPR "Right to Erasure."

## 10. API Specifications
*   `POST /v1/token`: OAuth2/JWT authentication.
*   `POST /v1/consent`: GDPR Article 13/14 consent capture.
*   `POST /v1/evaluate`: Initiates the 8-node agentic pipeline.
*   `GET /v1/evaluation/{id}/status`: Polls the current state of the LangGraph.
*   `GET /v1/evaluation/{id}/telemetry`: Returns OpenTelemetry-compatible latency and token usage data.
*   `POST /v1/evaluation/{id}/approve`: Submits HITL approval and triggers final report generation.

## 11. Security Requirements
*   **PII Redaction:** Gemma 3 27B-IT must scrub all PII at Node 1 before any data reaches external LLM APIs.
*   **Input Validation:** Pydantic v2 schema enforcement on all API inputs to prevent injection (OWASP A03).
*   **Rate Limiting:** 100 requests/min per IP to prevent DoS (OWASP A07).
*   **Encryption:** Mandatory TLS 1.3 for all endpoints; AES-256 for data at rest in BigQuery and GCS.

## 12. Deployment & Infrastructure
*   **Containerization:** All services packaged as Docker containers following 12-Factor App standards.
*   **Hosting:** Serverless deployment on Google Cloud Run.
*   **CI/CD:** Automated pipeline via Cloud Build with blue/green deployment strategy.
*   **Environment Management:** All secrets managed via Secret Manager; configuration via environment variables.

## 13. Success Metrics
*   **Efficiency:** Average time from RFP upload to ranked shortlist < 1 minute.
*   **Accuracy:** >95% recall in identifying mandatory compliance certifications.
*   **Fairness:** 0% EEOC violations in final reports (enforced by A2A veto).
*   **User Trust:** >4.5/5 rating on explanation clarity in user feedback loops.

## 14. Timeline & Milestones
*   **Phase 1 (Foundation):** Setup Cloud Run, FastAPI Gateway, and Gemma 3 PII scrubbing.
*   **Phase 2 (Intelligence):** Implement Criteria Extraction, Vector Retrieval, and Gemini-based scoring.
*   **Phase 3 (Compliance):** Integrate A2A Protocol for EEOC monitoring and Enkrypt AI guardrails.
*   **Phase 4 (Interface):** Build Streamlit Dashboard, HITL loop, and BigQuery audit reporting.

## 15. Open Questions & Risks
*   **Latency:** The 3-step A2A handshake between Scoring and Risk agents may add latency; requires optimization of Pub/Sub triggers.
*   **Implicit Criteria:** The accuracy of Gemini 1.5 Pro in identifying "implicit" criteria needs rigorous testing against diverse RFP formats.
*   **Model Availability:** Dependency on Google AI Studio/Vertex AI availability for Gemini 1.5 Pro.
