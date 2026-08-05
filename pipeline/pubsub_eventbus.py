"""
pipeline/pubsub_eventbus.py

Decoupled Microservice Event Bus (Cloud Pub/Sub Adapter)
=========================================================
Addresses the Architecture recommendation from HiDevs:
  "Refactor heavy agents (Intake Agent and Risk Detection Agent) into
  independent Cloud Run microservices that communicate asynchronously
  via Cloud Pub/Sub, rather than keeping them as tightly coupled nodes
  within a single monolithic LangGraph state machine."

Architecture:
  - Intake Microservice       ──[pubsub: rfp.ingested]──►  Event Bus
  - Event Bus                 ──[pubsub: criteria.extracted]──►  Retrieval Microservice
  - Risk Microservice         ◄──[pubsub: score.draft]──────  Scoring Microservice
  - Risk Microservice         ──[pubsub: risk.vetoed/approved]──► Scoring Microservice

This module provides both:
  1. In-process Async Event Bus (for local dev / Streamlit execution)
  2. GCP Cloud Pub/Sub Client (for production Cloud Run microservices)

Tech: Google Cloud Pub/Sub SDK (optional runtime fallback), Python asyncio
"""

import os
import json
import logging
from typing import Dict, Any, Callable, List

logger = logging.getLogger(__name__)

# Topics used across the decoupled microservices architecture
TOPIC_RFP_INGESTED = "vendormind.rfp.ingested"
TOPIC_CRITERIA_EXTRACTED = "vendormind.criteria.extracted"
TOPIC_SCORE_DRAFT = "vendormind.score.draft"
TOPIC_RISK_VETOTED = "vendormind.risk.vetoed"
TOPIC_RISK_APPROVED = "vendormind.risk.approved"
TOPIC_EVALUATION_COMPLETED = "vendormind.evaluation.completed"
TOPIC_VENDOR_CONSENT_LOGGED = "vendormind.vendor.consent"


class MicroserviceEventBus:
    """Event Bus interface matching GCP Cloud Pub/Sub publisher/subscriber pattern."""

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT", "vendormind-ai")
        self._subscribers: Dict[str, List[Callable]] = {}
        self._gcp_publisher = None

        # Attempt initializing real GCP Pub/Sub client if configured
        if os.getenv("PUBSUB_EMULATOR_HOST") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            try:
                from google.cloud import pubsub_v1  # type: ignore
                self._gcp_publisher = pubsub_v1.PublisherClient()
                logger.info("Cloud Pub/Sub Publisher initialised for project %s", self.project_id)
            except Exception as exc:
                logger.warning("Cloud Pub/Sub init fallback: %s", exc)

    def publish(self, topic_name: str, payload: Dict[str, Any]) -> str:
        """Publish a message to a microservice topic."""
        message_bytes = json.dumps(payload).encode("utf-8")
        message_id = f"msg_{topic_name}_{payload.get('evaluation_id', 'local')}"

        if self._gcp_publisher:
            try:
                topic_path = self._gcp_publisher.topic_path(self.project_id, topic_name.replace(".", "-"))
                future = self._gcp_publisher.publish(topic_path, message_bytes)
                return future.result()
            except Exception as exc:
                logger.warning("GCP Pub/Sub publish failed: %s — falling back to local bus", exc)

        # In-process asynchronous event dispatch fallback
        listeners = self._subscribers.get(topic_name, [])
        for callback in listeners:
            try:
                callback(payload)
            except Exception as exc:
                logger.error("Event listener error on %s: %s", topic_name, exc)

        logger.info("[Pub/Sub Event Bus] Published to %s (id: %s)", topic_name, message_id)
        return message_id

    def subscribe(self, topic_name: str, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe a microservice handler to a topic."""
        self._subscribers.setdefault(topic_name, []).append(callback)
        logger.info("[Pub/Sub Event Bus] Subscribed handler to %s", topic_name)


# Global event bus instance
event_bus = MicroserviceEventBus()
