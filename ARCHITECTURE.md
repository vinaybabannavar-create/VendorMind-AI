# VendorMind AI — System Architecture Specification
*Decoupled Microservices Architecture · 8-Node Stateful LangGraph Agentic Pipeline · Google Cloud Pub/Sub Event Bus · OpenTelemetry Correlation ID Tracing · Gemma 3 27B-IT Edge Privacy Gate*

---

## 1. Executive System Overview

VendorMind AI transforms raw RFP requirements and vendor proposals into explainable, compliant, and multi-signal shortlists using an **8-node stateful agentic graph (LangGraph)**, **decoupled Cloud Run microservices**, and **Google Cloud Pub/Sub**.

The architecture enforces:
1. **Edge Privacy (GDPR Article 5)**: Local PII redaction using Gemma 3 27B-IT at Node 1 before cloud egress.
2. **A2A EEOC Negotiation**: 3-step Agent-to-Agent handshake (`score_draft` -> `risk_veto` -> `score_final`) enforcing EEOC 4/5ths Rule Adverse Impact Ratios (AIR >= 0.80).
3. **Distributed Correlation Tracing**: Standardized message envelopes carrying `correlation_id`, `parent_span_id`, and `span_id` across all Pub/Sub topic boundaries.
4. **LLM Invocation Auditability**: OpenTelemetry logging capturing SHA-256 `prompt_hash`, exact `model_version`, and `temperature` for every LLM call.
5. **Vector Sync Consistency**: Write-Through + Periodic Batch Reconciliation (300s daemon) between Vertex AI Vector Search (authoritative) and local Qdrant (fallback).

---

## 2. Multi-Tier Decoupled Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 1 — USER INTERFACE TIER                                                            │
│   Procurement Officer (Web Browser)                                                     │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │ HTTP / Web Speech API
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 2 — FRONTEND DASHBOARD TIER                                                        │
│   Streamlit Procurement Dashboard (ui/app.py)                                           │
│   • Neural Glassmorphic Dashboard (Port 8516)                                           │
│   • GDPR Art. 13 Consent Checkbox & Art. 14 Transparency Notice Queue                   │
│   • 1-v-1 Cyber Duel Matrix · Enkrypt AI Guardrail Badges · Voice Briefing Engine       │
│   • Tab 6: Distributed Trace, Prompt Hash Audit & Vector Sync Telemetry                 │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │ REST API (HTTPS / TLS 1.3 / OAuth2 JWT)
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 3 — SECURITY GATEWAY & CONSENT TIER                                                │
│   FastAPI Gateway (api/main.py, Cloud Run)                                              │
│   • OAuth2 Password Bearer / JWT Token Issuance (`POST /token`)                         │
│   • GDPR Consent Capture & Transparency Notice Dispatch (`POST /v1/consent`)            │
│   • OWASP A03 Input Validation (Pydantic v2) & OWASP A07 Rate Limiting (100 req/min/IP)    │
│   • OpenTelemetry Observability Endpoint (`GET /evaluation/{id}/telemetry`)             │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 4 — EVENT BUS & DECOUPLED MICROSERVICES (pipeline/pubsub_eventbus.py)               │
│   Topics:                                                                               │
│     • `vendormind.rfp.ingested`         (Intake ➔ Criteria)                              │
│     • `vendormind.criteria.extracted`   (Criteria ➔ Retrieval)                           │
│     • `vendormind.score.draft`          (Scoring ➔ Risk A2A Step 1)                      │
│     • `vendormind.risk.vetoed`          (Risk ➔ Scoring A2A Step 2 Veto)                 │
│     • `vendormind.risk.approved`        (Risk ➔ Scoring A2A Step 3 Approval)             │
│     • `vendormind.evaluation.completed` (Pipeline Output ➔ BigQuery Audit)              │
│     • `vendormind.vendor.consent`       (GDPR Consent Logger)                           │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 5 — 8-NODE STATEFUL AGENTIC PIPELINE (pipeline/orchestrator.py)                     │
│                                                                                         │
│   [Node 1: Intake Agent]        ◄── Gemma 3 27B-IT Edge PII Scrubbing (GDPR Art. 5)     │
│              │                                                                          │
│              ▼                                                                          │
│   [Node 2: Criteria Agent]      ◄── Gemini 1.5 Pro + MCP Context Injection                │
│              │                                                                          │
│              ▼                                                                          │
│   [Node 3: Retrieval Agent]     ◄── VectorSyncManager (Vertex AI ↔ Qdrant Write-Through)  │
│              │                                                                          │
│              ▼                                                                          │
│   [Node 4: Scoring Agent]       ◄── 4-Signal Composite Scoring (Cost/Compliance/Fit)    │
│              │                                                                          │
│              │ ◄════════════════════════════════════════════════════════════════════►   │
│              │ A2A PROTOCOL HANDSHAKE (Score Draft ⇄ EEOC Adverse Impact Veto)           │
│              │ ◄════════════════════════════════════════════════════════════════════►   │
│              ▼                                                                          │
│   [Node 5: Risk & Bias Agent]   ◄── Gemini 1.5 Pro + Enkrypt AI Guardrails                  │
│              │                                                                          │
│              ▼                                                                          │
│   [Node 6: Explanation Agent]   ◄── Gemini 1.5 Pro (EU AI Act Art. 13 CRISPE Prompt)       │
│              │                                                                          │
│              ▼                                                                          │
│   [Node 7: Comparison Agent]    ◄── Side-by-Side Ranked Pandas Matrix                       │
│              │                                                                          │
│              ▼                                                                          │
│   [Node 8: Output & HITL Agent] ◄── Procurement Officer Approval Gate + Web Speech      │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 6 — DATA, PERSISTENCE & OBSERVABILITY TIER                                         │
│   • BigQuery Audit Store (Immutable Event Logs, A2A Messages, 90-Day Retention TTL)     │
│   • Vertex AI Vector Search (Primary Authoritative Knowledge Base)                      │
│   • Qdrant Local Fallback (Mirrored via Write-Through + 300s Batch Reconciliation Daemon) │
│   • OpenTelemetry Audit Log (correlation_id, prompt_hash SHA-256, model_version)        │
│   • Google Cloud Storage (Raw RFP PDFs & Vendor Proposals)                              │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Standardized Pub/Sub Message Envelope & Tracing (`pipeline/correlation_tracing.py`)

