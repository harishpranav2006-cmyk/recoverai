"""
RecoverAI — Autonomous Recovery Decision Engine
================================================
Translates ML recovery probability, failure telemetry, and customer context
into deterministic, policy-backed revenue recovery decisions.

Key Capabilities:
- 14-Step Decision Priority Architecture
- Centralized Settings & Threshold Integration
- Strict Hard Safety Rules (Retry limits, permanent failure guards, high-value overrides)
- Dynamic Delay Calculation (4h transient network, 24h bank/insufficient funds)
- Reason Code & Natural-Language Explanation Generation
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from backend.config import settings
from backend.schemas.decision import (
    DecisionResponse,
    ReasonCode,
    RecommendedAction,
    RecoveryStrategy,
    RecoveryTier,
)
from ml.predict import predict_recovery_probability

logger = logging.getLogger(__name__)


# Permanent / High-Friction Failure Types that must never be blindly retried
PERMANENT_FAILURE_REASONS = {
    "expired_card",
    "invalid_payment_details",
    "customer_cancelled",
}

# Transient / Temporary Failures eligible for short-delay smart retries
TEMPORARY_FAILURE_REASONS = {
    "network_failure",
    "temporary_gateway_failure",
    "payment_timeout",
}


class DecisionEngine:
    """
    Deterministic rule-and-ML policy engine for RecoverAI.
    """

    def __init__(
        self,
        high_threshold: Optional[float] = None,
        outreach_threshold: Optional[float] = None,
        max_retries: Optional[int] = None,
        min_retry_delay: Optional[float] = None,
        vip_clv_threshold: Optional[float] = None,
        high_value_payment_threshold: Optional[float] = None,
    ) -> None:
        self.high_threshold = high_threshold or settings.high_confidence_threshold
        self.outreach_threshold = outreach_threshold or settings.outreach_threshold
        self.max_retries = max_retries if max_retries is not None else settings.max_retry_attempts
        self.min_retry_delay = min_retry_delay or settings.min_retry_delay_hours
        self.vip_clv_threshold = vip_clv_threshold or settings.vip_clv_threshold
        self.high_value_threshold = high_value_payment_threshold or settings.high_value_payment_threshold

    def evaluate(
        self,
        payment_data: Dict[str, Any],
        customer_data: Optional[Dict[str, Any]] = None,
        recovery_prob: Optional[float] = None,
        explanation_factors: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> DecisionResponse:
        """
        Executes the 14-step deterministic decision evaluation pipeline.
        """
        payment_id = str(payment_data.get("payment_id", "P_UNKNOWN"))
        payment_amount = float(payment_data.get("amount", 0.0))
        failure_reason = str(payment_data.get("failure_reason", "")).lower().strip()
        retry_count = int(payment_data.get("retry_count", 0))

        # Merge customer data if provided
        if customer_data:
            clv = float(customer_data.get("lifetime_value", payment_data.get("customer_lifetime_value", 0.0)))
            segment = str(customer_data.get("segment", payment_data.get("segment", ""))).lower()
        else:
            clv = float(payment_data.get("customer_lifetime_value", 0.0))
            segment = str(payment_data.get("segment", "")).lower()

        sub_type = str(payment_data.get("subscription_type", "")).lower()
        prev_successes = int(payment_data.get("previous_successful_payments", 0))
        prev_failures = int(payment_data.get("previous_failed_payments", 0))
        is_vip = clv >= self.vip_clv_threshold or sub_type == "enterprise" or segment == "enterprise"

        # ──────────────────────────────────────────────────────────────────────
        # STEP 1 & 3: Check if Payment is Already Succeeded / Resolved
        # ──────────────────────────────────────────────────────────────────────
        is_success = payment_data.get("payment_success") is True
        is_resolved = payment_data.get("payment_resolved") is True or payment_data.get("status") == "recovered"
        if is_success or is_resolved:
            return DecisionResponse(
                payment_id=payment_id,
                recovery_probability=1.0,
                tier=RecoveryTier.SUPPRESS_OR_ESCALATE,
                strategy=RecoveryStrategy.SUPPRESSION,
                recommended_action=RecommendedAction.APPLY_GRACE_PERIOD_AND_SUPPRESS,
                delay_hours=None,
                reason_codes=[ReasonCode.PAYMENT_ALREADY_RECOVERED, ReasonCode.RETRY_BLOCKED],
                explanation="Payment has already succeeded or been resolved. Retries and recovery actions are blocked.",
                customer_message_required=False,
                human_review_required=False,
                channel_recommendation=None,
                metadata={"payment_resolved": True},
            )

        # ──────────────────────────────────────────────────────────────────────
        # STEP 5: Hard Safety Rule — Retry Limit Exhaustion
        # ──────────────────────────────────────────────────────────────────────
        if retry_count >= self.max_retries:
            return DecisionResponse(
                payment_id=payment_id,
                recovery_probability=round(float(recovery_prob or 0.25), 4),
                tier=RecoveryTier.SUPPRESS_OR_ESCALATE,
                strategy=RecoveryStrategy.SUPPRESSION,
                recommended_action=RecommendedAction.APPLY_GRACE_PERIOD_AND_SUPPRESS,
                delay_hours=None,
                reason_codes=[ReasonCode.RETRY_LIMIT_REACHED, ReasonCode.RETRY_BLOCKED],
                explanation=f"Maximum retry limit ({self.max_retries}) reached. Automatic retries blocked to protect customer account and gateway quotas.",
                customer_message_required=True,
                human_review_required=False,
                channel_recommendation="email",
                metadata={"retry_limit_reached": True},
            )

        # ──────────────────────────────────────────────────────────────────────
        # STEP 7: ML Recovery Prediction
        # ──────────────────────────────────────────────────────────────────────
        if recovery_prob is None:
            ml_result = predict_recovery_probability(payment_data, include_explanation=True)
            recovery_prob = float(ml_result["recovery_probability"])
            if explanation_factors is None:
                explanation_factors = ml_result.get("factors", [])
        elif explanation_factors is None:
            explanation_factors = []

        recovery_prob = round(float(recovery_prob), 4)

        # ──────────────────────────────────────────────────────────────────────
        # STEP 4: Hard Safety Rule — Permanent Failure Guards
        # ──────────────────────────────────────────────────────────────────────
        if failure_reason in PERMANENT_FAILURE_REASONS:
            reason_codes = [ReasonCode.PERMANENT_FAILURE, ReasonCode.ALTERNATIVE_PAYMENT_RECOMMENDED]
            
            if failure_reason in ["expired_card", "invalid_payment_details"]:
                reason_codes.append(
                    ReasonCode.EXPIRED_CARD_DETECTED
                    if failure_reason == "expired_card"
                    else ReasonCode.INVALID_PAYMENT_CREDENTIALS
                )
                strategy = RecoveryStrategy.PAYMENT_METHOD_UPDATE
                action = RecommendedAction.REQUEST_PAYMENT_METHOD_UPDATE
                channel = "email"
                explanation = "Card or payment credential is permanently invalid or expired. Automatic retry blocked; customer payment method update requested."
            else:  # customer_cancelled
                reason_codes.append(ReasonCode.CUSTOMER_CANCELLED_FLOW)
                strategy = RecoveryStrategy.RETENTION_INCENTIVE
                action = RecommendedAction.SEND_RETENTION_LINK
                channel = "whatsapp"
                explanation = "Customer cancelled the subscription flow. Dispatched personalized retention and reactivation link."

            tier = RecoveryTier.ACTIONABLE_OUTREACH if recovery_prob >= self.outreach_threshold else RecoveryTier.SUPPRESS_OR_ESCALATE
            if is_vip:
                reason_codes.append(ReasonCode.HIGH_CUSTOMER_VALUE)

            return DecisionResponse(
                payment_id=payment_id,
                recovery_probability=recovery_prob,
                tier=tier,
                strategy=strategy,
                recommended_action=action,
                delay_hours=0.0,
                reason_codes=reason_codes,
                explanation=explanation,
                customer_message_required=True,
                human_review_required=False,
                channel_recommendation=channel,
                metadata={"permanent_failure_type": failure_reason, "factors": explanation_factors},
            )

        # ──────────────────────────────────────────────────────────────────────
        # STEP 9: Determine Tier
        # ──────────────────────────────────────────────────────────────────────
        if recovery_prob >= self.high_threshold:
            tier = RecoveryTier.HIGH_CONFIDENCE
        elif recovery_prob >= self.outreach_threshold:
            tier = RecoveryTier.ACTIONABLE_OUTREACH
        else:
            tier = RecoveryTier.SUPPRESS_OR_ESCALATE

        reason_codes: List[ReasonCode] = []
        channel_rec: Optional[str] = None
        human_review = False
        customer_msg = False
        delay_hours: Optional[float] = None

        # ──────────────────────────────────────────────────────────────────────
        # TIER 1: HIGH CONFIDENCE (p >= 0.65) → SMART RETRY
        # ──────────────────────────────────────────────────────────────────────
        if tier == RecoveryTier.HIGH_CONFIDENCE:
            strategy = RecoveryStrategy.SMART_RETRY
            recommended_action = RecommendedAction.RETRY_AFTER_DELAY
            reason_codes.append(ReasonCode.HIGH_RECOVERY_PROBABILITY)
            reason_codes.append(ReasonCode.RETRY_ELIGIBLE)

            # Failure-specific delay calculation
            if failure_reason in TEMPORARY_FAILURE_REASONS:
                delay_hours = settings.network_failure_delay
                reason_codes.append(ReasonCode.TEMPORARY_FAILURE)
                reason_codes.append(
                    ReasonCode.TRANSIENT_NETWORK_FAILURE
                    if failure_reason == "network_failure"
                    else ReasonCode.TRANSIENT_GATEWAY_ERROR
                )
            elif failure_reason == "insufficient_funds":
                delay_hours = settings.insufficient_funds_delay
                reason_codes.append(ReasonCode.INSUFFICIENT_FUNDS_DETECTED)
            elif failure_reason == "bank_declined":
                delay_hours = settings.bank_declined_delay
                reason_codes.append(ReasonCode.BANK_DECLINE_REQUIRES_CUSTOMER)
            else:
                delay_hours = settings.default_retry_delay

            # Ensure minimum retry delay spacing
            delay_hours = max(delay_hours, self.min_retry_delay)

            if prev_successes >= 3:
                reason_codes.append(ReasonCode.STRONG_PAYMENT_HISTORY)
            if retry_count <= 1:
                reason_codes.append(ReasonCode.LOW_RETRY_COUNT)
            if prev_failures == 0:
                reason_codes.append(ReasonCode.FIRST_TIME_PAYMENT_FAILURE)
            if is_vip:
                reason_codes.append(ReasonCode.HIGH_CUSTOMER_VALUE)

            explanation = (
                f"High recovery probability ({recovery_prob:.1%}), strong payment history, "
                f"and low retry count support an automated smart retry scheduled in {int(delay_hours)} hours."
            )

        # ──────────────────────────────────────────────────────────────────────
        # TIER 2: ACTIONABLE OUTREACH (0.45 <= p < 0.65) → CUSTOMER OUTREACH
        # ──────────────────────────────────────────────────────────────────────
        elif tier == RecoveryTier.ACTIONABLE_OUTREACH:
            strategy = RecoveryStrategy.CUSTOMER_OUTREACH
            recommended_action = RecommendedAction.DISPATCH_PAYMENT_LINK
            delay_hours = 0.0
            customer_msg = True
            channel_rec = "whatsapp"
            reason_codes.append(ReasonCode.MODERATE_RECOVERY_PROBABILITY)

            if failure_reason == "insufficient_funds":
                reason_codes.append(ReasonCode.INSUFFICIENT_FUNDS_DETECTED)
            elif failure_reason == "limit_exceeded":
                reason_codes.append(ReasonCode.DAILY_LIMIT_EXCEEDED)
            else:
                reason_codes.append(ReasonCode.BANK_DECLINE_REQUIRES_CUSTOMER)

            if is_vip:
                reason_codes.append(ReasonCode.HIGH_CUSTOMER_VALUE)

            # High value payment check
            if payment_amount >= self.high_value_threshold:
                human_review = True
                reason_codes.append(ReasonCode.HIGH_VALUE_PAYMENT_REVIEW)
                explanation = f"Moderate recovery probability with high transaction value (₹{payment_amount:,.2f}). Actionable payment link prepared with human review flag."
            else:
                explanation = f"Moderate recovery probability ({recovery_prob:.1%}) indicates direct customer outreach via payment link yields optimal recovery rate."

        # ──────────────────────────────────────────────────────────────────────
        # TIER 3: SUPPRESS OR ESCALATE (p < 0.45)
        # ──────────────────────────────────────────────────────────────────────
        else:
            delay_hours = None
            reason_codes.append(ReasonCode.LOW_RECOVERY_PROBABILITY)
            reason_codes.append(ReasonCode.RETRY_BLOCKED)

            # VIP Override: High value enterprise accounts get account manager touch
            if is_vip:
                strategy = RecoveryStrategy.VIP_ACCOUNT_ESCALATION
                recommended_action = RecommendedAction.ESCALATE_TO_ACCOUNT_MANAGER
                human_review = True
                customer_msg = False
                reason_codes.append(ReasonCode.VIP_ENTERPRISE_HIGH_TOUCH)
                reason_codes.append(ReasonCode.HIGH_CUSTOMER_VALUE)
                explanation = "High-value VIP / Enterprise account with low automated recovery probability. Escalated to dedicated Account Manager for white-glove assistance."

            # Low Customer Engagement / Chronic Failure
            else:
                strategy = RecoveryStrategy.HUMAN_REVIEW
                recommended_action = RecommendedAction.FLAG_FOR_CS_REVIEW
                human_review = True
                customer_msg = False
                reason_codes.append(ReasonCode.CHRONIC_FAILURE_HISTORY)
                reason_codes.append(ReasonCode.HUMAN_REVIEW_REQUIRED)
                explanation = f"Low recovery probability ({recovery_prob:.1%}) and failure history indicate automated retries will fail. Flagged for customer support review."

        return DecisionResponse(
            payment_id=payment_id,
            recovery_probability=recovery_prob,
            tier=tier,
            strategy=strategy,
            recommended_action=recommended_action,
            delay_hours=delay_hours,
            reason_codes=reason_codes,
            explanation=explanation,
            customer_message_required=customer_msg,
            human_review_required=human_review,
            channel_recommendation=channel_rec,
            metadata={"factors": explanation_factors, "vip_account": is_vip, "amount": payment_amount},
        )


# Global Engine Singleton
_GLOBAL_ENGINE: Optional[DecisionEngine] = None


def get_decision_engine() -> DecisionEngine:
    """Returns the singleton DecisionEngine instance."""
    global _GLOBAL_ENGINE
    if _GLOBAL_ENGINE is None:
        _GLOBAL_ENGINE = DecisionEngine()
    return _GLOBAL_ENGINE


def decide_recovery_strategy(
    payment: Dict[str, Any],
    customer: Optional[Dict[str, Any]] = None,
    recovery_probability: Optional[float] = None,
    context: Optional[Dict[str, Any]] = None,
) -> DecisionResponse:
    """
    Standard interface for the RecoverAI Decision Engine.
    """
    engine = get_decision_engine()
    return engine.evaluate(
        payment_data=payment,
        customer_data=customer,
        recovery_prob=recovery_probability,
        context=context,
    )


def evaluate_recovery_decision(
    payment_data: Dict[str, Any],
    recovery_prob: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Convenience function returning JSON dictionary matching the RecoverAI schema.
    """
    decision = decide_recovery_strategy(payment=payment_data, recovery_probability=recovery_prob)
    return decision.model_dump()


def evaluate_payment(payment_id: str) -> DecisionResponse:
    """
    Convenience function to fetch payment & customer by ID and evaluate recovery policy.
    """
    from agent.tools import get_customer_history, get_payment_details
    payment_dict = get_payment_details(payment_id)
    customer_dict = None
    if payment_dict.get("customer_id"):
        try:
            customer_dict = get_customer_history(payment_dict["customer_id"])
        except Exception:
            pass
    return decide_recovery_strategy(payment=payment_dict, customer=customer_dict)

