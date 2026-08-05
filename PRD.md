# Product Requirements Document (PRD): VendorMind AI

## 1. Executive Summary
VendorMind AI is a production-grade, enterprise procurement intelligence platform designed for the HiDevs National AI Hackathon. The system automates the end-to-end evaluation of vendor Request for Proposal (RFP) submissions using a stateful, 8-node multi-agent pipeline. By leveraging Gemini 1.5 Pro for reasoning and Gemma 3 27B-IT for privacy-preserving edge processing, VendorMind AI transforms slow, manual spreadsheet comparisons into an explainable, compliant, and multi-signal scoring engine.

## 2. Problem Statement
Procurement teams at mid-to-large organizations face significant bottlenecks when evaluating vendor proposals. The current manual process is:
*   **Slow:** Cross-checking dozens of proposals against complex RFP criteria takes weeks.
*   **Inconsistent:** Human evaluators apply criteria subjectively, leading to potential bias.
*   **Opaque:** There is often no clear audit trail justifying why one vendor was selected over another, creating compliance risks.
*   **Privacy-Risky:** Handling PII within vendor documents often violates GDPR/internal policies when sent to cloud LLMs without redaction.

## 3. Goals & Objectives
*   **Automate Evaluation:** Reduce manual evaluation time by at least 70%.
*   **Ensure Explainability:** Provide human-readable justifications for every score (EU AI Act Art. 13 compliant).
*   **Enforce Fairness:** Implement automated EEOC 4/5ths rule monitoring via Agent-to-Agent (A2A) negotiation.
*   **Privacy First:** Redact PII at the intake boundary using local/on-device models (Gemma 3).
*   **Human-in-the-Loop:** Maintain human oversight with a mandatory approval stage before final selection.

## 4. Target Users / Stakeholders
*   **Procurement Managers:** Primary users who upload RFPs and review rankings.
*   **Compliance/Legal Officers:** Stakeholders who audit the evaluation process for fairness and GDPR compliance.
*   **Business Operations Teams:** Users who define the technical and financial requirements for vendor selection.

## 5. Functional Requirements
The system is structured as a stateful directed graph (LangGraph) consisting of 8 specialized nodes:

### 5.1. Intake & Privacy (Node 1)
*   **Requirement:** Ingest RFP and vendor documents (PDF/Text).
*   **Capability:** Use **Gemma 3 27B-IT** to detect and redact PII (Names, Emails, Phones) before data leaves the local environment/boundary.
*   **Output:** PII-scrubbed `parsed_rfp` and `parsed_vendors` state.

### 5.2. Criteria Extraction (Node 2)
*   **Requirement:** Extract explicit and implicit evaluation criteria.
*   **Capability:** Use **Gemini 1.5 Pro** with **MCP (Model Context Protocol)** to inject vendor knowledge base context.
*   **Output:** Structured JSON containing weights for cost, compliance, and technical specs.

### 5.3. Contextual Retrieval (Node 3)
*   **Requirement:** Retrieve historical vendor performance data.
*   **Capability:** Perform semantic search using **Vertex AI Vector Search** (fallback to Qdrant).
*   **Output:** `vendor_context` including past scores and reliability metrics.

### 5.4. Multi-Signal Scoring & A2A Fairness (Nodes 4 & 5)
*   **Requirement:** Compute composite scores and vet for bias.
*   **Capability:** 
    *   **Node 4 (Scoring):** Computes draft scores (Cost 40%, Compliance 36%, Semantic 24%).
    *   **Node 5 (Risk):** Monitors EEOC Adverse Impact Ratio (4/5ths rule).
    *   **A2A Protocol:** Scoring Agent sends `score_draft` to Risk Agent; Risk Agent issues `risk_veto` if AIR < 0.80, forcing a fairness-floor adjustment.

### 5.5. Explainability & Comparison (Nodes 6 & 7)
*   **Requirement:** Generate justifications and side-by-side views.
*   **Capability:** 
    *   **Node 6:** Uses Gemini 1.5 Pro (CRISPE prompt) to write 3-sentence justifications citing specific evidence.
    *   **Node 7:** Generates a ranked Pandas-based comparison matrix.

### 5.6. Output & HITL (Node 8)
*   **Requirement:** Final report generation and human approval.
*   **Capability:** Streamlit-based interface for "Approve/Reject" decisions. Persist all decisions and A2A logs to **BigQuery**.

