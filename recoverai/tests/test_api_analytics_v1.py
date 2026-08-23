"""
Tests for RecoverAI Analytics v1 API Endpoints
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_v1_analytics_overview():
    res = client.get("/api/v1/analytics/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_customers"] == 5000
    assert data["total_payments"] == 50000
    assert data["total_failed_payments"] == 13272
    assert "failed_payment_value" in data
    assert "recovered_value" in data
    assert "recovery_rate" in data


def test_v1_analytics_by_strategy():
    res = client.get("/api/v1/analytics/by-strategy")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    strategies = [item["strategy"] for item in data]
    assert "SMART_RETRY" in strategies


def test_v1_analytics_by_failure():
    res = client.get("/api/v1/analytics/by-failure")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 5


def test_v1_analytics_by_segment():
    res = client.get("/api/v1/analytics/by-segment")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    segments = [item["segment"] for item in data]
    assert "enterprise" in segments
    assert "premium" in segments


def test_v1_analytics_trends():
    res = client.get("/api/v1/analytics/trends?interval=daily")
    assert res.status_code == 200
    data = res.json()
    assert data["interval"] == "daily"
    assert "points" in data
    assert isinstance(data["points"], list)
    assert len(data["points"]) > 0
