"""
RecoverAI — Autonomous Recovery Agent Tool Layer
=================================================
Provides typed, validated, structured tools for the AI Recovery Agent.

Tools:
- get_payment_details: Fetches payment record and failure context
- get_customer_history: Fetches customer profile and historical behavior
- predict_recovery_probability: Calls validated Phase 2 ML prediction interface
- analyze_failure_reason: Categorizes failure and determines retry eligibility
- calculate_customer_value: Evaluates CLV, segment, and VIP status
- get_recovery_policy: Exposes active threshold and safety policy
- recommend_recovery_strategy: Executes deterministic Decision Engine
- generate_customer_message: Produces safe, personalized customer communication
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.config import settings
from backend.database import SessionLocal
from backend.models.customer import Customer
from backend.models.payment import Payment
from backend.schemas.decision import DecisionResponse
from ml.predict import predict_recovery_probability as ml_predict_recovery_probability
from agent.decision_engine import (
    PERMANENT_FAILURE_REASONS,
    TEMPORARY_FAILURE_REASONS,
    decide_recovery_strategy,
)
from agent.messaging import generate_customer_recovery_message

logger = logging.getLogger(__name__)


# ─── Tool 1: get_payment_details ──────────────────────────────────────────────

def get_payment_details(payment_id: str) -> Dict[str, Any]:
    """
    Retrieves full details of a payment transaction from the database.
    """
    if not payment_id:
        raise ValueError("payment_id cannot be empty.")

    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise KeyError(f"Payment with ID '{payment_id}' not found in database.")

        return {
            "payment_id": payment.id,
            "customer_id": payment.customer_id,
            "timestamp": str(payment.timestamp),
            "amount": float(payment.amount),
            "currency": payment.currency,
            "payment_method": payment.payment_method,
            "payment_method_type": payment.payment_method_type,
            "device_type": payment.device_type,
            "is_subscription": bool(payment.is_subscription),
            "subscription_type": payment.subscription_type or "standard",
            "subscription_age_days": int(payment.subscription_age_days),
            "payment_success": bool(payment.payment_success),
            "failure_reason": payment.failure_reason or "",
            "failure_category": payment.failure_category or "",
            "failure_temporary": payment.failure_temporary,
            "payment_gateway_status": payment.payment_gateway_status or "failed",
            "customer_age": int(payment.customer_age),
            "customer_region": payment.customer_region,
            "previous_successful_payments": int(payment.previous_successful_payments),
            "previous_failed_payments": int(payment.previous_failed_payments),
            "previous_retry_count": int(payment.previous_retry_count),
            "days_since_last_payment": int(payment.days_since_last_payment),
            "customer_lifetime_value": float(payment.customer_lifetime_value),
            "average_transaction_value": float(payment.average_transaction_value),
            "payment_frequency": float(payment.payment_frequency),
            "last_successful_payment_days": int(payment.last_successful_payment_days),
            "historical_recovery_rate": float(payment.historical_recovery_rate),
            "retry_count": int(payment.retry_count),
        }
    finally:
        db.close()


# ─── Tool 2: get_customer_history ─────────────────────────────────────────────

def get_customer_history(customer_id: str) -> Dict[str, Any]:
    """
    Retrieves customer account context and behavioral payment statistics.
    """
    if not customer_id:
        raise ValueError("customer_id cannot be empty.")

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise KeyError(f"Customer with ID '{customer_id}' not found in database.")

        # Aggregate customer payment history
        payments = db.query(Payment).filter(Payment.customer_id == customer_id).all()
        succ_count = sum(1 for p in payments if p.payment_success)
        fail_count = sum(1 for p in payments if not p.payment_success)
        rec_count = sum(1 for p in payments if p.recovered_after_failure)

        return {
            "customer_id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "region": customer.region,
            "segment": customer.segment,
            "lifetime_value": float(customer.lifetime_value),
            "age_days": int(customer.age_days),
            "total_transactions": len(payments),
            "successful_payments": succ_count,
            "failed_payments": fail_count,
            "recovered_payments": rec_count,
            "historical_recovery_rate": rec_count / max(fail_count, 1),
            "is_vip": customer.lifetime_value >= settings.vip_clv_threshold or customer.segment == "enterprise",
        }
    finally:
        db.close()


# ─── Tool 3: predict_recovery_probability ──────────────────────────────────────

def predict_recovery_probability(payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invokes the production Phase 2 calibrated recovery prediction model.
    Guarantees no leakage fields (e.g. recovered_after_failure) enter inference.
    """
    from ml.preprocessing import LEAKAGE_COLUMNS, TARGET_COLUMN
    safe_data = {k: v for k, v in payment_data.items() if k not in LEAKAGE_COLUMNS and k != TARGET_COLUMN}
    return ml_predict_recovery_probability(safe_data, include_explanation=True)


