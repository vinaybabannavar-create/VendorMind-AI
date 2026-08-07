"""
tests/test_orchestrator.py

Unit tests for pipeline/orchestrator.py — covers:
  - run_pipeline() returns all required state keys
  - correlation_id is a valid UUID4
  - llm_invocation_audit contains exactly 8 entries (one per node)
  - Each audit entry has required OpenTelemetry fields
  - Errors list is accessible (even if empty on success)
  - _SequentialFallbackGraph runs all 8 nodes in correct order
  - Node tracing function populates audit records correctly
  - Pipeline handles vendor list with multiple vendors
  - Pipeline produces final_report output
  - Pipeline produces comparison_table output
"""

import sys
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.orchestrator import (
    run_pipeline,
    _execute_node_with_tracing,
    _SequentialFallbackGraph,
    NODE_METADATA,
)
from pipeline.state import VendorMindState


# ── Shared Test Fixtures ───────────────────────────────────────────────────────

SAMPLE_RFP = (
    "We need a cloud infrastructure vendor with ISO27001 and SOC2 certification. "
    "Budget is $100,000 annually. SLA must be at least 99.9%."
)

SAMPLE_VENDORS = [
    {
        "vendor_id": "alpha_inc",
        "vendor_name": "Alpha Inc",
        "raw_text": (
            "Alpha Inc is ISO27001 and SOC2 certified. We offer cloud hosting at $95,000 "
            "per year with 99.95% SLA and enterprise support."
        ),
    },
    {
        "vendor_id": "beta_solutions",
        "vendor_name": "Beta Solutions",
        "raw_text": (
            "Beta Solutions provides cloud services at $80,000 per year. "
            "ISO27001 certified with 99.9% uptime SLA."
        ),
    },
]


def _make_base_state() -> VendorMindState:
    """Return a minimal valid initial state dict."""
    cid = str(uuid.uuid4())
    return {
        "rfp_text": SAMPLE_RFP,
        "vendors": SAMPLE_VENDORS,
        "errors": [],
        "correlation_id": cid,
        "otel_trace_id": cid,
        "llm_invocation_audit": [],
        "latency_ms": {},
        "token_usage": {},
    }


# ── NODE_METADATA ─────────────────────────────────────────────────────────────

class TestNodeMetadata:
    def test_exactly_8_nodes_defined(self):
        assert len(NODE_METADATA) == 8

    def test_all_nodes_have_required_keys(self):
        required = {"name", "func", "model", "topic"}
        for key, meta in NODE_METADATA.items():
            missing = required - set(meta.keys())
            assert not missing, f"Node '{key}' missing keys: {missing}"

    def test_node_names_match_keys(self):
        for key, meta in NODE_METADATA.items():
            assert meta["name"] == key

    def test_all_node_funcs_are_callable(self):
        for key, meta in NODE_METADATA.items():
            assert callable(meta["func"]), f"Node '{key}' func is not callable"


# ── _SequentialFallbackGraph ──────────────────────────────────────────────────

class TestSequentialFallbackGraph:
    def test_node_count_is_8(self):
        graph = _SequentialFallbackGraph()
        assert len(graph._NODE_KEYS) == 8

    def test_correct_node_order(self):
        graph = _SequentialFallbackGraph()
        expected_order = [
            "intake_agent",
            "criteria_agent",
            "retrieval_agent",
            "scoring_agent",
            "risk_agent",
            "explanation_agent",
            "comparison_agent",
            "output_agent",
        ]
        assert graph._NODE_KEYS == expected_order

    def test_invoke_runs_all_nodes(self):
        graph = _SequentialFallbackGraph()
        state = _make_base_state()
        visited = []

        def mock_trace(node_key, s):
            visited.append(node_key)
            return s

        with patch("pipeline.orchestrator._execute_node_with_tracing", side_effect=mock_trace):
            graph.invoke(state)

        assert visited == graph._NODE_KEYS


# ── _execute_node_with_tracing ────────────────────────────────────────────────

