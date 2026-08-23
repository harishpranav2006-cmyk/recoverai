"""
RecoverAI — Agent Tools Test Suite
==================================
Tests execution, input validation, output typing, and error handling for all 8 agent tools.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from agent.tools import (
    analyze_failure_reason,
    calculate_customer_value,
    generate_customer_message,
    get_customer_history,
    get_payment_details,
    get_recovery_policy,
    predict_recovery_probability,
    recommend_recovery_strategy,
)
from backend.database import SessionLocal
from backend.models.payment import Payment


@pytest.fixture
def sample_failed_payment_id() -> str:
    db = SessionLocal()
    try:
        p = (
            db.query(Payment)
            .filter(
                Payment.payment_success == False,
                Payment.retry_count == 0,
                Payment.failure_reason == "network_failure",
            )
            .first()
        )
        assert p is not None, "Database must have unrecovered failed payments."
        return p.id
    finally:
        db.close()


class TestAgentTools:
    """Verifies all 8 agent tools."""

    def test_get_payment_details_valid(self, sample_failed_payment_id: str) -> None:
        details = get_payment_details(sample_failed_payment_id)
        assert isinstance(details, dict)
        assert details["payment_id"] == sample_failed_payment_id
        assert "customer_id" in details
        assert "amount" in details
        assert "failure_reason" in details
        assert "payment_success" in details
        assert details["payment_success"] is False

    def test_get_payment_details_invalid_raises(self) -> None:
        with pytest.raises(KeyError):
            get_payment_details("P_NON_EXISTENT_999999")

    def test_get_payment_details_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            get_payment_details("")

    def test_get_customer_history_valid(self, sample_failed_payment_id: str) -> None:
        p_details = get_payment_details(sample_failed_payment_id)
        c_history = get_customer_history(p_details["customer_id"])
        assert isinstance(c_history, dict)
        assert c_history["customer_id"] == p_details["customer_id"]
        assert "name" in c_history
        assert "email" in c_history
        assert "lifetime_value" in c_history
        assert "total_transactions" in c_history
        assert c_history["total_transactions"] >= 1

    def test_get_customer_history_invalid_raises(self) -> None:
        with pytest.raises(KeyError):
            get_customer_history("C_NON_EXISTENT_999999")

    def test_predict_recovery_probability_tool(self, sample_failed_payment_id: str) -> None:
        p_details = get_payment_details(sample_failed_payment_id)
        ml_res = predict_recovery_probability(p_details)
        assert isinstance(ml_res, dict)
        assert "recovery_probability" in ml_res
        assert 0.0 <= ml_res["recovery_probability"] <= 1.0
        assert "model_version" in ml_res

    def test_analyze_failure_reason_temporary(self) -> None:
        res = analyze_failure_reason("network_failure")
        assert res["is_temporary"] is True
        assert res["is_permanent"] is False
        assert res["retry_eligible"] is True
        assert res["recommended_delay_hours"] == 4.0

    def test_analyze_failure_reason_permanent(self) -> None:
        res = analyze_failure_reason("expired_card")
        assert res["is_permanent"] is True
        assert res["is_temporary"] is False
        assert res["retry_eligible"] is False

    def test_calculate_customer_value(self, sample_failed_payment_id: str) -> None:
        p_details = get_payment_details(sample_failed_payment_id)
        val = calculate_customer_value(p_details["customer_id"])
        assert "customer_lifetime_value" in val
        assert "segment" in val
        assert "is_vip" in val
        assert "tier_label" in val

    def test_get_recovery_policy(self) -> None:
        policy = get_recovery_policy()
        assert policy["high_confidence_threshold"] == 0.65
        assert policy["outreach_threshold"] == 0.45
        assert policy["max_retry_attempts"] == 3
        assert policy["min_retry_delay_hours"] == 4.0
        assert "retry_delays_hours" in policy

    def test_recommend_recovery_strategy_tool(self, sample_failed_payment_id: str) -> None:
        p_details = get_payment_details(sample_failed_payment_id)
        c_history = get_customer_history(p_details["customer_id"])
        decision = recommend_recovery_strategy(
            payment=p_details,
            customer=c_history,
            recovery_probability=0.72,
        )
        assert decision.tier == "HIGH_CONFIDENCE"
        assert decision.strategy == "SMART_RETRY"

    def test_generate_customer_message_tool(self, sample_failed_payment_id: str) -> None:
        p_details = get_payment_details(sample_failed_payment_id)
        c_history = get_customer_history(p_details["customer_id"])
        decision = recommend_recovery_strategy(
            payment=p_details,
            customer=c_history,
            recovery_probability=0.55,
        )
        msg = generate_customer_message(
            decision=decision,
            customer=c_history,
            payment=p_details,
            channel="WHATSAPP",
        )
        assert isinstance(msg, dict)
        assert "content" in msg
        assert "channel" in msg
        assert msg["channel"] == "WHATSAPP"
        # Privacy guarantee: no technical scores in customer message
        assert "0.55" not in msg["content"]
        assert "probability" not in msg["content"].lower()
        assert "shap" not in msg["content"].lower()