# ─── Tool 4: analyze_failure_reason ───────────────────────────────────────────

def analyze_failure_reason(failure_reason: str) -> Dict[str, Any]:
    """
    Classifies payment failure type, determining temporary vs permanent nature
    and default retry spacing.
    """
    reason_clean = (failure_reason or "").lower().strip()
    is_perm = reason_clean in PERMANENT_FAILURE_REASONS
    is_temp = reason_clean in TEMPORARY_FAILURE_REASONS

    if reason_clean in ["network_failure", "temporary_gateway_failure", "payment_timeout"]:
        delay = settings.network_failure_delay
        category = "technical_issue"
    elif reason_clean in ["insufficient_funds", "limit_exceeded"]:
        delay = settings.insufficient_funds_delay
        category = "payment_issue"
    elif reason_clean == "bank_declined":
        delay = settings.bank_declined_delay
        category = "bank_policy"
    elif is_perm:
        delay = 0.0
        category = "card_issue" if "card" in reason_clean else "customer_intent"
    else:
        delay = settings.default_retry_delay
        category = "general_failure"

    return {
        "failure_reason": reason_clean,
        "failure_category": category,
        "is_permanent": is_perm,
        "is_temporary": is_temp,
        "retry_eligible": not is_perm,
        "recommended_delay_hours": delay,
    }


# ─── Tool 5: calculate_customer_value ─────────────────────────────────────────

def calculate_customer_value(customer_id: str) -> Dict[str, Any]:
    """
    Calculates customer monetization tier and VIP classification.
    """
    cust_info = get_customer_history(customer_id)
    clv = cust_info["lifetime_value"]
    seg = cust_info["segment"]
    is_vip = clv >= settings.vip_clv_threshold or seg == "enterprise"

    if clv >= settings.vip_clv_threshold:
        tier_label = "VIP_ENTERPRISE"
    elif clv >= 3000:
        tier_label = "TIER_1_HIGH_VALUE"
    elif clv >= 1000:
        tier_label = "TIER_2_MID_VALUE"
    else:
        tier_label = "TIER_3_ENTRY_VALUE"

    return {
        "customer_id": customer_id,
        "customer_lifetime_value": clv,
        "segment": seg,
        "tier_label": tier_label,
        "is_vip": is_vip,
    }


# ─── Tool 6: get_recovery_policy ──────────────────────────────────────────────

def get_recovery_policy() -> Dict[str, Any]:
    """
    Returns active recovery thresholds, limits, and spacing rules.
    """
    return {
        "high_confidence_threshold": settings.high_confidence_threshold,
        "outreach_threshold": settings.outreach_threshold,
        "max_retry_attempts": settings.max_retry_attempts,
        "min_retry_delay_hours": settings.min_retry_delay_hours,
        "high_value_payment_threshold": settings.high_value_payment_threshold,
        "vip_clv_threshold": settings.vip_clv_threshold,
        "retry_delays_hours": {
            "network_failure": settings.network_failure_delay,
            "temporary_gateway_failure": settings.temporary_gateway_failure_delay,
            "payment_timeout": settings.payment_timeout_delay,
            "insufficient_funds": settings.insufficient_funds_delay,
            "bank_declined": settings.bank_declined_delay,
            "default": settings.default_retry_delay,
        },
    }


# ─── Tool 7: recommend_recovery_strategy ──────────────────────────────────────

def recommend_recovery_strategy(
    payment: Dict[str, Any],
    customer: Optional[Dict[str, Any]] = None,
    recovery_probability: Optional[float] = None,
    context: Optional[Dict[str, Any]] = None,
) -> DecisionResponse:
    """
    Executes deterministic Decision Engine to formulate the recovery strategy.
    """
    return decide_recovery_strategy(
        payment=payment,
        customer=customer,
        recovery_probability=recovery_probability,
        context=context,
    )


# ─── Tool 8: generate_customer_message ────────────────────────────────────────

def generate_customer_message(
    decision: DecisionResponse,
    customer: Dict[str, Any],
    payment: Dict[str, Any],
    channel: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Produces safe, personalized customer communication without exposing internal ML data.
    """
    return generate_customer_recovery_message(
        decision=decision,
        customer_name=customer.get("name", "Customer"),
        amount=float(payment.get("amount", 0.0)),
        failure_reason=payment.get("failure_reason", ""),
        payment_id=payment.get("payment_id", decision.payment_id),
        channel=channel or decision.channel_recommendation,
    )
