"""
RecoverAI — Decision History Endpoints (v1)
===========================================
Provides paginated history and inspection of all autonomous and policy decisions.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import AgentDecision
from backend.schemas.common import PaginatedResponse
from backend.schemas.decision import DecisionResponse

router = APIRouter(prefix="/decisions", tags=["Decision History"])


@router.get("", response_model=PaginatedResponse[DecisionResponse], summary="List AI Decisions")
def list_decisions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    payment_id: Optional[str] = Query(None, description="Filter by payment ID"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    tier: Optional[str] = Query(None, description="Filter by recovery tier"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    human_review_required: Optional[bool] = Query(None, description="Filter by human review flag"),
    date_from: Optional[datetime] = Query(None, description="Filter decisions after timestamp"),
    date_to: Optional[datetime] = Query(None, description="Filter decisions before timestamp"),
    sort_by: str = Query("timestamp", description="Field to sort by (timestamp, recovery_probability)"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[DecisionResponse]:
    """
    Returns paginated historical decision engine audit records.
    """
    query = db.query(AgentDecision)

    if payment_id:
        query = query.filter(AgentDecision.payment_id == payment_id)

    if customer_id:
        from backend.models import Payment
        query = query.join(Payment, AgentDecision.payment_id == Payment.id).filter(Payment.customer_id == customer_id)

    if tier:
        t = tier.upper()
        if t == "HIGH_CONFIDENCE":
            query = query.filter(AgentDecision.recovery_probability >= 0.65)
        elif t == "ACTIONABLE_OUTREACH":
            query = query.filter(AgentDecision.recovery_probability >= 0.45, AgentDecision.recovery_probability < 0.65)
        elif t == "SUPPRESS_OR_ESCALATE":
            query = query.filter(AgentDecision.recovery_probability < 0.45)

    if strategy:
        query = query.filter(AgentDecision.recommended_action.ilike(f"%{strategy}%"))

    if human_review_required is not None:
        query = query.filter(AgentDecision.human_escalation_required == human_review_required)

    if date_from:
        query = query.filter(AgentDecision.timestamp >= date_from)

    if date_to:
        query = query.filter(AgentDecision.timestamp <= date_to)

    allowed_sorts = {
        "timestamp": AgentDecision.timestamp,
        "recovery_probability": AgentDecision.recovery_probability,
        "id": AgentDecision.id,
    }
    sort_col = allowed_sorts.get(sort_by, AgentDecision.timestamp)
    query = query.order_by(sort_col.asc() if sort_order.lower() == "asc" else sort_col.desc())

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()

    items = [
        DecisionResponse(
            payment_id=d.payment_id,
            recovery_probability=d.recovery_probability,
            tier=d.tier,
            strategy=d.strategy,
            recommended_action=d.recommended_action,
            delay_hours=d.delay_hours,
            reason_codes=d.reason_codes or [],
            customer_message_required=d.customer_message_required,
            human_review_required=d.human_review_required,
            explanation=d.explanation or "",
        )
        for d in records
    ]

    return PaginatedResponse[DecisionResponse](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/{decision_id}", response_model=DecisionResponse, summary="Get Decision Details")
def get_decision_details(decision_id: str, db: Session = Depends(get_db)) -> DecisionResponse:
    """
    Retrieves a specific decision record by its primary key ID.
    """
    decision = db.query(AgentDecision).filter(AgentDecision.id == decision_id).first()
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision with ID '{decision_id}' not found.",
        )

    return DecisionResponse(
        payment_id=decision.payment_id,
        recovery_probability=decision.recovery_probability,
        tier=decision.tier,
        strategy=decision.strategy,
        recommended_action=decision.recommended_action,
        delay_hours=decision.delay_hours,
        reason_codes=decision.reason_codes or [],
        customer_message_required=decision.customer_message_required,
        human_review_required=decision.human_review_required,
        explanation=decision.explanation or "",
    )
