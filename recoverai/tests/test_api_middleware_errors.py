"""
Tests for Request ID Middleware and Standardized Error Envelopes
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_request_id_generated_and_returned():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert "x-request-id" in res.headers
    assert res.headers["x-request-id"].startswith("req_")


def test_custom_request_id_propagated():
    custom_id = "test-req-custom-999"
    res = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert res.status_code == 200
    assert res.headers["x-request-id"] == custom_id


def test_standardized_error_format_on_404():
    res = client.get("/api/v1/customers/NON_EXISTENT_CUSTOMER_XYZ")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "message" in data["error"]
    assert "request_id" in data["error"]


def test_standardized_error_format_on_validation_error():
    res = client.get("/api/v1/customers?page_size=999")  # max is 100
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in data["error"]
