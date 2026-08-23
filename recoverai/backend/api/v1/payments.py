"""
RecoverAI — Payment Endpoints (v1)
==================================
Provides payment listings, detailed lifecycle lookups, and chronological event timelines.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from backend.database import get_db
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
from backend.schemas.common import PaginatedResponse
from backend.schemas.payment import (
    PaymentDetailResponse,
    PaymentResponse,
    PaymentTimelineResponse,
    TimelineEvent,
)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("", response_model=PaginatedResponse[PaymentResponse], summary="List Payments")
def list_payments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: success, failed, recovered"),
    failure_reason: Optional[str] = Query(None, description="Filter by failure reason"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method (card, upi, netbanking, wallet)"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum amount"),
    date_from: Optional[datetime] = Query(None, description="Filter payments from this timestamp"),
    date_to: Optional[datetime] = Query(None, description="Filter payments up to this timestamp"),
    sort_by: str = Query("timestamp", description="Field to sort by (timestamp, amount, retry_count)"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PaymentResponse]:
    """
    Returns paginated payments with extensive filtering for failure investigations.
    """
    query = db.query(Payment)

    # Status filter
    if status_filter:
        s = status_filter.lower()
        if s == "success":
            query = query.filter(Payment.payment_success == True)
        elif s == "recovered":
            query = query.filter(Payment.recovered_after_failure == True)
        elif s == "failed":
            query = query.filter(Payment.payment_success == False, Payment.recovered_after_failure == False)

    if failure_reason:
        query = query.filter(Payment.failure_reason == failure_reason)

    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)

    if customer_id:
        query = query.filter(Payment.customer_id == customer_id)

    if min_amount is not None:
        query = query.filter(Payment.amount >= min_amount)

    if max_amount is not None:
        query = query.filter(Payment.amount <= max_amount)

    if date_from:
        query = query.filter(Payment.timestamp >= date_from)

    if date_to:
        query = query.filter(Payment.timestamp <= date_to)

    # Validated sorting
    allowed_sort_fields = {
        "timestamp": Payment.timestamp,
        "amount": Payment.amount,
        "retry_count": Payment.retry_count,
        "id": Payment.id,
    }
    sort_col = allowed_sort_fields.get(sort_by, Payment.timestamp)
    query = query.order_by(sort_col.asc() if sort_order.lower() == "asc" else sort_col.desc())

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    offset = (page - 1) * page_size
    payments = query.offset(offset).limit(page_size).all()

    items = [
        PaymentResponse(
            id=p.id,
            customer_id=p.customer_id,
            timestamp=p.timestamp,
            amount=float(p.amount),
            currency=p.currency,
            payment_method=p.payment_method,
            payment_method_type=p.payment_method_type,
            device_type=p.device_type,
            is_subscription=p.is_subscription,
            subscription_type=p.subscription_type,
            payment_success=p.payment_success,
            failure_reason=p.failure_reason,
            failure_category=p.failure_category,
            retry_count=p.retry_count,
            recovered_after_failure=p.recovered_after_failure,
            recovered_amount=float(p.recovered_amount) if p.recovered_amount is not None else None,
            recovery_time_hours=float(p.recovery_time_hours) if p.recovery_time_hours is not None else None,
            demo_scenario=p.demo_scenario,
        )
        for p in payments
    ]

    return PaginatedResponse[PaymentResponse](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/{payment_id}", response_model=PaymentDetailResponse, summary="Get Payment Details")
def get_payment_details(payment_id: str, db: Session = Depends(get_db)) -> PaymentDetailResponse:
    """
    Retrieves full payment record, customer summary, recovery case, and latest AI prediction/decision.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID '{payment_id}' not found.",
        )

    customer = db.query(Customer).filter(Customer.id == payment.customer_id).first()
    recovery_case = db.query(RecoveryCase).filter(RecoveryCase.payment_id == payment_id).first()
    latest_pred = (
        db.query(ModelPrediction)
        .filter(ModelPrediction.payment_id == payment_id)
        .order_by(ModelPrediction.timestamp.desc())
        .first()
    )
    latest_dec = (
        db.query(AgentDecision)
        .filter(AgentDecision.payment_id == payment_id)
        .order_by(AgentDecision.timestamp.desc())
        .first()
    )
    latest_outcome = None
    if recovery_case:
        latest_outcome = (
            db.query(RecoveryOutcome)
            .filter(RecoveryOutcome.case_id == recovery_case.id)
            .first()
        )

    return PaymentDetailResponse(
        id=payment.id,
        customer_id=payment.customer_id,
        customer_name=customer.name if customer else None,
        customer_email=customer.email if customer else None,
        customer_segment=customer.segment if customer else None,
        customer_lifetime_value=float(payment.customer_lifetime_value),
        timestamp=payment.timestamp,
        amount=float(payment.amount),
        currency=payment.currency,
        payment_method=payment.payment_method,
        payment_method_type=payment.payment_method_type,
        device_type=payment.device_type,
        is_subscription=payment.is_subscription,
        subscription_type=payment.subscription_type,
        subscription_age_days=payment.subscription_age_days,
        payment_success=payment.payment_success,
        failure_reason=payment.failure_reason,
        failure_category=payment.failure_category,
        failure_temporary=payment.failure_temporary,
        retry_count=payment.retry_count,
        recovered_after_failure=payment.recovered_after_failure,
        recovered_amount=float(payment.recovered_amount) if payment.recovered_amount is not None else None,
        recovery_time_hours=float(payment.recovery_time_hours) if payment.recovery_time_hours is not None else None,
        demo_scenario=payment.demo_scenario,
        latest_prediction={
            "recovery_probability": float(latest_pred.recovery_probability),
            "model_version": latest_pred.model_version,
            "timestamp": latest_pred.timestamp.isoformat(),
        } if latest_pred else None,
        latest_decision={
            "tier": latest_dec.tier,
            "strategy": latest_dec.strategy,
            "recommended_action": latest_dec.recommended_action,
            "explanation": latest_dec.explanation,
            "timestamp": latest_dec.timestamp.isoformat(),
        } if latest_dec else None,
        latest_outcome={
            "status": latest_outcome.status,
            "amount_recovered": float(latest_outcome.amount_recovered),
            "strategy_used": latest_outcome.strategy_used,
        } if latest_outcome else None,
        recovery_case_status=recovery_case.status if recovery_case else None,
    )


