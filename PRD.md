# Product Requirements Document (PRD): VendorMind AI

## 1. Executive Summary
VendorMind AI is an agentic AI system designed to automate the complex, manual process of vendor evaluation for procurement teams. By utilizing a stateful, multi-node agent pipeline, the system transforms raw RFP (Request for Proposal) requirements and vendor submissions into structured, explainable, and risk-aware rankings. Unlike "black-box" scoring systems, VendorMind AI prioritizes transparency, providing human-readable justifications for every decision and maintaining a critical human-in-the-loop (HITL) approval step.

## 2. Problem Statement
Procurement teams at mid-to-large organizations currently face a bottleneck in vendor selection. The process is:
*   **Slow:** Manually cross-referencing dozens of proposals against complex RFP criteria.
*   **Inconsistent:** Subjective scoring leads to different results across different evaluators.
*   **Opaque:** Lack of a clear audit trail or documented reasoning for why a specific vendor was selected or rejected.
*   **Risk-Prone:** Difficulty in identifying subtle risks like single-vendor dependency or "dumping" (unusually low bids).

## 3. Goals & Objectives
*   **Efficiency:** Reduce manual evaluation time from weeks/days to minutes.
*   **Explainability:** Ensure every score is backed by a natural language justification citing specific evidence.
*   **Objectivity:** Standardize scoring logic across all vendors using a multi-signal approach.
*   **Risk Mitigation:** Automatically flag compliance gaps and market risks.
*   **Control:** Maintain human oversight through a dedicated approval interface.

## 4. Target Users / Stakeholders
*   **Procurement Managers:** Primary users who upload RFPs and review final shortlists.
*   **Business Operations Teams:** Stakeholders involved in vendor due diligence and compliance.
*   **Compliance Officers:** Users requiring an audit trail of the selection process.

## 5. Functional Requirements

### 5.1. Document Ingestion & Parsing
*   **Intake Agent:** Must ingest and normalize RFP documents and vendor submissions (PDFs, pricing sheets, certificates).
*   **Criteria Extraction:** Must use LLM reasoning to identify both explicit (e.g., "Must be ISO certified") and implicit (e.g., "Demonstrated experience in scaling") criteria.

### 5.2. Contextual Retrieval
*   **Vendor Profile Retrieval:** Must perform semantic vector searches against a historical knowledge base to include past performance and existing certifications in the current evaluation.

### 5.3. Multi-Signal Scoring
*   **Composite Scoring:** The system must compute scores based on:
    *   **Structured Signals:** Cost, compliance status, and delivery timelines.
    *   **Semantic Similarity:** Alignment between vendor capabilities and RFP requirements.
    *   **Historical Reliability:** Past performance data.

### 5.4. Risk & Bias Detection
*   **Automated Flagging:** Identify unusually low bids, missing documentation, or criteria that unfairly disadvantage specific vendor types (e.g., SMEs).

### 5.5. Reporting & Comparison
*   **Explanation Generation:** Generate human-readable "justification strings" for every rank.
*   **Side-by-Side Comparison:** Produce a structured grid comparing the top-N vendors across all extracted dimensions.

### 5.6. Human-in-the-Loop (HITL)
*   **Approval Workflow:** The system must present the final ranked shortlist to the user for a "Go/No-Go" decision before finalizing the report.

## 6. Non-Functional Requirements
*   **Performance:** Evaluation of a single vendor should complete within a few seconds.
*   **Scalability:** Support simultaneous comparison of 10–20 vendors per RFP.
*   **Auditability:** Every step of the agentic reasoning must be logged for compliance.
*   **Usability:** Dashboard must be intuitive for non-technical procurement staff.

## 7. System Architecture Overview
The system follows a vertical, stateful pipeline orchestrated by a directed graph:
1.  **Frontend:** Streamlit-based dashboard for user interaction.
2.  **API Layer:** FastAPI gateway managing requests.
3.  **Orchestration:** LangGraph managing the state and transitions between 8 specialized agents.
4.  **Agent Tier:** Sequential processing from Intake to Output.
5.  **Data/LLM Tier:** Foundational layer providing reasoning (Gemini), semantic memory (Vector DB), and persistence (BigQuery/GCS).

## 8. Tech Stack
*   **LLM & Reasoning:** Gemini 1.5 Pro (Vertex AI).
*   **Agent Orchestration:** LangGraph, Agent Development Kit (ADK).
*   **Backend:** FastAPI, Python, Cloud Run.
*   **Frontend:** Streamlit.
*   **Vector Search:** Vertex AI Vector Search / ChromaDB.
*   **Storage:** Google Cloud Storage (Documents), BigQuery (Audit/Logs), Cloud SQL (State).
*   **Tooling:** Model Context Protocol (MCP) for structured tool calls.

## 9. Data Requirements
*   **Unstructured Data:** RFP PDFs, Vendor Proposals, Compliance Certificates.
*   **Structured Data:** Extracted criteria schemas, scoring weights, and vendor metadata.
*   **Vector Data:** Embeddings of vendor historical performance and profiles.
*   **Audit Logs:** Full trace of agent decisions and LLM prompts/responses.

## 10. API Specifications
*   `POST /v1/evaluate`: Upload RFP and vendor docs to initiate the pipeline.
*   `GET /v1/status/{job_id}`: Poll for the current state of the agentic graph.
*   `GET /v1/comparison/{job_id}`: Retrieve the side-by-side analysis.
*   `POST /v1/approve`: Submit the final human decision back to the system.

## 11. Security Requirements
*   **Authentication:** Secure login for Procurement Managers.
*   **Data Isolation:** Ensure vendor documents from one RFP are not leaked into the evaluation of another.
*   **Data Protection:** Encryption at rest for all documents in GCS and BigQuery.

## 12. Deployment & Infrastructure
*   **Containerization:** All services deployed as Docker containers.
*   **Cloud Provider:** Google Cloud Platform (GCP).
*   **Compute:** Serverless execution via Cloud Run for the API and Agents.
*   **CI/CD:** Automated pipeline for testing agent logic and prompt performance.

## 13. Success Metrics
*   **Time Savings:** % reduction in time spent per vendor evaluation.
*   **Scoring Variance:** Reduction in score deviation between different human evaluators when assisted by the AI.
*   **User Trust:** Qualitative feedback on the helpfulness and accuracy of the "Explanation Generation" node.

## 14. Timeline & Milestones
*   **Phase 1 (MVP):** Intake, Criteria Extraction, and Basic Scoring (4 weeks).
*   **Phase 2 (Intelligence):** Vector Retrieval and Risk/Bias Detection (3 weeks).
*   **Phase 3 (UI/UX):** Streamlit Dashboard and HITL Approval Loop (3 weeks).
*   **Phase 4 (Compliance):** Audit logging and BigQuery integration (2 weeks).

## 15. Open Questions & Risks
*   **Hallucination Risk:** How does the system handle LLM hallucinations in pricing extraction? (Mitigation: Use structured parsing and MCP tool calls).
*   **Data Privacy:** Handling sensitive vendor financial data.
*   **Integration:** Future requirements for connecting directly to ERP systems (e.g., SAP, Oracle).
