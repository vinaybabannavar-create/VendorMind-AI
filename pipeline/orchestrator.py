"""
pipeline/orchestrator.py

Agent Orchestrator — wires all 8 agent nodes into a single stateful
LangGraph pipeline, matching the architecture diagram exactly:

Intake -> Criteria Extraction -> Vendor Profile Retrieval ->
Multi-Signal Scoring -> Risk & Bias Detection -> Explanation
Generation -> Comparison -> Output & HITL

Tech: LangGraph, Python
"""

from pipeline.state import VendorMindState
from pipeline.intake_agent import run_intake_agent
from pipeline.criteria_agent import run_criteria_agent
from pipeline.retrieval_agent import run_retrieval_agent
from pipeline.scoring_agent import run_scoring_agent
from pipeline.risk_agent import run_risk_agent
from pipeline.explanation_agent import run_explanation_agent
from pipeline.comparison_agent import run_comparison_agent
from pipeline.output_agent import run_output_agent


def build_graph():
    """Builds and compiles the LangGraph StateGraph. Falls back to a
    plain sequential runner (no LangGraph dependency) if the langgraph
    package isn't installed — same pipeline, same order, so behavior
    is identical either way."""
    try:
        from langgraph.graph import StateGraph, END

        graph = StateGraph(VendorMindState)
        graph.add_node("intake", run_intake_agent)
        graph.add_node("criteria", run_criteria_agent)
        graph.add_node("retrieval", run_retrieval_agent)
        graph.add_node("scoring", run_scoring_agent)
        graph.add_node("risk", run_risk_agent)
        graph.add_node("explanation", run_explanation_agent)
        graph.add_node("comparison", run_comparison_agent)
        graph.add_node("output", run_output_agent)

        graph.set_entry_point("intake")
        graph.add_edge("intake", "criteria")
        graph.add_edge("criteria", "retrieval")
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
    """Used only if langgraph isn't installed in the environment.
    Runs the exact same 8 functions in the exact same order."""

    _STEPS = [
        run_intake_agent,
        run_criteria_agent,
        run_retrieval_agent,
        run_scoring_agent,
        run_risk_agent,
        run_explanation_agent,
        run_comparison_agent,
        run_output_agent,
    ]

    def invoke(self, state: VendorMindState) -> VendorMindState:
        for step in self._STEPS:
            state = step(state)
        return state


_compiled_graph = None


def run_pipeline(rfp_text: str, vendors: list) -> VendorMindState:
    """Single entry point used by the API layer."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()

    initial_state: VendorMindState = {
        "rfp_text": rfp_text,
        "vendors": vendors,
        "errors": [],
    }
    result = _compiled_graph.invoke(initial_state)
    return result
