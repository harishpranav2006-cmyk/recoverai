"""
Tests for RecoverAI ML Prediction API Endpoints
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_ml_predict_endpoint():
    res = client.post("/api/v1/ml/predict/P000004")
    assert res.status_code == 200
    data = res.json()
    assert data["payment_id"] == "P000004"
    assert 0.0 <= data["recovery_probability"] <= 1.0
    assert data["prediction"] in [0, 1]
    assert data["calibrated"] is True
    assert isinstance(data["factors"], list)


def test_ml_status_endpoint():
    res = client.get("/api/v1/ml/status")
    assert res.status_code == 200
    data = res.json()
    assert data["model_loaded"] is True
    assert data["feature_count"] > 0
    assert len(data["features"]) > 0
