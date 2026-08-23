"""
RecoverAI — API Endpoints Test Suite
====================================
Tests FastAPI routes:
- GET /health
- POST /recovery/analyze
- POST /recovery/agent/run
- GET /recovery/{payment_id}/decision
- GET /recovery/{payment_id}/history
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.main import app
from backend.database import SessionLocal
from backend.models.payment import Payment

client = TestClient(app)


@pytest.fixture
def test_payment_id() -> str:
    db = SessionLocal()
    try:
        p = (
            db.query(Payment)
            .filter(Payment.payment_success == False, Payment.retry_count == 0)
            .first()
        )
        assert p is not None
        return p.id
    finally:
        db.close()


class TestRecoveryAPI:
    """Verifies all FastAPI recovery routes."""

    def test_health_check(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app"] == "RecoverAI"

    def test_post_recovery_analyze_valid(self, test_payment_id: str) -> None:
        response = client.post("/recovery/analyze", json={"payment_id": test_payment_id})
        assert response.status_code == 200
        data = response.json()
        assert data["payment_id"] == test_payment_id
        assert "recovery_probability" in data
        assert "tier" in data
        assert "strategy" in data
        assert "recommended_action" in data
        assert "reason_codes" in data

    def test_post_recovery_analyze_not_found(self) -> None:
        response = client.post("/recovery/analyze", json={"payment_id": "P_INVALID_999999"})
        assert response.status_code == 404

    def test_post_recovery_agent_run_valid(self, test_payment_id: str) -> None:
        response = client.post(
            "/recovery/agent/run",
            json={"payment_id": test_payment_id, "channel": "WHATSAPP"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment_id"] == test_payment_id
        assert "execution_steps" in data
        assert "model_version" in data
        assert "explanation" in data

    def test_get_recovery_decision_and_history(self, test_payment_id: str) -> None:
        # First run agent to ensure decision is in DB
        client.post("/recovery/agent/run", json={"payment_id": test_payment_id})

        # Test GET /recovery/{payment_id}/decision
        dec_resp = client.get(f"/recovery/{test_payment_id}/decision")
        assert dec_resp.status_code == 200
        dec_data = dec_resp.json()
        assert dec_data["payment_id"] == test_payment_id
        assert "recommended_action" in dec_data
        assert "recovery_probability" in dec_data

        # Test GET /recovery/{payment_id}/history
        hist_resp = client.get(f"/recovery/{test_payment_id}/history")
        assert hist_resp.status_code == 200
        hist_data = hist_resp.json()
        assert hist_data["payment_id"] == test_payment_id
        assert hist_data["total_decisions"] >= 1
        assert hist_data["total_predictions"] >= 1
        assert len(hist_data["decisions"]) >= 1
