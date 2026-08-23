"""
Tests for RecoverAI Agent API Endpoints
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_agent_run_single():
    res = client.post("/api/v1/agent/run", json={"payment_id": "P000004"})
    assert res.status_code == 200
    data = res.json()
    assert data["payment_id"] == "P000004"
    assert "strategy" in data
    assert "recovery_probability" in data


def test_agent_batch_run_success():
    res = client.post("/api/v1/agent/batch", json={"payment_ids": ["P000004", "P000005"]})
    assert res.status_code == 200
    data = res.json()
    assert data["total_requested"] == 2
    assert data["successful_count"] == 2
    assert len(data["results"]) == 2


def test_agent_batch_exceeds_limit():
    too_many = [f"P{i:06d}" for i in range(55)]
    res = client.post("/api/v1/agent/batch", json={"payment_ids": too_many})
    assert res.status_code == 422  # pydantic schema validation max_length=50
