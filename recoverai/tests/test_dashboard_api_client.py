"""
RecoverAI — Dashboard API Client Tests
======================================
Validates that the Dashboard APIClient interacts with the FastAPI backend without errors.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
import requests

from dashboard.api_client import APIClient


class TestDashboardAPIClient:
    """Tests for the dashboard APIClient methods."""

    @pytest.fixture
    def client(self) -> APIClient:
        return APIClient(base_url="http://testserver/api/v1")

    @patch("requests.Session.request")
    def test_get_health(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.return_value.status_code = 200
        mock_req.return_value.json.return_value = {"status": "healthy"}

        data, err = client.get_health()
        assert err is None
        assert data == {"status": "healthy"}
        mock_req.assert_called_once_with(
            method="GET",
            url="http://testserver/api/v1/health",
            params=None,
            json=None,
            timeout=15,
            headers={"Accept": "application/json"},
        )

    @patch("requests.Session.request")
    def test_get_overview(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.return_value.status_code = 200
        mock_req.return_value.json.return_value = {"total_payments": 50000, "recovery_rate": 0.57}

        data, err = client.get_overview()
        assert err is None
        assert data["total_payments"] == 50000

    @patch("requests.Session.request")
    def test_get_recovery_queue(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.return_value.status_code = 200
        mock_req.return_value.json.return_value = [{"payment_id": "P000004", "recovery_probability": 0.72}]

        data, err = client.get_recovery_queue(tier="HIGH_CONFIDENCE", limit=10)
        assert err is None
        assert len(data) == 1
        assert data[0]["payment_id"] == "P000004"

    @patch("requests.Session.request")
    def test_predict_payment(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.return_value.status_code = 200
        mock_req.return_value.json.return_value = {"payment_id": "P000004", "recovery_probability": 0.75}

        data, err = client.predict_payment("P000004")
        assert err is None
        assert data["recovery_probability"] == 0.75

    @patch("requests.Session.request")
    def test_analyze_recovery(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.return_value.status_code = 200
        mock_req.return_value.json.return_value = {
            "payment_id": "P000004",
            "tier": "HIGH_CONFIDENCE",
            "strategy": "SMART_RETRY",
        }

        data, err = client.analyze_recovery("P000004")
        assert err is None
        assert data["strategy"] == "SMART_RETRY"

    @patch("requests.Session.request")
    def test_run_agent(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.return_value.status_code = 200
        mock_req.return_value.json.return_value = {
            "payment_id": "P000004",
            "decision": {"strategy": "SMART_RETRY"},
        }

        data, err = client.run_agent("P000004", channel="whatsapp")
        assert err is None
        assert data["decision"]["strategy"] == "SMART_RETRY"

    @patch("requests.Session.request")
    def test_simulate_payment(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.return_value.status_code = 200
        mock_req.return_value.json.return_value = {
            "payment_id": "P000004",
            "gateway_response_code": "SUCCESS",
            "outcome_status": "RECOVERED",
        }

        data, err = client.simulate_payment("P000004", force_fresh=True)
        assert err is None
        assert data["outcome_status"] == "RECOVERED"

    @patch("requests.Session.request")
    def test_simulate_demo(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.return_value.status_code = 200
        mock_req.return_value.json.return_value = {
            "total_scenarios": 7,
            "scenarios": [{"scenario_name": "HIGH_RECOVERY_CASE", "outcome_status": "RECOVERED"}],
        }

        data, err = client.simulate_demo(seed=42)
        assert err is None
        assert data["total_scenarios"] == 7

    @patch("requests.Session.request")
    def test_get_customers_and_history(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.return_value.status_code = 200
        mock_req.return_value.json.return_value = {
            "items": [{"id": "C00001", "segment": "enterprise"}],
            "total": 1,
        }

        data, err = client.get_customers(search="C00001")
        assert err is None
        assert len(data["items"]) == 1

        mock_req.return_value.json.return_value = {"customer_id": "C00001", "payments": []}
        hist, hist_err = client.get_customer_history("C00001")
        assert hist_err is None
        assert hist["customer_id"] == "C00001"

    @patch("requests.Session.request")
    def test_get_decisions_and_trends(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.return_value.status_code = 200
        mock_req.return_value.json.return_value = {"items": [{"id": 1, "payment_id": "P000004"}], "total": 1}

        data, err = client.get_decisions(payment_id="P000004")
        assert err is None
        assert len(data["items"]) == 1

        mock_req.return_value.json.return_value = {"interval": "monthly", "points": []}
        trends, trends_err = client.get_trends(interval="monthly")
        assert trends_err is None
        assert trends["interval"] == "monthly"

    @patch("requests.Session.request")
    def test_run_workflow(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.return_value.status_code = 200
        mock_req.return_value.json.return_value = {
            "payment_id": "P000004",
            "simulated_outcome": {"outcome_status": "RECOVERED", "recovered_amount": 1200.0},
        }

        data, err = client.run_workflow("P000004", channel="whatsapp", force_fresh=True)
        assert err is None
        assert data["simulated_outcome"]["outcome_status"] == "RECOVERED"

    @patch("requests.Session.request")
    def test_error_handling_on_404(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.return_value.status_code = 404
        mock_req.return_value.json.return_value = {"error": {"message": "Payment not found."}}

        data, err = client.get_payment("P999999")
        assert data is None
        assert "Payment not found." in err

    @patch("requests.Session.request")
    def test_error_handling_on_500(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.return_value.status_code = 500
        mock_req.return_value.json.return_value = {"error": {"message": "Internal database lock error."}}

        data, err = client.get_payment("P000001")
        assert data is None
        assert "Internal database lock error." in err

    @patch("requests.Session.request")
    def test_connection_error_handling(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.side_effect = requests.exceptions.ConnectionError("Connection refused")

        data, err = client.get_health()
        assert data is None
        assert "Backend API unavailable" in err

    @patch("requests.Session.request")
    def test_timeout_error_handling(self, mock_req: MagicMock, client: APIClient) -> None:
        mock_req.side_effect = requests.exceptions.Timeout("Request timeout")

        data, err = client.get_overview()
        assert data is None
        assert "timed out" in err
