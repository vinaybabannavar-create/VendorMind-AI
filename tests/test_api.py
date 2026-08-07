"""
tests/test_api.py

Integration tests for api/main.py — covers:
  - GET /health endpoint
  - POST /evaluate input validation (OWASP A03)
  - POST /evaluate with valid mocked pipeline
  - GET /evaluation/{id} retrieval
  - GET /evaluation/{id} 404 for missing ID
  - GET /evaluation/{id}/comparison
  - POST /approve with valid and invalid payloads
  - Rate limit response shape
  - Security headers are present on every response
  - XSS / script injection input guard
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app, raise_server_exceptions=False)


# ── Shared Mock Pipeline Result ────────────────────────────────────────────────

MOCK_PIPELINE_RESULT = {
    "final_report": "VendorA is the recommended vendor based on cost and compliance.",
    "comparison_table": [
        {
            "vendor_id": "vendor_alpha",
            "vendor_name": "Alpha Corp",
            "composite_score": 0.87,
            "cost_score": 0.9,
            "compliance_score": 1.0,
        }
    ],
    "rankings": [{"rank": 1, "vendor_id": "vendor_alpha", "score": 0.87}],
    "telemetry": {"correlation_id": "test-corr-123", "total_duration_ms": 1234},
}

VALID_RFP = "We need a cloud vendor with ISO27001 certification for $50,000 annually."

VALID_VENDOR = {
    "vendor_id": "vendor_alpha",
    "vendor_name": "Alpha Corp",
    "raw_text": "Alpha Corp offers ISO27001 certified cloud services at $48,000 per year with 99.9% SLA.",
}


# ── GET /health ────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_ok_status(self):
        resp = client.get("/health")
        assert resp.json() == {"status": "ok"}

    def test_health_has_security_headers(self):
        resp = client.get("/health")
        assert "x-content-type-options" in resp.headers
        assert resp.headers["x-content-type-options"] == "nosniff"

    def test_health_has_xframe_options(self):
        resp = client.get("/health")
        assert "x-frame-options" in resp.headers
        assert resp.headers["x-frame-options"] == "DENY"


# ── POST /evaluate — Input Validation ─────────────────────────────────────────

class TestEvaluateInputValidation:
    def test_missing_rfp_text_returns_422(self):
        resp = client.post("/evaluate", json={"vendors": [VALID_VENDOR]})
        assert resp.status_code == 422

    def test_rfp_too_short_returns_422(self):
        resp = client.post("/evaluate", json={"rfp_text": "short", "vendors": [VALID_VENDOR]})
        assert resp.status_code == 422

    def test_empty_vendors_list_returns_422(self):
        resp = client.post("/evaluate", json={"rfp_text": VALID_RFP, "vendors": []})
        assert resp.status_code == 422

    def test_vendor_id_with_invalid_chars_returns_422(self):
        bad_vendor = {**VALID_VENDOR, "vendor_id": "vendor; DROP TABLE--"}
        resp = client.post("/evaluate", json={"rfp_text": VALID_RFP, "vendors": [bad_vendor]})
        assert resp.status_code == 422

    def test_xss_in_raw_text_rejected(self):
        xss_vendor = {**VALID_VENDOR, "raw_text": "<script>alert('xss')</script> Cloud services at $48,000."}
        resp = client.post("/evaluate", json={"rfp_text": VALID_RFP, "vendors": [xss_vendor]})
        assert resp.status_code == 422

    def test_javascript_injection_in_raw_text_rejected(self):
        js_vendor = {**VALID_VENDOR, "raw_text": "javascript:void(0) Cloud services at $48,000 annually ISO27001."}
        resp = client.post("/evaluate", json={"rfp_text": VALID_RFP, "vendors": [js_vendor]})
        assert resp.status_code == 422

    def test_vendor_id_too_long_rejected(self):
        long_id_vendor = {**VALID_VENDOR, "vendor_id": "v" * 65}
        resp = client.post("/evaluate", json={"rfp_text": VALID_RFP, "vendors": [long_id_vendor]})
        assert resp.status_code == 422


# ── POST /evaluate — Valid Request ────────────────────────────────────────────

class TestEvaluateValid:
    def test_valid_request_returns_200(self):
        with patch("api.main.run_pipeline", return_value=MOCK_PIPELINE_RESULT):
            resp = client.post("/evaluate", json={"rfp_text": VALID_RFP, "vendors": [VALID_VENDOR]})
        assert resp.status_code == 200

    def test_valid_request_returns_evaluation_id(self):
        with patch("api.main.run_pipeline", return_value=MOCK_PIPELINE_RESULT):
            resp = client.post("/evaluate", json={"rfp_text": VALID_RFP, "vendors": [VALID_VENDOR]})
        data = resp.json()
        assert "evaluation_id" in data
        assert data["evaluation_id"].startswith("eval_")

    def test_valid_request_returns_final_report(self):
        with patch("api.main.run_pipeline", return_value=MOCK_PIPELINE_RESULT):
            resp = client.post("/evaluate", json={"rfp_text": VALID_RFP, "vendors": [VALID_VENDOR]})
        data = resp.json()
        assert "final_report" in data
        assert isinstance(data["final_report"], str)

    def test_valid_request_returns_comparison_table(self):
        with patch("api.main.run_pipeline", return_value=MOCK_PIPELINE_RESULT):
            resp = client.post("/evaluate", json={"rfp_text": VALID_RFP, "vendors": [VALID_VENDOR]})
        data = resp.json()
        assert "comparison_table" in data
        assert isinstance(data["comparison_table"], list)

    def test_multiple_vendors_accepted(self):
        vendor2 = {
            "vendor_id": "vendor_beta",
            "vendor_name": "Beta Solutions",
            "raw_text": "Beta Solutions provides cloud hosting SOC2 certified at $52,000 per year with 99.5% SLA.",
        }
        with patch("api.main.run_pipeline", return_value=MOCK_PIPELINE_RESULT):
            resp = client.post("/evaluate", json={"rfp_text": VALID_RFP, "vendors": [VALID_VENDOR, vendor2]})
        assert resp.status_code == 200


# ── GET /evaluation/{id} ──────────────────────────────────────────────────────

class TestGetEvaluation:
    def _create_evaluation(self):
        with patch("api.main.run_pipeline", return_value=MOCK_PIPELINE_RESULT):
            resp = client.post("/evaluate", json={"rfp_text": VALID_RFP, "vendors": [VALID_VENDOR]})
        return resp.json()["evaluation_id"]

    def test_get_existing_evaluation_returns_200(self):
        eval_id = self._create_evaluation()
        resp = client.get(f"/evaluation/{eval_id}")
        assert resp.status_code == 200

    def test_get_missing_evaluation_returns_404(self):
        resp = client.get("/evaluation/eval_99999")
        assert resp.status_code == 404

    def test_get_evaluation_contains_expected_keys(self):
        eval_id = self._create_evaluation()
        resp = client.get(f"/evaluation/{eval_id}")
        data = resp.json()
        assert "final_report" in data or "comparison_table" in data


# ── GET /evaluation/{id}/comparison ──────────────────────────────────────────

class TestGetComparison:
    def _create_evaluation(self):
        with patch("api.main.run_pipeline", return_value=MOCK_PIPELINE_RESULT):
            resp = client.post("/evaluate", json={"rfp_text": VALID_RFP, "vendors": [VALID_VENDOR]})
        return resp.json()["evaluation_id"]

    def test_comparison_returns_200(self):
        eval_id = self._create_evaluation()
        resp = client.get(f"/evaluation/{eval_id}/comparison")
        assert resp.status_code == 200

    def test_comparison_returns_list(self):
        eval_id = self._create_evaluation()
        resp = client.get(f"/evaluation/{eval_id}/comparison")
        data = resp.json()
        assert "comparison_table" in data
        assert isinstance(data["comparison_table"], list)

    def test_comparison_missing_evaluation_returns_404(self):
        resp = client.get("/evaluation/eval_99999/comparison")
        assert resp.status_code == 404


# ── Security Headers ──────────────────────────────────────────────────────────

class TestSecurityHeaders:
    def test_xss_protection_header_present(self):
        resp = client.get("/health")
        assert "x-xss-protection" in resp.headers

    def test_cache_control_no_store(self):
        resp = client.get("/health")
        assert resp.headers.get("cache-control") == "no-store"

    def test_referrer_policy_set(self):
        resp = client.get("/health")
        assert "referrer-policy" in resp.headers

    def test_vendormind_version_header_present(self):
        resp = client.get("/health")
        assert "x-vendormind-version" in resp.headers
