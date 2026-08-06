"""
tests/test_risk_agent.py

Unit tests for pipeline/risk_agent.py — covers:
  - Missing compliance documentation flag
  - Dumping risk flag (unusually low bid relative to median price)
  - A2A Protocol handshake & EEOC Adverse Impact Ratio vetting
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.risk_agent import run_risk_agent
from pipeline.a2a_protocol import scoring_to_risk_handshake


class TestRiskAgentFlags:
    def test_missing_certifications_flag(self):
        state = {
            "parsed_vendors": [
                {
                    "vendor_id": "v1",
                    "vendor_name": "Vendor A",
                    "extracted": {"certifications_mentioned": ["ISO27001"], "price_mentioned": "$50,000"},
                }
            ],
            "criteria": {"compliance_requirements": ["ISO27001", "SOC2"]},
            "scores": {"v1": {"composite": 0.8}},
        }
        res = run_risk_agent(state)
        flags = res.get("risk_flags", {}).get("v1", [])
        assert any("SOC2" in f for f in flags)

    def test_dumping_risk_flag(self):
        state = {
            "parsed_vendors": [
                {"vendor_id": "v1", "extracted": {"price_mentioned": "$100,000"}},
                {"vendor_id": "v2", "extracted": {"price_mentioned": "$105,000"}},
                {"vendor_id": "v3", "extracted": {"price_mentioned": "$15,000"}},  # 15% of median (100k) -> dumping risk
            ],
            "criteria": {},
            "scores": {},
        }
        res = run_risk_agent(state)
        v3_flags = res.get("risk_flags", {}).get("v3", [])
        assert any("dumping risk" in f.lower() for f in v3_flags)


class TestA2AProtocolHandshake:
    def test_scoring_to_risk_handshake_returns_audited_scores(self):
        draft_scores = {"v1": {"composite_score": 0.85, "cost": 0.9, "compliance": 0.8, "semantic": 0.8}}
        state = {"parsed_vendors": [{"vendor_id": "v1", "vendor_name": "Vendor A"}], "a2a_log": []}

        final_scores = scoring_to_risk_handshake(
            state=state,
            draft_scores=draft_scores,
        )

        assert "v1" in final_scores
        assert len(state["a2a_log"]) >= 2
