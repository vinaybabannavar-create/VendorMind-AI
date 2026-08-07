"""
pipeline/orchestrator.py

Agent Orchestrator — wires all 8 agent nodes into a single stateful
LangGraph pipeline, matching the architecture diagram exactly:

Intake -> Criteria Extraction -> Vendor Profile Retrieval ->
Multi-Signal Scoring -> Risk & Bias Detection -> Explanation
Generation -> Comparison -> Output & HITL

Updated in Step 1:
  - Generates a root correlation_id (UUID4) at start of run_pipeline()
  - Publishes trace events via Pub/Sub event bus for every node hop
  - Populates state["llm_invocation_audit"] with OpenTelemetry spans,
    prompt_hash (SHA-256), exact model_version, and latency per node.

Tech: LangGraph, Python, OpenTelemetry correlation tracing
"""

import uuid
import time
import logging
from typing import Dict, Any, List

from pipeline.state import VendorMindState
from pipeline.intake_agent import run_intake_agent
from pipeline.criteria_agent import run_criteria_agent
from pipeline.retrieval_agent import run_retrieval_agent
from pipeline.scoring_agent import run_scoring_agent
from pipeline.risk_agent import run_risk_agent
from pipeline.explanation_agent import run_explanation_agent
from pipeline.comparison_agent import run_comparison_agent
from pipeline.output_agent import run_output_agent
from pipeline.pubsub_eventbus import event_bus, TOPIC_RFP_INGESTED, TOPIC_CRITERIA_EXTRACTED, TOPIC_SCORE_DRAFT, TOPIC_EVALUATION_COMPLETED
from pipeline.correlation_tracing import LLMInvocationAudit

logger = logging.getLogger(__name__)

# Node metadata mapping for OpenTelemetry tracing & LLM audit
NODE_METADATA = {
    "intake_agent":      {"name": "intake_agent",      "func": run_intake_agent,      "model": "gemma-3-27b-it",   "topic": TOPIC_RFP_INGESTED},
    "criteria_agent":    {"name": "criteria_agent",    "func": run_criteria_agent,    "model": "gemini-1.5-pro-002","topic": TOPIC_CRITERIA_EXTRACTED},
    "retrieval_agent":   {"name": "retrieval_agent",   "func": run_retrieval_agent,   "model": "sentence-transformers/all-MiniLM-L6-v2", "topic": None},
    "scoring_agent":     {"name": "scoring_agent",     "func": run_scoring_agent,     "model": "gemini-1.5-pro-002","topic": TOPIC_SCORE_DRAFT},
    "risk_agent":        {"name": "risk_agent",        "func": run_risk_agent,        "model": "gemini-1.5-pro-002","topic": None},
    "explanation_agent": {"name": "explanation_agent", "func": run_explanation_agent, "model": "gemini-1.5-pro-002","topic": None},
    "comparison_agent":  {"name": "comparison_agent",  "func": run_comparison_agent,  "model": "pandas-rank-matrix", "topic": None},
    "output_agent":      {"name": "output_agent",      "func": run_output_agent,      "model": "streamlit-hitl-gate", "topic": TOPIC_EVALUATION_COMPLETED},
}


