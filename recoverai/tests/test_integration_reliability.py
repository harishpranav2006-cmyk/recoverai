"""
RecoverAI — API Reliability, Security & Edge Case Integration Tests
===================================================================
Tests API error handling, Request-ID tracing, privacy rules, batch limits, and concurrency safety.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal
from backend.models import Payment
from ml.predict import predict_payment_recovery, predict_recovery_probability


class TestAPIReliabilityAndSecurity:
    """Reliability, security, and edge-case integration tests."""

    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(app)

    # -------------------------------------------------------------------------
    # 1. Request ID Middleware & Latency Tracing
    # -------------------------------------------------------------------------
    def test_request_id_propagation_and_latency(self, client: TestClient) -> None:
        custom_id = "req_custom_test_999"
        res = client.get("/api/v1/health", headers={"x-request-id": custom_id})
        assert res.status_code == 200
        assert res.headers.get("x-request-id") == custom_id
        assert "x-process-time-ms" in res.headers

    def test_server_generates_request_id_if_missing(self, client: TestClient) -> None:
        res = client.get("/api/v1/health")
        assert res.status_code == 200
        req_id = res.headers.get("x-request-id")
        assert req_id is not None
        assert req_id.startswith("req_")

    # -------------------------------------------------------------------------
    # 2. Standardized Error Envelopes
    # -------------------------------------------------------------------------
    def test_404_error_envelope_structure(self, client: TestClient) -> None:
        res = client.get("/api/v1/payments/P999999")
        assert res.status_code == 404
        data = res.json()
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
        assert "Payment with ID 'P999999' not found." in data["error"]["message"]
        assert "request_id" in data["error"]

    def test_422_validation_error_envelope(self, client: TestClient) -> None:
        # Request invalid page_size (exceeds max_page_size=100)
        res = client.get("/api/v1/payments?page_size=500")
        assert res.status_code == 422
        data = res.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "request_id" in data["error"]

    # -------------------------------------------------------------------------
    # 3. Batch Agent Processing & Upper Limit
    # -------------------------------------------------------------------------
    def test_batch_agent_execution_valid_limits(self, client: TestClient) -> None:
        # Batch of 2 payments
        res = client.post("/api/v1/agent/batch", json={"payment_ids": ["P000004", "P000005"]})
        assert res.status_code == 200
        data = res.json()
        assert data["total_requested"] == 2
        assert len(data["results"]) == 2

    def test_batch_agent_execution_exceeds_50_limit_rejected(self, client: TestClient) -> None:
        # Batch of 51 payments
        p_ids = [f"P{i:06d}" for i in range(1, 52)]
        res = client.post("/api/v1/agent/batch", json={"payment_ids": p_ids})
        assert res.status_code == 422
        data = res.json()
        assert "error" in data

    # -------------------------------------------------------------------------
    # 4. Zero Data Leakage Regression Test
    # -------------------------------------------------------------------------
    def test_ml_inference_rejects_leakage_columns(self) -> None:
        """Ensures that model prediction strictly rejects future outcome fields."""
        leakage_dict = {
            "amount": 1000.0,
            "payment_method": "card",
            "failure_reason": "network_failure",
            "recovered_after_failure": True,  # TARGET LEAKAGE
            "recovery_time_hours": 4.5,       # OUTCOME LEAKAGE
            "recovered_amount": 1000.0,       # OUTCOME LEAKAGE
        }

        with pytest.raises(ValueError, match="Data leakage detected"):
            predict_recovery_probability(leakage_dict)

    # -------------------------------------------------------------------------
    # 5. Customer Outreach Privacy
    # -------------------------------------------------------------------------
    def test_customer_outreach_privacy_rules(self, client: TestClient) -> None:
        res = client.post("/api/v1/recovery/P000004/agent?channel=whatsapp")
        assert res.status_code == 200
        data = res.json()

        outreach = data.get("customer_outreach")
        if outreach:
            content = outreach.get("content", "")
            # Ensure no internal ML values or scores leak into customer text
            assert "0." not in content, "Customer message leaked decimal score"
            assert "probability" not in content.lower(), "Customer message leaked 'probability'"
            assert "shap" not in content.lower(), "Customer message leaked 'SHAP'"
            assert "tier" not in content.lower(), "Customer message leaked 'tier'"
            assert "reason_code" not in content.lower(), "Customer message leaked 'reason_code'"

    # -------------------------------------------------------------------------
    # 6. Concurrency / Repeated Request Idempotency
    # -------------------------------------------------------------------------
    def test_repeated_workflow_requests_are_idempotent(self, client: TestClient) -> None:
        # Run workflow call 1
        res1 = client.post("/api/v1/recovery/P000004/workflow?force_fresh=true&seed=42")
        assert res1.status_code == 200
        data1 = res1.json()

        # Run workflow call 2 (idempotent cached replay)
        res2 = client.post("/api/v1/recovery/P000004/workflow?force_fresh=false&seed=42")
        assert res2.status_code == 200
        data2 = res2.json()

        assert data1["outcome"]["status"] == data2["outcome"]["status"]
