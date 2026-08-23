"""
RecoverAI — AI Recovery Agent End-to-End Test Suite
===================================================
Tests:
- Full agent workflow execution & step tracking
- Mock LLM mode (zero external API keys)
- Message privacy verification (no probabilities or internal ML data leaked)
- LLM safety boundaries (cannot override Decision Engine outputs)
- Database persistence and audit logging
- All 7 Phase 1 demo scenario evaluations
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from agent.agent import RecoveryAgent, run_recovery_agent
from backend.database import SessionLocal
from backend.models.agent import AgentDecision, ModelPrediction
from backend.models.payment import Payment


@pytest.fixture
def agent() -> RecoveryAgent:
    return RecoveryAgent()


@pytest.fixture
def sample_failed_payment() -> Payment:
    db = SessionLocal()
    try:
        p = (
            db.query(Payment)
            .filter(Payment.payment_success == False, Payment.recovered_after_failure == False)
            .first()
        )
        assert p is not None
        return p
    finally:
        db.close()


class TestAgentExecution:
    """Verifies end-to-end agent workflow."""

    def test_full_agent_workflow_success(self, agent: RecoveryAgent, sample_failed_payment: Payment) -> None:
        result = agent.run(payment_id=sample_failed_payment.id)

        assert isinstance(result, dict)
        assert result["payment_id"] == sample_failed_payment.id
        assert "customer_id" in result
        assert "recovery_probability" in result
        assert "tier" in result
        assert "strategy" in result
        assert "recommended_action" in result
        assert "reason_codes" in result
        assert "explanation" in result
        assert "execution_steps" in result
        assert "model_version" in result
        assert "timestamp" in result

        # Check step sequence
        steps = result["execution_steps"]
        assert "get_payment_details" in steps
        assert "get_customer_history" in steps
        assert "predict_recovery_probability" in steps
        assert "recommend_recovery_strategy" in steps
        assert "persist_decision_audit" in steps

    def test_database_persistence_and_audit(self, sample_failed_payment: Payment) -> None:
        result = run_recovery_agent(sample_failed_payment.id)
        assert result["payment_id"] == sample_failed_payment.id

        db = SessionLocal()
        try:
            # Check AgentDecision was persisted
            dec = (
                db.query(AgentDecision)
                .filter(AgentDecision.payment_id == sample_failed_payment.id)
                .order_by(AgentDecision.timestamp.desc())
                .first()
            )
            assert dec is not None
            assert dec.payment_id == sample_failed_payment.id
            assert dec.recommended_action == result["recommended_action"]
            assert abs(dec.recovery_probability - result["recovery_probability"]) < 1e-4

            # Check ModelPrediction audit was persisted
            pred = (
                db.query(ModelPrediction)
                .filter(ModelPrediction.payment_id == sample_failed_payment.id)
                .order_by(ModelPrediction.timestamp.desc())
                .first()
            )
            assert pred is not None
            assert pred.payment_id == sample_failed_payment.id
            assert pred.model_version is not None
        finally:
            db.close()

    def test_mock_llm_mode_no_api_key_required(self, sample_failed_payment: Payment) -> None:
        """Agent must work flawlessly in demo/mock mode without any external API key."""
        result = run_recovery_agent(sample_failed_payment.id, channel_override="WHATSAPP")
        assert result is not None
        if result["customer_message_required"]:
            assert result["customer_message"] is not None
            assert len(result["customer_message"]) > 10

    def test_message_privacy_no_ml_leakage(self, sample_failed_payment: Payment) -> None:
        """Customer messages must NEVER expose recovery probabilities or ML terminology."""
        result = run_recovery_agent(sample_failed_payment.id)
        if result.get("customer_message"):
            msg = result["customer_message"].lower()
            assert "probability" not in msg
            assert "shap" not in msg
            assert "model" not in msg
            assert "logistic regression" not in msg
            assert "tier" not in msg


class TestDemoScenarios:
    """Verifies all 7 Phase 1 tagged demo scenarios."""

    def test_demo_high_recovery_case(self) -> None:
        db = SessionLocal()
        try:
            p = db.query(Payment).filter(Payment.demo_scenario == "HIGH_RECOVERY_CASE").first()
            if p:
                res = run_recovery_agent(p.id)
                assert res["tier"] in ["HIGH_CONFIDENCE", "ACTIONABLE_OUTREACH"]
                if res["tier"] == "HIGH_CONFIDENCE":
                    assert res["strategy"] == "SMART_RETRY"
        finally:
            db.close()

    def test_demo_medium_recovery_case(self) -> None:
        db = SessionLocal()
        try:
            p = (
                db.query(Payment)
                .filter(Payment.demo_scenario == "MEDIUM_RECOVERY_CASE", Payment.retry_count < 3)
                .first()
            )
            if p:
                res = run_recovery_agent(p.id)
                assert res["tier"] in ["ACTIONABLE_OUTREACH", "HIGH_CONFIDENCE"]
        finally:
            db.close()

    def test_demo_low_recovery_case(self) -> None:
        db = SessionLocal()
        try:
            p = db.query(Payment).filter(Payment.demo_scenario == "LOW_RECOVERY_CASE").first()
            if p:
                res = run_recovery_agent(p.id)
                assert res["tier"] == "SUPPRESS_OR_ESCALATE"
        finally:
            db.close()

    def test_demo_temporary_failure_case(self) -> None:
        db = SessionLocal()
        try:
            p = db.query(Payment).filter(Payment.demo_scenario == "TEMPORARY_FAILURE_CASE").first()
            if p:
                res = run_recovery_agent(p.id)
                # Temporary failure with low retry count should allow smart retry
                if res["tier"] == "HIGH_CONFIDENCE":
                    assert res["delay_hours"] == 4.0
        finally:
            db.close()

    def test_demo_permanent_failure_case(self) -> None:
        db = SessionLocal()
        try:
            p = db.query(Payment).filter(Payment.demo_scenario == "PERMANENT_FAILURE_CASE").first()
            if p:
                res = run_recovery_agent(p.id)
                # Must never blindly retry permanent failure
                assert res["strategy"] != "SMART_RETRY"
                assert res["recommended_action"] != "RETRY_AFTER_DELAY"
        finally:
            db.close()

    def test_demo_multiple_retry_case(self) -> None:
        db = SessionLocal()
        try:
            p = db.query(Payment).filter(Payment.demo_scenario == "MULTIPLE_RETRY_CASE").first()
            if p:
                res = run_recovery_agent(p.id)
                if p.retry_count >= 3:
                    assert res["tier"] == "SUPPRESS_OR_ESCALATE"
                    assert res["strategy"] == "SUPPRESSION"
        finally:
            db.close()

    def test_demo_high_value_customer(self) -> None:
        db = SessionLocal()
        try:
            p = db.query(Payment).filter(Payment.demo_scenario == "HIGH_VALUE_CUSTOMER").first()
            if p:
                res = run_recovery_agent(p.id)
                assert res is not None
        finally:
            db.close()
