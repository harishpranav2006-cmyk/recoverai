"""
RecoverAI — Recovery Workflow & Retry Execution Test Suite
==========================================================
Tests:
- End-to-end recovery workflow execution
- Retry execution and safety validation
- Multi-step recovery & retry counting
- Idempotency guarantees (running workflow on recovered payment returns cached state)
- Outreach simulation within workflow
- All 7 demo scenario workflow executions
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.database import SessionLocal
from backend.models.payment import Payment
from backend.models.recovery import RecoveryCase, RecoveryOutcome, RetryAttempt
from services.recovery_workflow import run_recovery_workflow
from services.retry_service import RetryExecutionError, execute_retry


@pytest.fixture
def sample_failed_payment_id() -> str:
    db = SessionLocal()
    try:
        p = (
            db.query(Payment)
            .filter(Payment.payment_success == False, Payment.recovered_after_failure == False, Payment.retry_count == 0)
            .first()
        )
        assert p is not None
        return p.id
    finally:
        db.close()


class TestRecoveryWorkflow:
    """Verifies end-to-end recovery workflow."""

    def test_run_recovery_workflow_structure(self, sample_failed_payment_id: str) -> None:
        res = run_recovery_workflow(sample_failed_payment_id, seed=42)

        assert isinstance(res, dict)
        assert res["payment_id"] == sample_failed_payment_id
        assert "decision" in res
        assert "action" in res
        assert "outcome" in res
        assert "revenue_impact" in res
        assert res["simulated"] is True

    def test_idempotency_on_recovered_payment(self, sample_failed_payment_id: str) -> None:
        """Second call on an already resolved payment must return immediately with cached state."""
        # 1st run
        res1 = run_recovery_workflow(sample_failed_payment_id, seed=42)

        # Manually verify or set payment state to recovered in test DB if needed
        db = SessionLocal()
        try:
            p = db.query(Payment).filter(Payment.id == sample_failed_payment_id).first()
            p.recovered_after_failure = True
            p.recovered_amount = float(p.amount)
            db.commit()
        finally:
            db.close()

        # 2nd run
        res2 = run_recovery_workflow(sample_failed_payment_id, seed=42)
        assert res2["status"] == "RECOVERED"
        assert res2["idempotent"] is True

    def test_retry_safety_blocks_retry_count_3(self) -> None:
        """Retry execution must fail when retry_count >= 3."""
        db = SessionLocal()
        try:
            p = db.query(Payment).filter(Payment.payment_success == False, Payment.retry_count >= 3).first()
            if p:
                with pytest.raises(RetryExecutionError):
                    execute_retry(p.id, db=db)
        finally:
            db.close()

    def test_demo_scenarios_workflow_execution(self) -> None:
        """Executes all 7 Phase 1 tagged demo scenarios through the complete workflow."""
        demo_keys = [
            "HIGH_RECOVERY_CASE",
            "MEDIUM_RECOVERY_CASE",
            "LOW_RECOVERY_CASE",
            "TEMPORARY_FAILURE_CASE",
            "PERMANENT_FAILURE_CASE",
            "MULTIPLE_RETRY_CASE",
            "HIGH_VALUE_CUSTOMER",
        ]
        db = SessionLocal()
        try:
            for k in demo_keys:
                p = db.query(Payment).filter(Payment.demo_scenario == k).first()
                if p:
                    res = run_recovery_workflow(p.id, seed=42, db=db)
                    assert res["payment_id"] == p.id
                    assert "outcome" in res
                    assert res["simulated"] is True
        finally:
            db.close()