@router.get("/{payment_id}/timeline", response_model=PaymentTimelineResponse, summary="Get Payment Event Timeline")
def get_payment_timeline(payment_id: str, db: Session = Depends(get_db)) -> PaymentTimelineResponse:
    """
    Returns chronological timeline events representing the full lifecycle of the payment and recovery actions.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID '{payment_id}' not found.",
        )

    events: List[TimelineEvent] = []

    # 1. Initial Payment Event
    if payment.payment_success:
        events.append(
            TimelineEvent(
                event_type="PAYMENT_SUCCESS",
                timestamp=payment.timestamp,
                title="Payment Completed Successfully",
                description=f"Transaction of ₹{payment.amount:,.2f} via {payment.payment_method.upper()} succeeded.",
                status="SUCCESS",
            )
        )
    else:
        events.append(
            TimelineEvent(
                event_type="PAYMENT_FAILURE",
                timestamp=payment.timestamp,
                title="Initial Payment Failed",
                description=f"Payment of ₹{payment.amount:,.2f} failed due to '{payment.failure_reason}'.",
                status="FAILED",
                metadata={"failure_reason": payment.failure_reason, "category": payment.failure_category},
            )
        )

    # 2. Predictions
    predictions = (
        db.query(ModelPrediction)
        .filter(ModelPrediction.payment_id == payment_id)
        .order_by(ModelPrediction.timestamp.asc())
        .all()
    )
    for pred in predictions:
        events.append(
            TimelineEvent(
                event_type="ML_PREDICTION",
                timestamp=pred.timestamp,
                title="ML Recovery Assessment",
                description=f"Predicted recovery probability: {float(pred.recovery_probability):.1%}.",
                status="COMPLETED",
                metadata={"model_version": pred.model_version, "probability": float(pred.recovery_probability)},
            )
        )

    # 3. Agent Decisions
    decisions = (
        db.query(AgentDecision)
        .filter(AgentDecision.payment_id == payment_id)
        .order_by(AgentDecision.timestamp.asc())
        .all()
    )
    for dec in decisions:
        events.append(
            TimelineEvent(
                event_type="AGENT_DECISION",
                timestamp=dec.timestamp,
                title=f"AI Strategy: {dec.strategy}",
                description=dec.explanation or f"Assigned Tier: {dec.tier}. Action: {dec.recommended_action}.",
                status="DECIDED",
                metadata={"tier": dec.tier, "strategy": dec.strategy, "action": dec.recommended_action},
            )
        )

    # 4. Recovery Actions
    actions = (
        db.query(RecoveryAction)
        .join(RecoveryCase, RecoveryAction.case_id == RecoveryCase.id)
        .filter(RecoveryCase.payment_id == payment_id)
        .order_by(RecoveryAction.timestamp.asc())
        .all()
    )
    for act in actions:
        events.append(
            TimelineEvent(
                event_type="RECOVERY_ACTION",
                timestamp=act.timestamp,
                title=f"Recovery Action: {act.action_type}",
                description=act.details or f"Action {act.action_type} executed (result: {act.result or 'executed'}).",
                status=act.result or "EXECUTED",
                metadata={"action_type": act.action_type, "case_id": act.case_id},
            )
        )

    # 5. Customer Messages
    messages = (
        db.query(Message)
        .join(RecoveryCase, Message.case_id == RecoveryCase.id)
        .filter(RecoveryCase.payment_id == payment_id)
        .order_by(Message.timestamp.asc())
        .all()
    )
    for msg in messages:
        snippet = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
        events.append(
            TimelineEvent(
                event_type="OUTREACH_DISPATCH",
                timestamp=msg.timestamp,
                title=f"Customer Outreach ({msg.channel.upper()})",
                description=snippet,
                status="SENT",
                metadata={"channel": msg.channel, "tone": msg.tone},
            )
        )

    # 6. Retry Attempts
    retries = (
        db.query(RetryAttempt)
        .filter(RetryAttempt.payment_id == payment_id)
        .order_by(RetryAttempt.timestamp.asc())
        .all()
    )
    for r in retries:
        status_str = "SUCCESS" if r.success else "FAILED"
        desc_str = f"Retry attempt #{r.attempt_number} completed: {status_str}."
        if not r.success and r.failure_reason:
            desc_str += f" Reason: {r.failure_reason}."
        events.append(
            TimelineEvent(
                event_type="RETRY_ATTEMPT",
                timestamp=r.timestamp,
                title=f"Payment Retry Attempt #{r.attempt_number}",
                description=desc_str,
                status=status_str,
                metadata={"attempt_number": r.attempt_number, "simulated": r.simulated},
            )
        )

    # 6. Final Recovery Outcome
    if payment.recovered_after_failure:
        events.append(
            TimelineEvent(
                event_type="RECOVERY_OUTCOME",
                timestamp=payment.timestamp,
                title="Payment Successfully Recovered",
                description=f"Recovered ₹{payment.recovered_amount or payment.amount:,.2f} after {payment.recovery_time_hours or 0.0:.1f} hours.",
                status="RECOVERED",
                metadata={"recovered_amount": float(payment.recovered_amount or payment.amount)},
            )
        )

    # Sort all events chronologically
    events.sort(key=lambda e: e.timestamp)

    current_status = "RECOVERED" if payment.recovered_after_failure else ("SUCCESS" if payment.payment_success else "UNRECOVERED")

    return PaymentTimelineResponse(
        payment_id=payment.id,
        customer_id=payment.customer_id,
        amount=float(payment.amount),
        current_status=current_status,
        total_events=len(events),
        events=events,
    )
