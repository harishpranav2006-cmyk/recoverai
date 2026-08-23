"""
Tests for RecoverAI Health & Readiness API Endpoints
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_v1_health_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["database"] == "connected"
    assert data["ml_model"] == "available"
    assert data["simulator"] == "available"
    assert "version" in data


def test_v1_liveness_probe():
    res = client.get("/api/v1/health/live")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "alive"
    assert data["alive"] is True


def test_v1_readiness_probe():
    res = client.get("/api/v1/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["ready"] is True
    assert data["database_connected"] is True
    assert data["ml_model_loaded"] is True


def test_legacy_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["app"] == "RecoverAI"
