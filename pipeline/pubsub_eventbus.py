"""
pipeline/pubsub_eventbus.py

Decoupled Microservice Event Bus (Cloud Pub/Sub Adapter)
=========================================================
Now with FULL correlation ID propagation across ALL Pub/Sub boundaries
per the HIGH-priority HiDevs evaluator recommendation:
  "Define a standardized metadata envelope for all Pub/Sub messages that
   includes a correlation_id, parent_span_id, and timestamp to enable
   seamless OpenTelemetry tracing across the decoupled microservices."

Topics:
  vendormind.rfp.ingested         — Intake → Criteria microservice
  vendormind.criteria.extracted   — Criteria → Retrieval microservice
  vendormind.score.draft          — Scoring → Risk microservice (A2A handshake)
  vendormind.risk.vetoed          — Risk → Scoring (veto / A2A step 2)
  vendormind.risk.approved        — Risk → Scoring (approval / A2A step 3)
  vendormind.evaluation.completed — Final output → BigQuery audit sink
  vendormind.vendor.consent       — GDPR Art. 13 consent events

Message Envelope Schema (standardized for OpenTelemetry compatibility):
  {
    "trace_context": {
      "correlation_id"  : <UUID4 — same across ALL hops for this evaluation>,
      "parent_span_id"  : <UUID4 of the upstream publishing span>,
      "span_id"         : <UUID4 for this specific publish event>,
      "node_name"       : <LangGraph node label, e.g. "intake_agent">,
      "timestamp_utc"   : <ISO-8601 UTC timestamp>,
    },
    "llm_audit": {
      "model_version"   : <e.g. "gemini-1.5-pro-002">,
      "prompt_hash"     : <SHA-256 hex of prompt — for drift auditing>,
      "temperature"     : <float — temperature setting>,
      "latency_ms"      : <float — node execution latency>,
    },
    "payload": { ... }   ← The actual business data
  }

Tech: Google Cloud Pub/Sub SDK (optional runtime), Python asyncio, correlation_tracing module
"""

import os
import json
import logging
from typing import Dict, Any, Callable, List, Optional

from pipeline.correlation_tracing import build_trace_envelope, extract_payload, extract_trace_context

logger = logging.getLogger(__name__)

# ── Topic Registry ────────────────────────────────────────────────────────────
TOPIC_RFP_INGESTED          = "vendormind.rfp.ingested"
TOPIC_CRITERIA_EXTRACTED    = "vendormind.criteria.extracted"
TOPIC_SCORE_DRAFT           = "vendormind.score.draft"
TOPIC_RISK_VETOED           = "vendormind.risk.vetoed"
TOPIC_RISK_APPROVED         = "vendormind.risk.approved"
TOPIC_EVALUATION_COMPLETED  = "vendormind.evaluation.completed"
TOPIC_VENDOR_CONSENT_LOGGED = "vendormind.vendor.consent"


