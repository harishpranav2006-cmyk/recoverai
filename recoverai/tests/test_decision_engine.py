"""
RecoverAI — Decision Engine Exhaustive Test Suite
=================================================
Tests:
- Exact threshold boundaries (0.80, 0.65, 0.6499, 0.45, 0.4499)
- Retry limits (retry_count = 0, 2, 3, 4)
- Permanent failure restrictions (expired_card, invalid_details, customer_cancelled)
- Temporary failure retry eligibility (network, gateway, timeout)
- Delay rules (4h for network, 24h for insufficient funds/bank decline)
- High value payment safety overrides (>= ₹15,000)
- VIP Account overrides (CLV >= ₹10,000 / Enterprise)
- Already recovered payment blocks
- Schema matching user's exact specification
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from agent.decision_engine import DecisionEngine, decide_recovery_strategy, evaluate_recovery_decision
from backend.schemas.decision import (
    DecisionResponse,
    ReasonCode,
    RecommendedAction,
    RecoveryStrategy,
    RecoveryTier,
)


@pytest.fixture
def engine() -> DecisionEngine:
    return DecisionEngine()


class TestThresholdBoundaries:
    """Verifies exact 3-tier boundary cutoff points."""

    def test_threshold_0_80_high_confidence(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P01", "failure_reason": "network_failure"}
        d = engine.evaluate(p, recovery_prob=0.80)
        assert d.tier == RecoveryTier.HIGH_CONFIDENCE
        assert d.strategy == RecoveryStrategy.SMART_RETRY

    def test_threshold_0_65_high_confidence(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P02", "failure_reason": "network_failure"}
        d = engine.evaluate(p, recovery_prob=0.65)
        assert d.tier == RecoveryTier.HIGH_CONFIDENCE
        assert d.strategy == RecoveryStrategy.SMART_RETRY

    def test_threshold_0_6499_actionable_outreach(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P03", "failure_reason": "insufficient_funds"}
        d = engine.evaluate(p, recovery_prob=0.6499)
        assert d.tier == RecoveryTier.ACTIONABLE_OUTREACH
        assert d.strategy == RecoveryStrategy.CUSTOMER_OUTREACH

    def test_threshold_0_45_actionable_outreach(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P04", "failure_reason": "insufficient_funds"}
        d = engine.evaluate(p, recovery_prob=0.45)
        assert d.tier == RecoveryTier.ACTIONABLE_OUTREACH
        assert d.strategy == RecoveryStrategy.CUSTOMER_OUTREACH

    def test_threshold_0_4499_suppress_or_escalate(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P05", "failure_reason": "bank_declined"}
        d = engine.evaluate(p, recovery_prob=0.4499)
        assert d.tier == RecoveryTier.SUPPRESS_OR_ESCALATE


class TestRetryLimits:
    """Verifies that retry_count >= 3 blocks automated retries regardless of probability."""

    def test_retry_count_0_eligible(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P10", "failure_reason": "network_failure", "retry_count": 0}
        d = engine.evaluate(p, recovery_prob=0.75)
        assert d.strategy == RecoveryStrategy.SMART_RETRY
        assert d.recommended_action == RecommendedAction.RETRY_AFTER_DELAY

    def test_retry_count_2_eligible(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P11", "failure_reason": "network_failure", "retry_count": 2}
        d = engine.evaluate(p, recovery_prob=0.75)
        assert d.strategy == RecoveryStrategy.SMART_RETRY
        assert d.recommended_action == RecommendedAction.RETRY_AFTER_DELAY

    def test_retry_count_3_blocked(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P12", "failure_reason": "network_failure", "retry_count": 3}
        d = engine.evaluate(p, recovery_prob=0.85)  # High probability must NOT override safety rule
        assert d.tier == RecoveryTier.SUPPRESS_OR_ESCALATE
        assert d.strategy == RecoveryStrategy.SUPPRESSION
        assert d.recommended_action == RecommendedAction.APPLY_GRACE_PERIOD_AND_SUPPRESS
        assert ReasonCode.RETRY_LIMIT_REACHED in d.reason_codes
        assert ReasonCode.RETRY_BLOCKED in d.reason_codes

    def test_retry_count_greater_than_3_blocked(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P13", "failure_reason": "insufficient_funds", "retry_count": 5}
        d = engine.evaluate(p, recovery_prob=0.90)
        assert d.tier == RecoveryTier.SUPPRESS_OR_ESCALATE
        assert d.strategy == RecoveryStrategy.SUPPRESSION
        assert ReasonCode.RETRY_LIMIT_REACHED in d.reason_codes


class TestPermanentFailures:
    """Permanent failures must never be blindly retried."""

    def test_expired_card_requests_method_update(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P20", "failure_reason": "expired_card"}
        d = engine.evaluate(p, recovery_prob=0.80)  # High prob should still block blind retry
        assert d.strategy == RecoveryStrategy.PAYMENT_METHOD_UPDATE
        assert d.recommended_action == RecommendedAction.REQUEST_PAYMENT_METHOD_UPDATE
        assert d.delay_hours == 0.0
        assert ReasonCode.PERMANENT_FAILURE in d.reason_codes
        assert ReasonCode.EXPIRED_CARD_DETECTED in d.reason_codes

    def test_invalid_payment_details_requests_method_update(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P21", "failure_reason": "invalid_payment_details"}
        d = engine.evaluate(p, recovery_prob=0.70)
        assert d.strategy == RecoveryStrategy.PAYMENT_METHOD_UPDATE
        assert d.recommended_action == RecommendedAction.REQUEST_PAYMENT_METHOD_UPDATE
        assert ReasonCode.INVALID_PAYMENT_CREDENTIALS in d.reason_codes

    def test_customer_cancelled_sends_retention_link(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P22", "failure_reason": "customer_cancelled"}
        d = engine.evaluate(p, recovery_prob=0.60)
        assert d.strategy == RecoveryStrategy.RETENTION_INCENTIVE
        assert d.recommended_action == RecommendedAction.SEND_RETENTION_LINK
        assert ReasonCode.CUSTOMER_CANCELLED_FLOW in d.reason_codes


class TestTemporaryFailuresAndDelays:
    """Verifies failure-specific retry delays."""

    def test_network_failure_delay_4h(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P30", "failure_reason": "network_failure"}
        d = engine.evaluate(p, recovery_prob=0.75)
        assert d.delay_hours == 4.0
        assert ReasonCode.TEMPORARY_FAILURE in d.reason_codes

    def test_temporary_gateway_failure_delay_4h(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P31", "failure_reason": "temporary_gateway_failure"}
        d = engine.evaluate(p, recovery_prob=0.75)
        assert d.delay_hours == 4.0
        assert ReasonCode.TRANSIENT_GATEWAY_ERROR in d.reason_codes

    def test_payment_timeout_delay_4h(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P32", "failure_reason": "payment_timeout"}
        d = engine.evaluate(p, recovery_prob=0.75)
        assert d.delay_hours == 4.0

    def test_insufficient_funds_delay_24h(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P33", "failure_reason": "insufficient_funds"}
        d = engine.evaluate(p, recovery_prob=0.75)
        assert d.delay_hours == 24.0
        assert ReasonCode.INSUFFICIENT_FUNDS_DETECTED in d.reason_codes

    def test_bank_declined_delay_24h(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P34", "failure_reason": "bank_declined"}
        d = engine.evaluate(p, recovery_prob=0.75)
        assert d.delay_hours == 24.0


class TestSpecialSafetyRules:
    """Already recovered payments, High-value overrides, and VIP enterprise accounts."""

    def test_already_succeeded_payment_blocked(self, engine: DecisionEngine) -> None:
        p = {"payment_id": "P40", "payment_success": True, "failure_reason": ""}
        d = engine.evaluate(p, recovery_prob=0.99)
        assert d.tier == RecoveryTier.SUPPRESS_OR_ESCALATE
        assert ReasonCode.PAYMENT_ALREADY_RECOVERED in d.reason_codes
        assert ReasonCode.RETRY_BLOCKED in d.reason_codes

    def test_high_value_payment_review_flag(self, engine: DecisionEngine) -> None:
        """Payment >= ₹15,000 in moderate tier requires human review flag."""
        p = {"payment_id": "P41", "amount": 25000.0, "failure_reason": "insufficient_funds"}
        d = engine.evaluate(p, recovery_prob=0.55)
        assert d.human_review_required is True
        assert ReasonCode.HIGH_VALUE_PAYMENT_REVIEW in d.reason_codes

    def test_vip_enterprise_escalation(self, engine: DecisionEngine) -> None:
        """Enterprise/VIP account with low probability gets escalated to Account Manager."""
        p = {
            "payment_id": "P42",
            "amount": 5000.0,
            "failure_reason": "bank_declined",
            "subscription_type": "enterprise",
            "customer_lifetime_value": 35000.0,
        }
        d = engine.evaluate(p, recovery_prob=0.35)
        assert d.strategy == RecoveryStrategy.VIP_ACCOUNT_ESCALATION
        assert d.recommended_action == RecommendedAction.ESCALATE_TO_ACCOUNT_MANAGER
        assert d.human_review_required is True
        assert ReasonCode.VIP_ENTERPRISE_HIGH_TOUCH in d.reason_codes


class TestUserReferenceSampleOutput:
    """Matches user's exact provided JSON format."""

    def test_exact_user_json_match(self) -> None:
        payment = {
            "payment_id": "P1023",
            "amount": 1999.0,
            "failure_reason": "insufficient_funds",
            "retry_count": 0,
            "previous_successful_payments": 5,
        }
        res = evaluate_recovery_decision(payment, recovery_prob=0.78)

        assert res["payment_id"] == "P1023"
        assert res["recovery_probability"] == 0.78
        assert res["tier"] == "HIGH_CONFIDENCE"
        assert res["strategy"] == "SMART_RETRY"
        assert res["recommended_action"] == "RETRY_AFTER_DELAY"
        assert res["delay_hours"] == 24
        assert res["customer_message_required"] is False
        assert res["human_review_required"] is False
        assert "HIGH_RECOVERY_PROBABILITY" in res["reason_codes"]
        assert "STRONG_PAYMENT_HISTORY" in res["reason_codes"]
        assert "LOW_RETRY_COUNT" in res["reason_codes"]
