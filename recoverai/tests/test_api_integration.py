"""
End-to-End API Integration Tests
=================================
Tests complete end-to-end recovery lifecycle via the REST API layer.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_full_recovery_workflow_api_integration():
    payment_id = "P000227"

    # 1. Run Complete Workflow
    res = client.post(f"/api/v1/recovery/{payment_id}/workflow?force_fresh=true&seed=42")
    assert res.status_code == 200
    data = res.json()

    # 2. Verify Structured Response
    assert data["payment_id"] == payment_id
    assert "decision" in data
    assert "action" in data
    assert "outcome" in data
    assert "revenue_impact" in data

    decision = data["decision"]
    assert decision["strategy"] in ["SMART_RETRY", "CUSTOMER_OUTREACH", "PAYMENT_METHOD_UPDATE", "SUPPRESSION", "VIP_ACCOUNT_ESCALATION"]
    assert 0.0 <= decision["recovery_probability"] <= 1.0

    # 3. Verify Decision Record via Decision API
    dec_res = client.get(f"/api/v1/recovery/{payment_id}/decision")
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["payment_id"] == payment_id

    # 4. Verify History API
    hist_res = client.get(f"/api/v1/recovery/{payment_id}/history")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data["decisions"]) >= 1
    assert len(hist_data["predictions"]) >= 1

    # 5. Verify Timeline API
    time_res = client.get(f"/api/v1/payments/{payment_id}/timeline")
    assert time_res.status_code == 200
    time_data = time_res.json()
    assert time_data["total_events"] >= 2

    # 6. Verify Analytics reflect the workflow
    analytics_res = client.get("/api/v1/analytics/overview")
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["recovered_value"] > 0