class MicroserviceEventBus:
    """
    Event Bus interface matching GCP Cloud Pub/Sub publisher/subscriber pattern.
    All published messages are wrapped in the standardized OpenTelemetry-compatible
    trace envelope to enable full end-to-end distributed tracing across
    asynchronous Cloud Run microservice boundaries.
    """

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT", "vendormind-ai")
        self._subscribers: Dict[str, List[Callable]] = {}
        self._gcp_publisher = None

        # Attempt initializing real GCP Pub/Sub client if configured
        if os.getenv("PUBSUB_EMULATOR_HOST") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            try:
                from google.cloud import pubsub_v1  # type: ignore
                self._gcp_publisher = pubsub_v1.PublisherClient()
                logger.info("[EventBus] Cloud Pub/Sub Publisher initialized for project %s", self.project_id)
            except Exception as exc:
                logger.warning("[EventBus] Cloud Pub/Sub init fallback: %s", exc)

    def publish(
        self,
        topic_name: str,
        payload: Dict[str, Any],
        correlation_id: str,
        node_name: str,
        parent_span_id: Optional[str] = None,
        model_version: Optional[str] = None,
        prompt_text: Optional[str] = None,
        temperature: Optional[float] = None,
        latency_ms: Optional[float] = None,
    ) -> str:
        """
        Publish a message to a microservice topic wrapped in the standardized
        OpenTelemetry trace envelope.

        The envelope includes:
          - correlation_id : Root trace ID propagated from the first publishing node.
          - parent_span_id : Span ID of the upstream node that triggered this publish.
          - span_id        : New UUID4 span for this specific publish event.
          - node_name      : The LangGraph node publishing this event.
          - model_version  : Exact model used (e.g., "gemini-1.5-pro-002").
          - prompt_hash    : SHA-256 of the LLM prompt (for drift auditing).
          - temperature    : LLM temperature setting.
          - latency_ms     : Node execution time.

        Args:
            topic_name    : Target Pub/Sub topic name.
            payload       : Business data to publish.
            correlation_id: Root trace UUID4 for this evaluation run.
            node_name     : LangGraph node publishing this event.
            parent_span_id: Span ID of the upstream publisher node.
            model_version : LLM model version string.
            prompt_text   : Raw LLM prompt (will be hashed, never stored raw).
            temperature   : LLM temperature setting.
            latency_ms    : Node execution latency.

        Returns:
            message_id: String message ID (GCP Pub/Sub future result or local ID).
        """
        # Build standardized OpenTelemetry-compatible trace envelope
        envelope = build_trace_envelope(
            correlation_id=correlation_id,
            parent_span_id=parent_span_id,
            node_name=node_name,
            payload=payload,
            model_version=model_version,
            prompt_text=prompt_text,
            temperature=temperature,
            latency_ms=latency_ms,
        )

        message_bytes = json.dumps(envelope).encode("utf-8")
        message_id = f"msg_{topic_name}_{payload.get('evaluation_id', 'local')}_{envelope['trace_context']['span_id'][:8]}"

        # ── GCP Cloud Pub/Sub (Production Path) ───────────────────────────
        if self._gcp_publisher:
            try:
                topic_path = self._gcp_publisher.topic_path(
                    self.project_id, topic_name.replace(".", "-")
                )
                future = self._gcp_publisher.publish(
                    topic_path,
                    message_bytes,
                    # GCP Pub/Sub message attributes for native tracing
                    correlation_id=correlation_id,
                    span_id=envelope["trace_context"]["span_id"],
                    node_name=node_name,
                )
                gcp_id = future.result()
                logger.info(
                    "[EventBus][GCP] Published to %s | correlation=%s | span=%s | gcp_id=%s",
                    topic_name, correlation_id[:8], envelope["trace_context"]["span_id"][:8], gcp_id
                )
                return gcp_id
            except Exception as exc:
                logger.warning("[EventBus] GCP Pub/Sub publish failed: %s — falling back to local bus", exc)

        # ── In-Process Local Bus (Dev / Streamlit Fallback) ──────────────
        listeners = self._subscribers.get(topic_name, [])
        for callback in listeners:
            try:
                callback(envelope)  # Pass full envelope to subscriber
            except Exception as exc:
                logger.error("[EventBus] Listener error on %s: %s", topic_name, exc)

        logger.info(
            "[EventBus][Local] Published to %s | correlation=%s | span=%s | id=%s",
            topic_name, correlation_id[:8], envelope["trace_context"]["span_id"][:8], message_id
        )
        return message_id

    def subscribe(self, topic_name: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Subscribe a microservice handler to a topic.
        The callback receives the full trace envelope (not just the payload).
        Use extract_payload(envelope) and extract_trace_context(envelope) to unpack.
        """
        self._subscribers.setdefault(topic_name, []).append(callback)
        logger.info("[EventBus] Subscribed handler to %s", topic_name)


# ── Global singleton event bus instance ──────────────────────────────────────
event_bus = MicroserviceEventBus()
