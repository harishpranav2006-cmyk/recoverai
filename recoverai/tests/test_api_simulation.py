"""
Tests for RecoverAI Simulation API Endpoints
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_simulate_payment_retry():
    res = client.post("/api/v1/simulation/payment/P000004?force_fresh=true&seed=42")
    assert res.status_code == 200
    data = res.json()
    assert data["simulated"] is True
    assert data["payment_id"] == "P000004"
    assert "gateway_response" in data


def test_simulate_workflow():
    res = client.post("/api/v1/simulation/workflow/P000004?force_fresh=true&seed=42")
    assert res.status_code == 200
    data = res.json()
    assert data["simulated"] is True
    assert "decision" in data
    assert "outcome" in data


def test_simulate_demo_scenarios():
    res = client.post("/api/v1/simulation/demo?seed=42")
    assert res.status_code == 200
    data = res.json()
    assert data["simulated"] is True
    assert data["status"] == "completed"
    assert data["scenarios_executed"] == 7
    assert len(data["results"]) == 7