To resolve distributed tracing across asynchronous Google Cloud Pub/Sub boundaries, every published event is wrapped in a standardized OpenTelemetry trace envelope:

```json
{
  "trace_context": {
    "correlation_id": "8f3c7b2a-1e4d-4a9f-8b2c-3d4e5f6a7b8c",
    "parent_span_id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
    "span_id": "9f8e7d6c-5b4a-3f2e-1d0c-9b8a7f6e5d4c",
    "node_name": "scoring_agent",
    "timestamp_utc": "2026-08-05T21:22:00.123456Z"
  },
  "llm_audit": {
    "model_version": "gemini-1.5-pro-002",
    "prompt_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "temperature": 0.1,
    "latency_ms": 342.50
  },
  "payload": {
    "evaluation_id": "eval_101",
    "scores": { "vendor_1": 0.88, "vendor_2": 0.74 }
  }
}
```

### Trace Propagation Rules
1. **`correlation_id`**: Generated at Node 1 (Intake) or API entry point. Passed unchanged across ALL microservices and Pub/Sub topics for the entire evaluation run.
2. **`parent_span_id`**: Set to the `span_id` of the upstream node that published the message. Enables full DAG reconstruction.
3. **`span_id`**: Newly generated UUID4 for each node execution.

---

## 4. Vector Search Write-Through & Reconciliation Protocol (`pipeline/vector_sync.py`)

To ensure read consistency and fault isolation between primary cloud storage (**Vertex AI Vector Search**) and local fallback (**Qdrant**), VendorMind AI enforces a **Write-Through + Periodic Batch Reconciliation** protocol.

```
                  ┌───────────────────────────────┐
                  │ Upsert Vendor Embedding       │
                  └───────────────┬───────────────┘
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
                   ▼                             ▼
   ┌──────────────────────────────┐ ┌──────────────────────────────┐
   │ Vertex AI Vector Search      │ │ Local Qdrant Fallback        │
   │ (Primary / Authoritative)    │ │ (Mirrored Write-Through)     │
   └──────────────────────────────┘ └──────────────┬───────────────┘
                                                   │
                                         [If Write Fails]
                                                   │
                                                   ▼
                                    ┌──────────────────────────────┐
                                    │ Pending Reconciliation Queue │
                                    └──────────────┬───────────────┘
                                                   │
                                     [Background Daemon (300s)]
                                                   │
                                                   ▼
                                    ┌──────────────────────────────┐
                                    │ Re-sync to Qdrant            │
                                    └──────────────────────────────┘
```

