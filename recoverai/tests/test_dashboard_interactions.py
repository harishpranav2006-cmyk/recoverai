"""
RecoverAI — Dashboard Interaction & Workflow Integration Tests
==============================================================
Validates the operational workflows triggered from the interactive dashboard pages.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestDashboardInteractiveWorkflows:
    """Validates operational actions triggered by interactive buttons in the dashboard."""

    def test_overview_demo_batch_execution(self, client: TestClient) -> None:
        """Tests the 'Execute Selected Scenario (ALL_7_SCENARIOS)' button workflow."""
        resp = client.post("/api/v1/simulation/demo", params={"seed": 42})
        assert resp.status_code == 200
        data = resp.json()
        assert data["simulated"] is True
        assert data["scenarios_executed"] == 7
        assert len(data["results"]) == 7

        # Verify each scenario has required reporting fields
        for sc in data["results"]:
            assert "payment_id" in sc
            assert "probability" in sc
            assert "strategy" in sc
            assert "outcome_status" in sc
            assert "recovered_amount" in sc

    def test_recovery_workstation_analyze_action(self, client: TestClient) -> None:
        """Tests the '[ 🧠 Analyze Payment ]' button workflow in Recovery Queue."""
        resp = client.post("/api/v1/recovery/P000004/analyze")
        assert resp.status_code == 200
        data = resp.json()
        assert data["payment_id"] == "P000004"
        assert data["tier"] == "HIGH_CONFIDENCE"
        assert data["strategy"] == "SMART_RETRY"
        assert "reason_codes" in data

    def test_recovery_workstation_agent_action(self, client: TestClient) -> None:
        """Tests the '[ 🤖 Run AI Agent ]' button workflow in Recovery Queue."""
        resp = client.post("/api/v1/recovery/P000004/agent", params={"channel": "whatsapp"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["payment_id"] == "P000004"
        assert "tools_invoked" in data or "execution_steps" in data

    def test_recovery_workstation_simulate_gateway_action(self, client: TestClient) -> None:
        """Tests the '[ ⚡ Simulate Gateway ]' button workflow in Recovery Queue."""
        resp = client.post("/api/v1/simulation/payment/P000004", params={"force_fresh": True, "seed": 42})
        assert resp.status_code == 200
        data = resp.json()
        assert data["payment_id"] == "P000004"
        assert "gateway_response" in data
        assert "code" in data["gateway_response"]

    def test_recovery_workstation_full_workflow_execution(self, client: TestClient) -> None:
        """Tests the '[ 🚀 Confirm & Run Recovery Workflow ]' button workflow."""
        resp = client.post(
            "/api/v1/recovery/P000004/workflow",
            params={"channel": "whatsapp", "force_fresh": True, "seed": 42},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["payment_id"] == "P000004"
        assert "outcome" in data or "simulated_outcome" in data

    def test_ai_decisions_re_evaluate_action(self, client: TestClient) -> None:
        """Tests the '[ 🔄 Re-Evaluate Decision Engine ]' button workflow in AI Decisions."""
        resp = client.post("/api/v1/recovery/P000001/analyze")
        assert resp.status_code == 200
        data = resp.json()
        assert data["payment_id"] == "P000001"
        assert "strategy" in data
        assert "reason_codes" in data
