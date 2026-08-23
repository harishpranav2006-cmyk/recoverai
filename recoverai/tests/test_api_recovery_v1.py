"""
Tests for RecoverAI Recovery v1 API Endpoints
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_v1_analyze_payment():
    res = client.post("/api/v1/recovery/P000004/analyze")
    assert res.status_code == 200
    data = res.json()
    assert data["payment_id"] == "P000004"
    assert "recovery_probability" in data
    assert "tier" in data
    assert "strategy" in data
    assert "recommended_action" in data


def test_v1_run_agent():
    res = client.post("/api/v1/recovery/P000004/agent")
    assert res.status_code == 200
    data = res.json()
    assert data["payment_id"] == "P000004"
    assert "strategy" in data
    assert "recovery_probability" in data


def test_v1_workflow():
    res = client.post("/api/v1/recovery/P000004/workflow?force_fresh=true&seed=42")
    assert res.status_code == 200
    data = res.json()
    assert data["payment_id"] == "P000004"
    assert "decision" in data
    assert "action" in data
    assert "outcome" in data
    assert "revenue_impact" in data


def test_v1_recovery_queue():
    res = client.get("/api/v1/recovery/queue?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) <= 10
    if data["items"]:
        item = data["items"][0]
        assert "priority_score" in item
        assert "recovery_probability" in item
        assert "strategy" in item


def test_v1_get_decision():
    res = client.get("/api/v1/recovery/P000004/decision")
    assert res.status_code == 200
    data = res.json()
    assert data["payment_id"] == "P000004"
    assert "tier" in data


def test_v1_get_history():
    res = client.get("/api/v1/recovery/P000004/history")
    assert res.status_code == 200
    data = res.json()
    assert data["payment_id"] == "P000004"
    assert "predictions" in data
    assert "decisions" in data