class TestNodeTracing:
    def test_returns_updated_state(self):
        state = _make_base_state()
        with patch.dict(
            "pipeline.orchestrator.NODE_METADATA",
            {"intake_agent": {
                "name": "intake_agent",
                "func": lambda s: {**s, "rfp_text": s["rfp_text"]},
                "model": "test-model",
                "topic": None,
            }},
        ):
            result = _execute_node_with_tracing("intake_agent", state)
        assert isinstance(result, dict)

    def test_audit_record_appended(self):
        state = _make_base_state()
        with patch.dict(
            "pipeline.orchestrator.NODE_METADATA",
            {"intake_agent": {
                "name": "intake_agent",
                "func": lambda s: s,
                "model": "gemma-3-27b-it",
                "topic": None,
            }},
        ):
            result = _execute_node_with_tracing("intake_agent", state)
        assert len(result.get("llm_invocation_audit", [])) == 1

    def test_audit_record_has_otel_fields(self):
        state = _make_base_state()
        with patch.dict(
            "pipeline.orchestrator.NODE_METADATA",
            {"intake_agent": {
                "name": "intake_agent",
                "func": lambda s: s,
                "model": "gemma-3-27b-it",
                "topic": None,
            }},
        ):
            result = _execute_node_with_tracing("intake_agent", state)
        audit = result["llm_invocation_audit"][0]
        assert "span_id" in audit
        assert "latency_ms" in audit

    def test_last_span_id_set_in_state(self):
        state = _make_base_state()
        with patch.dict(
            "pipeline.orchestrator.NODE_METADATA",
            {"intake_agent": {
                "name": "intake_agent",
                "func": lambda s: s,
                "model": "gemma-3-27b-it",
                "topic": None,
            }},
        ):
            result = _execute_node_with_tracing("intake_agent", state)
        assert "_last_span_id" in result


# ── run_pipeline() ────────────────────────────────────────────────────────────

# Mock all 8 agent node functions so tests are fast and don't need API keys
MOCK_NODE_FUNCS = {
    "intake_agent":      lambda s: {**s, "rfp_cleaned": s.get("rfp_text", "")},
    "criteria_agent":    lambda s: {**s, "criteria": ["ISO27001", "SOC2"]},
    "retrieval_agent":   lambda s: {**s, "retrieved_context": []},
    "scoring_agent":     lambda s: {**s, "vendor_scores": {"alpha_inc": 0.87}},
    "risk_agent":        lambda s: {**s, "risk_summary": "Low risk"},
    "explanation_agent": lambda s: {**s, "explanations": {"alpha_inc": "Top choice"}},
    "comparison_agent":  lambda s: {**s, "comparison_table": [{"vendor_id": "alpha_inc", "score": 0.87}]},
    "output_agent":      lambda s: {**s, "final_report": "Alpha Inc is recommended."},
}


class TestRunPipeline:
    def _run(self):
        patched_meta = {
            k: {**v, "func": MOCK_NODE_FUNCS[k]}
            for k, v in NODE_METADATA.items()
        }
        with patch("pipeline.orchestrator.NODE_METADATA", patched_meta):
            return run_pipeline(rfp_text=SAMPLE_RFP, vendors=SAMPLE_VENDORS)

    def test_returns_dict(self):
        result = self._run()
        assert isinstance(result, dict)

    def test_has_correlation_id(self):
        result = self._run()
        assert "correlation_id" in result
        try:
            uuid.UUID(result["correlation_id"], version=4)
        except ValueError:
            assert False, "correlation_id is not a valid UUID4"

    def test_has_otel_trace_id(self):
        result = self._run()
        assert "otel_trace_id" in result

    def test_correlation_matches_otel_trace(self):
        result = self._run()
        assert result["correlation_id"] == result["otel_trace_id"]

    def test_llm_audit_is_list(self):
        result = self._run()
        assert isinstance(result.get("llm_invocation_audit", []), list)

    def test_llm_audit_has_8_records(self):
        result = self._run()
        audit = result.get("llm_invocation_audit", [])
        assert len(audit) == 8, f"Expected 8 audit records, got {len(audit)}"

    def test_each_audit_record_has_latency(self):
        result = self._run()
        for rec in result.get("llm_invocation_audit", []):
            assert "latency_ms" in rec, f"Audit record missing latency_ms: {rec}"

    def test_errors_key_present(self):
        result = self._run()
        assert "errors" in result

    def test_vendors_preserved_in_state(self):
        result = self._run()
        assert "vendors" in result
        assert len(result["vendors"]) == len(SAMPLE_VENDORS)

    def test_rfp_text_preserved_in_state(self):
        result = self._run()
        assert result.get("rfp_text") == SAMPLE_RFP

    def test_different_runs_have_unique_correlation_ids(self):
        patched_meta = {k: {**v, "func": MOCK_NODE_FUNCS[k]} for k, v in NODE_METADATA.items()}
        with patch("pipeline.orchestrator.NODE_METADATA", patched_meta):
            r1 = run_pipeline(rfp_text=SAMPLE_RFP, vendors=SAMPLE_VENDORS)
            r2 = run_pipeline(rfp_text=SAMPLE_RFP, vendors=SAMPLE_VENDORS)
        assert r1["correlation_id"] != r2["correlation_id"]

    def test_final_report_present(self):
        result = self._run()
        assert "final_report" in result
        assert isinstance(result["final_report"], str)

    def test_comparison_table_present(self):
        result = self._run()
        assert "comparison_table" in result
        assert isinstance(result["comparison_table"], list)
