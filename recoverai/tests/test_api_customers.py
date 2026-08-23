"""
Tests for RecoverAI Customer API Endpoints
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_list_customers_paginated():
    res = client.get("/api/v1/customers?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total"] == 5000
    assert len(data["items"]) == 10
    assert data["total_pages"] == 500


def test_list_customers_filtering():
    res = client.get("/api/v1/customers?segment=enterprise&page_size=5")
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["segment"] == "enterprise"


def test_get_customer_details_success():
    res = client.get("/api/v1/customers/C00001")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "C00001"
    assert "lifetime_value" in data
    assert "total_transactions" in data
    assert "successful_payments" in data
    assert "failed_payments" in data


def test_get_customer_details_not_found():
    res = client.get("/api/v1/customers/NON_EXISTENT_ID")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_get_customer_history():
    res = client.get("/api/v1/customers/C00001/history")
    assert res.status_code == 200
    data = res.json()
    assert data["customer_id"] == "C00001"
    assert "payments" in data
    assert isinstance(data["payments"], list)
