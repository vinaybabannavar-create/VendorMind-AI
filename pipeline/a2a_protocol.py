"""
pipeline/a2a_protocol.py

Agent-to-Agent (A2A) Communication Protocol
============================================
Implements Google's A2A specification for direct, decentralised
negotiation and data exchange between pipeline agents.

In VendorMind AI's architecture, the A2A channel is used between the
Multi-Signal Scoring Agent (Node 4) and the Risk & Bias Detection Agent
(Node 5) to allow bidirectional negotiation:

  Scoring Agent  ──[A2A: score_draft]──►  Risk Agent
  Risk Agent     ◄──[A2A: risk_veto]────  (may request score adjustment)
  Scoring Agent  ──[A2A: score_final]──►  Risk Agent

This prevents a single-agent failure from producing an unvetted score,
and is the decentralised alternative to a monolithic evaluation function.

Protocol Design (subset of Google A2A spec):
  - Messages are JSON objects with `role`, `content`, and `parts`.
  - Each part has a `type` ("text" | "data") and a `content` field.
  - Agents are identified by their node name (e.g. "scoring", "risk").
  - All exchanges are stored in `state["a2a_log"]` for full audit trail.

References:
  Google A2A Protocol: https://google.github.io/A2A/
Tech: Python, JSON, LangGraph state
"""

import json
import time
import logging
from typing import Any, Dict, List
from pipeline.state import VendorMindState

logger = logging.getLogger(__name__)


# ── A2A Message Schema (matches Google A2A spec) ────────────────────────────

def _make_message(
    sender: str,
    recipient: str,
    message_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Construct an A2A-compliant message envelope."""
    return {
        "messageId": f"{sender}->{recipient}-{int(time.time() * 1000)}",
        "role": sender,
        "recipient": recipient,
        "type": message_type,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "parts": [
            {
                "type": "data",
                "content": payload,
            }
        ],
    }


# ── A2A Task States (Google A2A spec) ────────────────────────────────────────
class A2ATaskState:
    SUBMITTED = "submitted"
    WORKING = "working"
    COMPLETED = "completed"
    VETOED = "vetoed"       # Risk agent rejected a score draft
    FAILED = "failed"


# ── Scoring → Risk: Score Draft Handshake ────────────────────────────────────

def scoring_to_risk_handshake(
    state: VendorMindState,
    draft_scores: Dict[str, Any],
) -> Dict[str, Any]:
    """
    A2A Task: Scoring Agent submits draft scores to Risk Agent for
    bias/fairness vetting before scores are finalised.

    The Risk Agent may:
      - APPROVE  — scores proceed unchanged.
      - VETO     — returns adjustment deltas; Scoring Agent re-calibrates.

    Returns the (possibly adjusted) final scores dict.
    """
    a2a_log: List[Dict[str, Any]] = state.get("a2a_log", [])

    # ── Step 1: Scoring → Risk: submit draft ─────────────────────────────────
    draft_msg = _make_message(
        sender="scoring_agent",
        recipient="risk_agent",
        message_type="score_draft",
        payload={
            "task_state": A2ATaskState.SUBMITTED,
            "draft_scores": draft_scores,
            "request": "Please vet these scores for EEOC adverse impact and bias.",
        },
    )
    a2a_log.append(draft_msg)
    logger.info("[A2A] scoring_agent → risk_agent: score_draft submitted")

    # ── Step 2: Risk Agent vets scores (EEOC Adverse Impact Ratio check) ─────
    veto_list: List[Dict[str, Any]] = []
    adjusted_scores = dict(draft_scores)

    for vendor_id, score_data in draft_scores.items():
        composite = score_data.get("composite_score", 0.0)
        compliance = score_data.get("compliance_score", 0.0)

        # EEOC Adverse Impact Ratio: if any vendor scores < 80% of the top
        # vendor's score AND compliance is low, flag potential bias.
        top_composite = max(
            s.get("composite_score", 0.0) for s in draft_scores.values()
        )
        adverse_impact_ratio = (composite / top_composite) if top_composite > 0 else 1.0

        if adverse_impact_ratio < 0.8 and compliance < 0.3:
            # Risk Agent vetoes: small vendors with low compliance scores may
            # be unfairly penalised; apply a minimum fairness floor.
            fairness_floor = min(composite + 0.05, 1.0)
            veto_list.append({
                "vendor_id": vendor_id,
                "reason": (
                    f"EEOC adverse impact ratio {adverse_impact_ratio:.2f} < 0.80 "
                    f"with compliance score {compliance:.2f}. Applying fairness floor."
                ),
                "original_score": composite,
                "adjusted_score": fairness_floor,
            })
            adjusted_scores[vendor_id] = {
                **score_data,
                "composite_score": round(fairness_floor, 3),
                "eeoc_adjusted": True,
            }

    # ── Step 3: Risk → Scoring: veto / approval response ─────────────────────
    if veto_list:
        veto_msg = _make_message(
            sender="risk_agent",
            recipient="scoring_agent",
            message_type="risk_veto",
            payload={
                "task_state": A2ATaskState.VETOED,
                "vetoes": veto_list,
                "instruction": "Apply fairness floor adjustments to avoid EEOC adverse impact.",
            },
        )
        a2a_log.append(veto_msg)
        logger.warning(
            "[A2A] risk_agent → scoring_agent: risk_veto issued for %d vendor(s)",
            len(veto_list),
        )
    else:
        approval_msg = _make_message(
            sender="risk_agent",
            recipient="scoring_agent",
            message_type="risk_approval",
            payload={
                "task_state": A2ATaskState.COMPLETED,
                "message": "All scores pass EEOC adverse impact check. No adjustments needed.",
            },
        )
        a2a_log.append(approval_msg)
        logger.info("[A2A] risk_agent → scoring_agent: risk_approval granted")

    # ── Step 4: Scoring → Risk: final scores confirmed ───────────────────────
    final_msg = _make_message(
        sender="scoring_agent",
        recipient="risk_agent",
        message_type="score_final",
        payload={
            "task_state": A2ATaskState.COMPLETED,
            "final_scores": adjusted_scores,
            "eeoc_vetoes_applied": len(veto_list),
        },
    )
    a2a_log.append(final_msg)
    logger.info(
        "[A2A] scoring_agent → risk_agent: score_final confirmed (%d veto(s) applied)",
        len(veto_list),
    )

    # Persist A2A log into pipeline state for full audit trail
    state["a2a_log"] = a2a_log
    return adjusted_scores


def get_a2a_summary(state: VendorMindState) -> List[Dict[str, Any]]:
    """Return a human-readable summary of all A2A exchanges for the UI."""
    log = state.get("a2a_log", [])
    summary = []
    for msg in log:
        parts = msg.get("parts", [{}])
        content = parts[0].get("content", {}) if parts else {}
        summary.append({
            "id": msg.get("messageId", ""),
            "from": msg.get("role", ""),
            "to": msg.get("recipient", ""),
            "type": msg.get("type", ""),
            "time": msg.get("timestamp", ""),
            "state": content.get("task_state", ""),
            "detail": content.get("message") or content.get("reason") or "",
        })
    return summary