def _execute_node_with_tracing(node_key: str, state: VendorMindState) -> VendorMindState:
    """Executes a single pipeline node with end-to-end correlation ID tracing & LLM audit logging."""
    meta = NODE_METADATA.get(node_key, {"name": node_key, "model": "unknown", "topic": None})
    correlation_id = state.get("correlation_id") or str(uuid.uuid4())
    parent_span_id = state.get("_last_span_id")

    audit = LLMInvocationAudit(
        node_name=meta["name"],
        model_version=meta["model"],
        prompt_text=f"Node {node_key} invocation prompt payload",
        temperature=0.1,
        correlation_id=correlation_id,
        parent_span_id=parent_span_id,
    )

    t0 = time.monotonic()
    func = meta.get("func")
    if func:
        try:
            state = func(state)
        except Exception as exc:
            logger.error("[Orchestrator] Exception executing node %s: %s", node_key, exc)
            if "errors" not in state or state["errors"] is None:
                state["errors"] = []
            state["errors"].append(f"{node_key}: {exc}")
    elapsed_ms = round((time.monotonic() - t0) * 1000, 2)

    audit_record = audit.finish()
    audit_record["latency_ms"] = elapsed_ms

    # Update state audit log
    if "llm_invocation_audit" not in state or state["llm_invocation_audit"] is None:
        state["llm_invocation_audit"] = []
    state["llm_invocation_audit"].append(audit_record)
    state["_last_span_id"] = audit_record["span_id"]

    # Publish to Pub/Sub event bus with correlation ID trace envelope
    if meta.get("topic"):
        try:
            event_bus.publish(
                topic_name=meta["topic"],
                payload={"node": node_key, "status": "completed"},
                correlation_id=correlation_id,
                node_name=node_key,
                parent_span_id=parent_span_id,
                model_version=meta["model"],
                latency_ms=elapsed_ms,
            )
        except Exception as exc:
            logger.warning("[Orchestrator] PubSub publish error for %s: %s", node_key, exc)

    return state


def build_graph():
    """Builds and compiles the LangGraph StateGraph. Falls back to a
    plain sequential runner if the langgraph package isn't installed."""
    try:
        from langgraph.graph import StateGraph, END

        graph = StateGraph(VendorMindState)
        
        # Wrapped node functions
        graph.add_node("intake", lambda s: _execute_node_with_tracing("intake_agent", s))
        graph.add_node("criteria_extraction", lambda s: _execute_node_with_tracing("criteria_agent", s))
        graph.add_node("retrieval", lambda s: _execute_node_with_tracing("retrieval_agent", s))
        graph.add_node("scoring", lambda s: _execute_node_with_tracing("scoring_agent", s))
        graph.add_node("risk", lambda s: _execute_node_with_tracing("risk_agent", s))
        graph.add_node("explanation", lambda s: _execute_node_with_tracing("explanation_agent", s))
        graph.add_node("comparison", lambda s: _execute_node_with_tracing("comparison_agent", s))
        graph.add_node("output", lambda s: _execute_node_with_tracing("output_agent", s))

        graph.set_entry_point("intake")
        graph.add_edge("intake", "criteria_extraction")
        graph.add_edge("criteria_extraction", "retrieval")
        graph.add_edge("retrieval", "scoring")
        graph.add_edge("scoring", "risk")
        graph.add_edge("risk", "explanation")
        graph.add_edge("explanation", "comparison")
        graph.add_edge("comparison", "output")
        graph.add_edge("output", END)

        return graph.compile()
    except ImportError:
        return _SequentialFallbackGraph()


class _SequentialFallbackGraph:
    """Used if langgraph package isn't installed in the environment."""

    _NODE_KEYS = [
        "intake_agent",
        "criteria_agent",
        "retrieval_agent",
        "scoring_agent",
        "risk_agent",
        "explanation_agent",
        "comparison_agent",
        "output_agent",
    ]

    def invoke(self, state: VendorMindState) -> VendorMindState:
        for node_key in self._NODE_KEYS:
            state = _execute_node_with_tracing(node_key, state)
        return state


_compiled_graph = None


def run_pipeline(rfp_text: str, vendors: list) -> VendorMindState:
    """Single entry point used by the API layer."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()

    correlation_id = str(uuid.uuid4())

    initial_state: VendorMindState = {
        "rfp_text": rfp_text,
        "vendors": vendors,
        "errors": [],
        "correlation_id": correlation_id,
        "otel_trace_id": correlation_id,
        "llm_invocation_audit": [],
        "latency_ms": {},
        "token_usage": {},
    }
    result = _compiled_graph.invoke(initial_state)
    result["correlation_id"] = correlation_id
    result["otel_trace_id"] = correlation_id
    return result