## 6. Non-Functional Requirements
*   **Performance:** Response latency under 10 seconds for the full pipeline per vendor.
*   **Scalability:** Support 10–20 vendor proposals per RFP evaluation.
*   **Reliability:** 12-Factor App compliant; stateless execution on Cloud Run.
*   **Auditability:** 100% of agent communications (A2A) and LLM prompts must be logged for compliance.
*   **Security:** OWASP Top 10 compliance, specifically focusing on A01 (Access Control) and A02 (Cryptographic Failures).

## 7. System Architecture Overview
The system follows a **Stateful Multi-Agent Orchestration** pattern:
1.  **Client Layer:** Streamlit Dashboard for user interaction.
2.  **API Layer:** FastAPI Gateway hosted on Cloud Run.
3.  **Orchestration Layer:** LangGraph managed by **Antigravity (AGY)** for lifecycle and state transitions.
4.  **Agent Pipeline:** 8-node sequential and bidirectional (A2A) flow.
5.  **Service/Storage Layer:** Google AI Studio (Gemini), Vertex AI (Gemma/Vector Search), BigQuery (Audit), and Cloud Storage (Docs).

## 8. Tech Stack
*   **LLM & Reasoning:** Gemini 1.5 Pro (Google AI Studio), Gemma 3 27B-IT (Vertex AI).
*   **Orchestration:** LangGraph, Antigravity (AGY), Google ADK.
*   **Context & Tools:** MCP (Model Context Protocol), A2A Protocol.
*   **Backend:** FastAPI, Python, Pandas, NumPy.
*   **Frontend:** Streamlit.
*   **Data/Storage:** BigQuery (Audit/State), Vertex AI Vector Search / Qdrant (Vector DB), Google Cloud Storage.
*   **Deployment:** Cloud Run, Docker (12-Factor App).
*   **Guardrails:** Enkrypt AI (Bias/Toxicity scanning).

## 9. Data Requirements
*   **Data Minimization:** Gemma 3 must redact PII before any cloud API calls (GDPR Art. 5).
*   **Retention:** BigQuery TTL set to 90 days for evaluation logs.
*   **State Management:** LangGraph `StateGraph` persists the `parsed_rfp`, `criteria_dict`, `final_scores`, and `a2a_log`.

## 10. API Specifications
*   `POST /v1/evaluate`: Ingests RFP and Vendor docs; returns `evaluation_id`.
*   `GET /v1/status/{id}`: Returns current node execution status and latency.
*   `POST /v1/approve`: Submits HITL approval and triggers final report generation.
*   `GET /v1/telemetry/{id}`: Returns OpenTelemetry-compatible trace and token usage data.

## 11. Security Requirements
*   **PII Redaction:** Mandatory Gemma-based scrubbing at Node 1.
*   **Input Validation:** Pydantic v2 schema enforcement on all API inputs.
*   **Rate Limiting:** 100 requests/min/IP enforced at the FastAPI gateway.
*   **Audit Trail:** Every A2A message and HITL decision must include a timestamp and `messageId` in BigQuery.

## 12. Deployment & Infrastructure
*   **Containerization:** All components containerized via Docker.
*   **Hosting:** Google Cloud Run (Serverless).
*   **CI/CD:** Google Cloud Build with Blue/Green deployment strategy.
*   **Environment:** All secrets managed via Environment Variables (12-Factor App).

## 13. Success Metrics
*   **Efficiency:** Time from upload to ranked shortlist < 2 minutes.
*   **Fairness:** 100% of evaluations pass the automated EEOC 4/5ths rule check.
*   **Accuracy:** > 90% user acceptance rate of AI-generated explanations.
*   **Compliance:** Zero PII leaked to Gemini API logs (verified by Gemma audit).

## 14. Timeline & Milestones
*   **Milestone 1:** Intake & Extraction (Nodes 1-2) with Gemma PII scrubbing.
*   **Milestone 2:** Retrieval & Scoring (Nodes 3-4) with Vertex AI Vector Search.
*   **Milestone 3:** Risk & A2A (Node 5) implementation of the 4/5ths rule handshake.
*   **Milestone 4:** Explanation & HITL (Nodes 6-8) with Streamlit dashboard integration.
*   **Milestone 5:** Final Audit & 12-Factor App deployment on Cloud Run.

## 15. Open Questions & Risks
*   **Risk:** Latency of the 8-node chain might exceed user expectations if LLM cold starts occur.
*   **Risk:** Accuracy of Gemma 3 in redacting highly nested tabular PII in complex PDFs.
*   **Question:** Should the system support multi-language RFPs, or is it restricted to English for the hackathon? (Current Scope: English).
