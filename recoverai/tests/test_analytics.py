"""
RecoverAI — Revenue Analytics Test Suite
========================================
Tests:
- calculate_recovery_metrics aggregate numbers and mathematical integrity
- calculate_recovery_by_strategy
- calculate_recovery_by_failure_type
- calculate_recovery_by_segment
- FastAPI analytics endpoints (GET /analytics/recovery, /by-strategy, /by-failure, /by-segment)
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.main import app
from services.analytics import (
    calculate_recovery_by_failure_type,
    calculate_recovery_by_segment,
    calculate_recovery_by_strategy,
    calculate_recovery_metrics,
)

client = TestClient(app)


class TestRevenueAnalytics:
    """Verifies analytics calculations."""

    def test_calculate_recovery_metrics_integrity(self) -> None:
        metrics = calculate_recovery_metrics()

        assert "total_failed_payments" in metrics
        assert "failed_payment_value" in metrics
        assert "recovered_value" in metrics
        assert "unrecovered_value" in metrics
        assert "recovery_rate" in metrics

        assert metrics["total_failed_payments"] > 0
        assert metrics["failed_payment_value"] > 0
        assert 0.0 <= metrics["recovery_rate"] <= 1.0

        # Mathematical consistency: failed_val >= recovered_val
        assert metrics["failed_payment_value"] >= metrics["recovered_value"]
        assert round(metrics["failed_payment_value"] - metrics["recovered_value"], 2) == metrics["unrecovered_value"]

    def test_calculate_recovery_by_strategy(self) -> None:
        stats = calculate_recovery_by_strategy()
        assert isinstance(stats, list)

    def test_calculate_recovery_by_failure_type(self) -> None:
        stats = calculate_recovery_by_failure_type()
        assert isinstance(stats, list)
        assert len(stats) > 0
        for s in stats:
            assert "failure_reason" in s
            assert "total_failed" in s
            assert "recovered_amount" in s
            assert 0.0 <= s["recovery_rate"] <= 1.0

    def test_calculate_recovery_by_segment(self) -> None:
        stats = calculate_recovery_by_segment()
        assert isinstance(stats, list)
        assert len(stats) > 0
        for s in stats:
            assert "segment" in s
            assert "total_failed_payments" in s
            assert "recovered_value" in s


class TestAnalyticsAPIEndpoints:
    """Verifies FastAPI analytics endpoints."""

    def test_get_analytics_recovery(self) -> None:
        resp = client.get("/analytics/recovery")
        assert resp.status_code == 200
        data = resp.json()
        assert "failed_payment_value" in data
        assert "recovered_value" in data
        assert "recovery_rate" in data

    def test_get_analytics_by_strategy(self) -> None:
        resp = client.get("/analytics/recovery/by-strategy")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_analytics_by_failure(self) -> None:
        resp = client.get("/analytics/recovery/by-failure")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_analytics_by_segment(self) -> None:
        resp = client.get("/analytics/recovery/by-segment")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
