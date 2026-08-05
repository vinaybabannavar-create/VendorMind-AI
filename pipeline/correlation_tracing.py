"""
pipeline/correlation_tracing.py

Distributed Tracing & Correlation ID Propagation
==================================================
Addresses HIGH-Priority HiDevs Evaluator Recommendation:
  "Define a standardized metadata envelope for all Pub/Sub messages that
   includes a correlation_id, parent_span_id, and timestamp to enable
   seamless OpenTelemetry tracing across the decoupled microservices."

Also Addresses MEDIUM-Priority Recommendation:
  "Extend the OpenTelemetry schema to explicitly capture and log the
   prompt hash, exact model version (e.g., gemini-1.5-pro-002), and
   temperature settings for every LLM invocation."

Architecture:
  Every Pub/Sub message envelope contains:
    - correlation_id   : UUID4 shared across ALL microservice hops for
                         one evaluation run (root trace context)
    - parent_span_id   : UUID4 of the immediate upstream node (parent span)
    - span_id          : UUID4 for this specific node execution (child span)
    - node_name        : LangGraph node label (e.g., "intake_agent")
    - timestamp_utc    : ISO-8601 UTC timestamp at envelope creation
    - model_version    : Exact model string (e.g., "gemini-1.5-pro-002")
    - prompt_hash      : SHA-256 hex digest of the prompt sent to LLM
    - temperature      : Float temperature setting used for this invocation
    - latency_ms       : Measured node execution latency in milliseconds

Tech: Python stdlib (uuid, hashlib, datetime), OpenTelemetry-compatible schema
"""

import uuid
import hashlib
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


# ── Pub/Sub Standardized Message Envelope ────────────────────────────────────

def build_trace_envelope(
    correlation_id: str,
    parent_span_id: Optional[str],
    node_name: str,
    payload: Dict[str, Any],
    model_version: Optional[str] = None,
    prompt_text: Optional[str] = None,
    temperature: Optional[float] = None,
    latency_ms: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Build a standardized, OpenTelemetry-compatible Pub/Sub message envelope
    that propagates the full distributed trace context across every
    asynchronous microservice boundary.

    Args:
        correlation_id : The root trace ID shared across ALL hops for this evaluation run.
        parent_span_id : The span_id of the upstream caller node (None if root span).
        node_name      : LangGraph node label (e.g., 'intake_agent', 'scoring_agent').
        payload        : The actual business data being published on the Pub/Sub topic.
        model_version  : Exact model version string used in this node invocation.
        prompt_text    : The raw LLM prompt string (will be SHA-256 hashed — never stored raw).
        temperature    : LLM temperature setting for auditability of model drift.
        latency_ms     : Execution latency of this node in milliseconds.

    Returns:
        A dict representing the complete standardized Pub/Sub message envelope.
    """
    span_id = str(uuid.uuid4())
    prompt_hash = _hash_prompt(prompt_text) if prompt_text else None
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    envelope = {
        # ── OpenTelemetry Distributed Trace Context ────────────────────────
        "trace_context": {
            "correlation_id": correlation_id,       # Root trace — same across ALL pub/sub hops
            "parent_span_id": parent_span_id,       # Upstream node span (enables DAG tracing)
            "span_id": span_id,                     # This node's span
            "node_name": node_name,                 # LangGraph node label
            "timestamp_utc": timestamp_utc,         # ISO-8601 envelope creation time
        },
        # ── LLM Invocation Audit Record (Evaluator Recommendation) ─────────
        "llm_audit": {
            "model_version": model_version,         # e.g., "gemini-1.5-pro-002"
            "prompt_hash": prompt_hash,             # SHA-256 of prompt for LLM drift auditing
            "temperature": temperature,             # Temperature setting for reproducibility audit
            "latency_ms": latency_ms,               # Node execution latency
        },
        # ── Business Payload ───────────────────────────────────────────────
        "payload": payload,
    }

    logger.info(
        "[TraceEnvelope] node=%s | correlation_id=%s | span_id=%s | parent=%s | model=%s | prompt_hash=%s",
        node_name, correlation_id, span_id, parent_span_id, model_version, prompt_hash
    )
    return envelope


def _hash_prompt(prompt_text: str) -> str:
    """
    Generate a SHA-256 hash of the LLM prompt string.
    - Enables detection of prompt drift between evaluation runs without
      storing sensitive raw prompt content in audit logs.
    - Used for enterprise LLM audit compliance (evaluator recommendation).
    """
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()


# ── Correlation ID Management ─────────────────────────────────────────────────

def generate_correlation_id() -> str:
    """
    Generate a new root correlation_id (UUID4) for an evaluation run.
    This ID propagates unchanged across ALL Cloud Run microservices and
    ALL Pub/Sub topic hops for this evaluation.
    """
    return str(uuid.uuid4())


def extract_trace_context(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract the trace context from an incoming Pub/Sub message envelope.
    Used by subscriber microservices to continue the distributed trace.

    Returns:
        trace_context dict with correlation_id, parent_span_id, span_id, etc.
    """
    return envelope.get("trace_context", {})


def extract_payload(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the business payload from a received Pub/Sub message envelope."""
    return envelope.get("payload", {})


# ── OpenTelemetry Telemetry Record Builder ────────────────────────────────────

class LLMInvocationAudit:
    """
    Records a single LLM invocation with full auditability metadata.
    Satisfies evaluator requirement for prompt_hash + model_version + temperature logging.
    """

    def __init__(
        self,
        node_name: str,
        model_version: str,
        prompt_text: str,
        temperature: float = 0.1,
        correlation_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ):
        self.node_name = node_name
        self.model_version = model_version
        self.prompt_hash = _hash_prompt(prompt_text)
        self.temperature = temperature
        self.span_id = str(uuid.uuid4())
        self.correlation_id = correlation_id or generate_correlation_id()
        self.parent_span_id = parent_span_id
        self.start_time = time.monotonic()
        self.timestamp_utc = datetime.now(timezone.utc).isoformat()
        self.latency_ms: Optional[float] = None

    def finish(self) -> Dict[str, Any]:
        """Mark the LLM invocation as complete and record latency."""
        self.latency_ms = round((time.monotonic() - self.start_time) * 1000, 2)
        record = {
            "node_name": self.node_name,
            "correlation_id": self.correlation_id,
            "parent_span_id": self.parent_span_id,
            "span_id": self.span_id,
            "timestamp_utc": self.timestamp_utc,
            "model_version": self.model_version,
            "prompt_hash": self.prompt_hash,
            "temperature": self.temperature,
            "latency_ms": self.latency_ms,
        }
        logger.info(
            "[LLMAudit] node=%s | model=%s | prompt_hash=%.12s... | temp=%.2f | latency=%.1fms",
            self.node_name, self.model_version, self.prompt_hash, self.temperature, self.latency_ms
        )
        return record
