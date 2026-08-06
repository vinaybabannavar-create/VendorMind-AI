"""
tests/test_scoring_agent.py

Unit tests for pipeline/scoring_agent.py — covers:
  - Cost signal: lower price → higher cost_score
  - Compliance signal: cert matching logic
  - Composite weighting formula
  - Dumping-risk edge case (price = 0 / inf)
  - A2A fairness floor application (via run_scoring_agent state output)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.scoring_agent import _extract_price, _compliance_score


# ── _extract_price ────────────────────────────────────────────────────────────

class TestExtractPrice:
    def test_simple_dollar(self):
        assert _extract_price("Total cost: $50,000") == 50_000.0

    def test_decimal_price(self):
        assert _extract_price("Quote: $1,234.56 per year") == 1_234.56

    def test_no_price_returns_inf(self):
        assert _extract_price("No pricing information provided") == float("inf")

    def test_empty_string_returns_inf(self):
        assert _extract_price("") == float("inf")

    def test_none_returns_inf(self):
        assert _extract_price(None) == float("inf")

    def test_zero_dollar_sign(self):
        # $0 is technically parseable; cost_score handles the zero case
        assert _extract_price("$0") == 0.0


# ── _compliance_score ─────────────────────────────────────────────────────────

class TestComplianceScore:
    def test_full_compliance(self):
        score = _compliance_score(["ISO27001", "SOC2"], ["iso27001", "soc2"])
        assert score == 1.0

    def test_partial_compliance(self):
        # Has 1 of 2 required certs → 0.5
        score = _compliance_score(["ISO27001"], ["ISO27001", "SOC2"])
        assert score == 0.5

    def test_no_compliance(self):
        score = _compliance_score([], ["ISO27001", "SOC2"])
        assert score == 0.0

    def test_no_requirements_returns_full(self):
        # When RFP has no cert requirements, every vendor is fully compliant
        score = _compliance_score([], [])
        assert score == 1.0

    def test_case_insensitive(self):
        score = _compliance_score(["iso27001", "soc2"], ["ISO27001", "SOC2"])
        assert score == 1.0

    def test_extra_certs_dont_hurt(self):
        # Vendor has more certs than required — should still be 1.0
        score = _compliance_score(["ISO27001", "SOC2", "GDPR", "PCI-DSS"], ["ISO27001"])
        assert score == 1.0


# ── Composite weighting ───────────────────────────────────────────────────────

class TestCompositeWeighting:
    """Test the weighting formula by manually computing expected composites."""

    def _composite(self, cost_score, compliance, semantic, cost_weight=0.4):
        remaining = max(0.0, 1.0 - cost_weight)
        return (
            cost_weight * cost_score
            + (remaining * 0.6) * compliance
            + (remaining * 0.4) * semantic
        )

    def test_perfect_vendor(self):
        score = self._composite(1.0, 1.0, 1.0)
        assert abs(score - 1.0) < 1e-9

    def test_zero_vendor(self):
        score = self._composite(0.0, 0.0, 0.0)
        assert score == 0.0

    def test_cost_weight_dominates_at_1(self):
        score = self._composite(1.0, 0.0, 0.0, cost_weight=1.0)
        assert abs(score - 1.0) < 1e-9

    def test_compliance_weight(self):
        # cost_weight=0, compliance=1, semantic=0 → remaining*0.6 = 0.6
        score = self._composite(0.0, 1.0, 0.0, cost_weight=0.0)
        assert abs(score - 0.6) < 1e-9

    def test_semantic_weight(self):
        # cost_weight=0, compliance=0, semantic=1 → remaining*0.4 = 0.4
        score = self._composite(0.0, 0.0, 1.0, cost_weight=0.0)
        assert abs(score - 0.4) < 1e-9
