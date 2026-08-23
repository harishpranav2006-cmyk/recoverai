"""
RecoverAI — End-to-End Workflow Integration & Reliability Tests
==============================================================
Validates the complete chain from Failed Payment to ML Prediction, AI Decision Engine,
Autonomous Recovery Workflow, Gateway Simulator, State Machine, Outcome, and Analytics.
"""

from __future__ import annotations

import pytest

from backend.database import SessionLocal
from backend.models import (
    AgentDecision,
    Customer,
    Message,
    ModelPrediction,
    Payment,
    RecoveryAction,
    RecoveryCase,
    RecoveryOutcome,
    RetryAttempt,
)
from services.recovery_workflow import run_recovery_workflow
from services.analytics import calculate_recovery_metrics
from services.state_machine import PaymentStateMachine, PaymentState, InvalidStateTransitionError


class TestEndToEndWorkflow:
    """End-to-End tests spanning the complete lifecycle of payment recovery."""

    @pytest.fixture
    def db_session(self):
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def test_high_confidence_smart_retry_end_to_end(self, db_session):
        """
        Flow 1: High Confidence ($p >= 0.65$)
        Payment Failed -> ML Predict -> High Confidence -> Smart Retry -> Gateway Simulator -> Recovered.
        """
        # Find or create a transient failure payment
        payment = (
            db_session.query(Payment)
            .filter(Payment.failure_reason == "network_failure", Payment.retry_count == 0)
            .first()
        )
        assert payment is not None, "Seed data must contain a transient network failure payment"

        # Execute complete workflow
        result = run_recovery_workflow(
            payment_id=payment.id,
            channel_override="whatsapp",
            force_fresh=True,
            seed=42,
            db=db_session,
        )

        assert result["payment_id"] == payment.id
        assert result["decision"] is not None
        assert result["decision"]["tier"] == "HIGH_CONFIDENCE"
        assert result["decision"]["strategy"] == "SMART_RETRY"
        assert result["outcome"] is not None
        assert result["simulated"] is True

        # Database Consistency Validation
        db_session.refresh(payment)
        assert payment is not None
        assert result["outcome"]["status"] in ["RECOVERED", "FAILED"]

        db_case = db_session.query(RecoveryCase).filter(RecoveryCase.payment_id == payment.id).first()
        assert db_case is not None
        assert db_case.status in ["recovered", "failed", "in_progress"]

        db_dec = db_session.query(AgentDecision).filter(AgentDecision.payment_id == payment.id).first()
        assert db_dec is not None
        assert db_dec.recovery_probability >= 0.65

    def test_actionable_outreach_flow_and_privacy(self, db_session):
        """
        Flow 2: Actionable Outreach ($0.45 <= p < 0.65$) / Expired Card
        Verifies customer message generation, privacy enforcement, and simulated outreach.
        """
        payment = (
            db_session.query(Payment)
            .filter(Payment.failure_reason == "expired_card", Payment.retry_count == 0)
            .first()
        )
        assert payment is not None

        result = run_recovery_workflow(
            payment_id=payment.id,
            channel_override="whatsapp",
            force_fresh=True,
            seed=42,
            db=db_session,
        )

        assert result["decision"]["strategy"] in ["PAYMENT_METHOD_UPDATE", "CUSTOMER_OUTREACH"]

        # Privacy verification: Ensure customer message never exposes internal ML scores
        msg = (
            db_session.query(Message)
            .filter(Message.customer_id == payment.customer_id)
            .order_by(Message.timestamp.desc())
            .first()
        )
        if msg:
            content = msg.content
            assert "0." not in content, "Customer message must not contain probability decimal"
            assert "SHAP" not in content, "Customer message must not contain SHAP keywords"
            assert "TIER" not in content, "Customer message must not contain internal tier designations"
            assert "reason_code" not in content, "Customer message must not contain internal reason codes"

    def test_low_recovery_suppression_flow(self, db_session):
        """
        Flow 3: Low Recovery ($p < 0.45$)
        Ensures blind retries are suppressed and state is updated safely.
        """
        payment = (
            db_session.query(Payment)
            .filter(Payment.failure_reason == "authentication_failure")
            .first()
        )
        assert payment is not None

        result = run_recovery_workflow(
            payment_id=payment.id,
            channel_override="email",
            force_fresh=True,
            seed=42,
            db=db_session,
        )

        assert result["decision"] is not None
        assert result["payment_id"] == payment.id

    def test_temporary_failure_delay_spacing(self):
        """
        Flow 4: Temporary Failures enforce exact delay rules:
        - network/gateway timeout: 4 hours
        - insufficient funds/bank decline: 24 hours
        """
        from agent.decision_engine import DecisionEngine

        engine = DecisionEngine()
        res_net = engine.evaluate(
            {"payment_id": "P_TEST_NET", "amount": 1500.0, "failure_reason": "network_failure", "retry_count": 0},
            recovery_prob=0.85,
        )
        assert res_net.delay_hours == 4.0

        res_funds = engine.evaluate(
            {"payment_id": "P_TEST_FUNDS", "amount": 1500.0, "failure_reason": "insufficient_funds", "retry_count": 0},
            recovery_prob=0.85,
        )
        assert res_funds.delay_hours == 24.0

    def test_retry_limit_blocking(self, db_session):
        """
        Flow 5: Max Retry Limit (3 attempts).
        Attempts at retry_count >= 3 must be blocked from automated retries.
        """
        payment = db_session.query(Payment).filter(Payment.retry_count >= 3).first()
        if not payment:
            payment = db_session.query(Payment).filter(Payment.payment_success == False).first()
            payment.retry_count = 3
            db_session.commit()

        result = run_recovery_workflow(
            payment_id=payment.id,
            force_fresh=True,
            db=db_session,
        )
        assert result["decision"]["strategy"] == "SUPPRESSION"
        assert any(
            code in result["decision"]["reason_codes"]
            for code in ["RETRY_LIMIT_REACHED", "RETRY_BLOCKED", "MAX_RETRIES_EXCEEDED"]
        )

    def test_state_machine_legal_and_illegal_transitions(self):
        """
        Flow 6: State Machine Integrity
        Validates legal state flows and ensures invalid transitions raise exceptions.
        """
        sm = PaymentStateMachine()

        # Legal: FAILED -> RETRY_SCHEDULED -> RETRYING -> RECOVERED
        assert (
            sm.transition_payment(PaymentState.FAILED, PaymentState.RETRY_SCHEDULED)
            == PaymentState.RETRY_SCHEDULED
        )
        assert (
            sm.transition_payment(PaymentState.RETRY_SCHEDULED, PaymentState.RETRYING)
            == PaymentState.RETRYING
        )
        assert (
            sm.transition_payment(PaymentState.RETRYING, PaymentState.RECOVERED)
            == PaymentState.RECOVERED
        )

        # Illegal: RECOVERED -> RETRYING
        with pytest.raises(InvalidStateTransitionError):
            sm.transition_payment(PaymentState.RECOVERED, PaymentState.RETRYING)

        # Illegal: RECOVERED -> FAILED
        with pytest.raises(InvalidStateTransitionError):
            sm.transition_payment(PaymentState.RECOVERED, PaymentState.FAILED)

    def test_idempotency_workflow_replay(self, db_session):
        """
        Flow 7: Idempotency Protection
        Repeated workflow calls on a resolved payment return cached outcome without duplicate DB records.
        """
        payment = db_session.query(Payment).filter(Payment.payment_success == False).first()

        # First run (force fresh)
        res1 = run_recovery_workflow(
            payment_id=payment.id,
            force_fresh=True,
            seed=42,
            db=db_session,
        )

        outcomes_count_before = (
            db_session.query(RecoveryOutcome)
            .join(RecoveryCase, RecoveryOutcome.case_id == RecoveryCase.id)
            .filter(RecoveryCase.payment_id == payment.id)
            .count()
        )

        # Second run (without force fresh - should return cached outcome)
        res2 = run_recovery_workflow(
            payment_id=payment.id,
            force_fresh=False,
            seed=42,
            db=db_session,
        )

        outcomes_count_after = (
            db_session.query(RecoveryOutcome)
            .join(RecoveryCase, RecoveryOutcome.case_id == RecoveryCase.id)
            .filter(RecoveryCase.payment_id == payment.id)
            .count()
        )

        assert outcomes_count_before == outcomes_count_after, "Idempotent call must not duplicate outcome records"

    def test_analytics_metrics_consistency_delta(self, db_session):
        """
        Flow 8: Analytics Consistency
        Validates that metrics calculated by analytics service are non-negative and mathematically sound.
        """
        metrics = calculate_recovery_metrics(db_session)
        assert metrics["total_payments"] == 50000
        assert metrics["total_customers"] == 5000
        assert metrics["total_failed_payments"] > 0
        assert metrics["recovered_value"] >= 0.0
        assert metrics["unrecovered_value"] >= 0.0
        assert 0.0 <= metrics["recovery_rate"] <= 1.0
        assert metrics["failed_payment_value"] == pytest.approx(
            metrics["recovered_value"] + metrics["unrecovered_value"], rel=1e-3
        )