### Protocol Mechanics
- **Write-Through (Real-Time)**: When a new vendor vector is upserted, `VectorSyncManager.upsert_vendor()` writes to Vertex AI first, then immediately mirrors to Qdrant.
- **Read Fallback Chain**: Queries check Vertex AI Vector Search (with 5s timeout). If Vertex AI is unreachable, queries automatically fall back to local Qdrant.
- **Periodic Batch Reconciliation**: A background daemon thread executes `VectorSyncManager.reconcile()` every 300 seconds to retry failed Qdrant writes and eliminate data drift.

---

## 5. Node Specifications & Technical Responsibilities

| Node ID | Node Name | Responsibilities | Technology & Models | Key Outputs / State Updates |
|---|---|---|---|---|
| **Node 1** | Intake Agent | Parses PDFs/TXTs; scrubs PII before cloud egress | Gemma 3 27B-IT, PyPDF2 | `parsed_rfp`, `parsed_vendors`, `gemma_pii_results` |
| **Node 2** | Criteria Extraction Agent | Extracts explicit/implicit criteria; flags RFP bias | Gemini 1.5 Pro, MCP | `criteria_dict`, `rfp_bias_flags` |
| **Node 3** | Vendor Retrieval Agent | Fetches historical performance & certs via vector search | Vertex Vector Search, Qdrant, sentence-transformers | `vendor_context`, `vector_sync_status` |
| **Node 4** | Multi-Signal Scoring Agent | Computes 4-signal composite score; initiates A2A handshake | Gemini 1.5 Pro, Python, NumPy | `score_draft`, `a2a_log` |
| **Node 5** | Risk & Bias Detection Agent | Monitors EEOC 4/5ths rule; triggers A2A veto if AIR < 0.80 | Gemini 1.5 Pro, Enkrypt AI | `risk_flags`, `eeoc_report`, `a2a_veto_count` |
| **Node 6** | Explanation Generation Agent | Generates 3-sentence human-readable score rationale | Gemini 1.5 Pro (CRISPE Prompt) | `explanations` (EU AI Act Art. 13) |
| **Node 7** | Comparison Agent | Generates side-by-side ranked comparison matrix | Pandas, Python | `comparison_table`, `rankings` |
| **Node 8** | Output & HITL Agent | Presents recommendations to Procurement Officer | Streamlit, Web Speech API | `hitl_approved`, `approver_note`, `final_report` |

---

## 6. OpenTelemetry & LLM Audit Logging Schema

To satisfy enterprise auditability requirements and detect LLM prompt drift, every node logs invocation telemetry to BigQuery and exposes it via `GET /evaluation/{id}/telemetry`:

```python
{
  "node_name": "criteria_agent",
  "model_version": "gemini-1.5-pro-002",
  "prompt_hash": "a3f8902c4b1e582d90a12e3f456789abcdef0123456789abcdef0123456789ab", # SHA-256
  "temperature": 0.1,
  "latency_ms": 412.8,
  "span_id": "c7a8b9c0-d1e2-3f4a-5b6c-7d8e9f0a1b2c",
  "parent_span_id": "f0e9d8c7-b6a5-4f3e-2d1c-0b9a8f7e6d5c",
  "timestamp_utc": "2026-08-05T21:22:00.450Z"
}
```

---

## 7. Security, Privacy & Regulatory Controls Summary

- **GDPR Article 5**: Gemma 3 27B-IT redacts PII at Node 1 edge boundary.
- **GDPR Article 13/14**: Consent capture `/v1/consent` & automated DPO transparency notices.
- **GDPR Article 17**: 90-day automatic data retention TTL in BigQuery.
- **EEOC 4/5ths Rule**: A2A negotiation applies fairness floor when AIR < 0.80.
- **EU AI Act Article 13**: Explainable 3-sentence score justifications citing evidence.
- **OWASP Top 10 Security**: OAuth2 JWT token auth, HSTS TLS 1.3 in transit, AES-256 at rest, Pydantic v2 input validation, 100 req/min IP rate limiting.
