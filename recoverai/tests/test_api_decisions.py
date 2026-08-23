"""
Tests for RecoverAI Decision History API Endpoints
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_list_decisions_paginated():
    res = client.get("/api/v1/decisions?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert "total" in data
    assert "items" in data


def test_list_decisions_filtered():
    res = client.get("/api/v1/decisions?tier=HIGH_CONFIDENCE&page_size=5")
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["tier"] == "HIGH_CONFIDENCE"
