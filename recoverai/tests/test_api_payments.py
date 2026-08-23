"""
Tests for RecoverAI Payment API Endpoints
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_list_payments_paginated():
    res = client.get("/api/v1/payments?page=1&page_size=15")
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 15
    assert data["total"] == 50000
    assert len(data["items"]) == 15


def test_list_payments_filter_failed():
    res = client.get("/api/v1/payments?status=failed&page_size=10")
    assert res.status_code == 200
    data = res.json()
    for p in data["items"]:
        assert p["payment_success"] is False


def test_get_payment_details_success():
    res = client.get("/api/v1/payments/P000001")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "P000001"
    assert "amount" in data
    assert "payment_method" in data
    assert "customer_lifetime_value" in data


def test_get_payment_details_not_found():
    res = client.get("/api/v1/payments/INVALID_PID")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_get_payment_timeline():
    res = client.get("/api/v1/payments/P000004/timeline")
    assert res.status_code == 200
    data = res.json()
    assert data["payment_id"] == "P000004"
    assert "events" in data
    assert len(data["events"]) >= 1
    assert "event_type" in data["events"][0]
