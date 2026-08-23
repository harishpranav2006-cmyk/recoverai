"""
RecoverAI — Recovery & Queue Endpoints (v1)
===========================================
Exposes AI recovery analysis, autonomous agent workflow, outcome inspection, and prioritized recovery queue.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from agent.agent import run_recovery_agent
from agent.decision_engine import evaluate_payment
from agent.tools import get_payment_details as tool_get_payment_details
from backend.config import settings
from backend.database import get_db
from backend.models import (
    AgentDecision,
    Customer,
    ModelPrediction,
    Payment,
    RecoveryCase,
    RecoveryOutcome,
)
from backend.schemas.decision import DecisionResponse
from backend.schemas.recovery import RecoveryOutcomeResponse, RecoveryQueueItem, RecoveryQueueResponse
from ml.predict import predict_payment_recovery
from services.recovery_workflow import run_recovery_workflow
from services.retry_service import RetryExecutionError, execute_retry

router = APIRouter(prefix="/recovery", tags=["Recovery & Decision Core"])


@router.post("/{payment_id}/analyze", response_model=DecisionResponse, summary="Analyze Payment Recovery Policy")
def analyze_payment(payment_id: str) -> DecisionResponse:
    """
    Evaluates ML recovery probability and applies deterministic Decision Engine policy.
    """
    try:
        decision = evaluate_payment(payment_id=payment_id)
        return decision
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Analysis failed: {str(exc)}")


@router.post("/{payment_id}/agent", summary="Run AI Recovery Agent")
def run_agent_for_payment(
    payment_id: str,
    channel: Optional[str] = Query(None, description="Optional channel override (whatsapp, email, sms)"),
) -> Dict[str, Any]:
    """
    Executes the autonomous AI Recovery Agent orchestrating tools, decision engine, messaging, and audit persistence.
    """
    try:
        agent_result = run_recovery_agent(payment_id=payment_id, channel_override=channel)
        return agent_result
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Agent execution failed: {str(exc)}")


@router.post("/{payment_id}/execute", summary="Execute Approved Recovery Action")
def execute_recovery_action(
    payment_id: str,
    delay_hours: Optional[float] = Query(None, description="Optional delay hours override"),
    seed: Optional[int] = Query(42, description="Deterministic seed for simulator"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Executes an approved simulated recovery action governed by Decision Engine safety constraints.
    """
    try:
        result = execute_retry(
            payment_id=payment_id,
            delay_hours=delay_hours,
            seed=seed,
            db=db,
        )
        return result
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RetryExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Execution error: {str(exc)}")


@router.post("/{payment_id}/workflow", summary="Run Complete End-to-End Recovery Workflow")
def run_workflow_for_payment(
    payment_id: str,
    channel: Optional[str] = Query(None, description="Optional channel override"),
    force_fresh: bool = Query(False, description="Bypass idempotency check for live simulation demo"),
    seed: Optional[int] = Query(42, description="Deterministic seed for simulator"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Executes the complete autonomous lifecycle: Agent -> Decision -> Simulation -> Outcome -> Revenue Accounting.
    """
    try:
        result = run_recovery_workflow(
            payment_id=payment_id,
            channel_override=channel,
            force_fresh=force_fresh,
            seed=seed,
            db=db,
        )
        return result
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Workflow failed: {str(exc)}")


@router.get("/{payment_id}/decision", response_model=DecisionResponse, summary="Get Latest AI Decision")
def get_latest_decision(payment_id: str, db: Session = Depends(get_db)) -> DecisionResponse:
    """
    Retrieves the most recent persisted Decision Engine audit record for a payment.
    """
    latest = (
        db.query(AgentDecision)
        .filter(AgentDecision.payment_id == payment_id)
        .order_by(AgentDecision.timestamp.desc())
        .first()
    )
    if not latest:
        # Evaluate dynamically if not stored
        try:
            return evaluate_payment(payment_id=payment_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment '{payment_id}' not found.")

    return DecisionResponse(
        payment_id=latest.payment_id,
        recovery_probability=latest.recovery_probability,
        tier=latest.tier,
        strategy=latest.strategy,
        recommended_action=latest.recommended_action,
        delay_hours=latest.delay_hours,
        reason_codes=latest.reason_codes or [],
        customer_message_required=latest.customer_message_required,
        human_review_required=latest.human_review_required,
        explanation=latest.explanation or "",
    )


@router.get("/{payment_id}/history", summary="Get Payment Recovery History")
def get_recovery_history(payment_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Retrieves the complete audit trail of predictions and AI decisions for a payment.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment '{payment_id}' not found.")

    predictions = (
        db.query(ModelPrediction)
        .filter(ModelPrediction.payment_id == payment_id)
        .order_by(ModelPrediction.timestamp.asc())
        .all()
    )
    decisions = (
        db.query(AgentDecision)
        .filter(AgentDecision.payment_id == payment_id)
        .order_by(AgentDecision.timestamp.asc())
        .all()
    )

    return {
        "payment_id": payment_id,
        "predictions": [
            {
                "id": p.id,
                "recovery_probability": float(p.recovery_probability),
                "model_version": p.model_version,
                "timestamp": p.timestamp.isoformat(),
            }
            for p in predictions
        ],
        "decisions": [
            {
                "id": d.id,
                "tier": d.tier,
                "strategy": d.strategy,
                "recommended_action": d.recommended_action,
                "delay_hours": d.delay_hours,
                "reason_codes": d.reason_codes,
                "explanation": d.explanation,
                "timestamp": d.timestamp.isoformat(),
            }
            for d in decisions
        ],
    }


@router.get("/{payment_id}/outcome", response_model=RecoveryOutcomeResponse, summary="Get Recovery Outcome")
def get_recovery_outcome(payment_id: str, db: Session = Depends(get_db)) -> RecoveryOutcomeResponse:
    """
    Retrieves the simulated recovery outcome for a payment.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment '{payment_id}' not found.")

    case = db.query(RecoveryCase).filter(RecoveryCase.payment_id == payment_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No recovery case found for '{payment_id}'.")

    outcome = db.query(RecoveryOutcome).filter(RecoveryOutcome.case_id == case.id).first()
    if not outcome:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No outcome recorded for case '{case.id}'.")

    return RecoveryOutcomeResponse(
        payment_id=payment.id,
        case_id=case.id,
        case_status=case.status,
        amount=float(case.amount),
        recovered_amount=float(outcome.amount_recovered),
        is_recovered=(outcome.status == "RECOVERED" or payment.recovered_after_failure),
        strategy_used=outcome.strategy_used,
        timestamp=outcome.timestamp.isoformat(),
        simulated=True,
    )


@router.get("/queue", response_model=RecoveryQueueResponse, summary="Get Prioritized Recovery Queue")
def get_recovery_queue(
    tier: Optional[str] = Query(None, description="Filter by tier: HIGH_CONFIDENCE, ACTIONABLE_OUTREACH, SUPPRESS_OR_ESCALATE"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    human_review_required: Optional[bool] = Query(None, description="Filter by human review flag"),
    retry_eligible: Optional[bool] = Query(None, description="Filter by retry eligibility"),
    failure_reason: Optional[str] = Query(None, description="Filter by failure reason"),
    customer_segment: Optional[str] = Query(None, description="Filter by customer segment"),
    limit: int = Query(50, ge=1, le=100, description="Max queue items to return"),
    db: Session = Depends(get_db),
) -> RecoveryQueueResponse:
    """
    Returns failed payments requiring recovery intervention, prioritized by business value and recovery likelihood.
    """
    # Fetch active failed payments
    query = (
        db.query(Payment, Customer)
        .join(Customer, Payment.customer_id == Customer.id)
        .filter(Payment.payment_success == False, Payment.recovered_after_failure == False)
    )

    if failure_reason:
        query = query.filter(Payment.failure_reason == failure_reason)
    if customer_segment:
        query = query.filter(Customer.segment == customer_segment)

    failed_records = query.limit(200).all()

    queue_items: List[RecoveryQueueItem] = []

    for payment, customer in failed_records:
        try:
            decision = evaluate_payment(payment_id=payment.id)
        except Exception:
            continue

        if tier and decision.tier != tier:
            continue
        if strategy and decision.strategy != strategy:
            continue
        if human_review_required is not None and decision.human_review_required != human_review_required:
            continue

        is_eligible = (
            payment.retry_count < settings.max_retry_attempts
            and decision.strategy in ["SMART_RETRY", "PAYMENT_METHOD_UPDATE", "CUSTOMER_OUTREACH"]
        )
        if retry_eligible is not None and is_eligible != retry_eligible:
            continue

        is_vip = float(customer.lifetime_value) >= settings.vip_clv_threshold or customer.segment == "enterprise"

        # Prioritization formula
        vip_multiplier = 1.5 if is_vip else 1.0
        amount_factor = float(payment.amount) / 1000.0
        prob_factor = decision.recovery_probability + 0.1
        eligibility_factor = 1.2 if is_eligible else 0.8
        priority_score = round(vip_multiplier * amount_factor * prob_factor * eligibility_factor, 2)

        queue_items.append(
            RecoveryQueueItem(
                payment_id=payment.id,
                customer_id=customer.id,
                customer_name=customer.name,
                customer_segment=customer.segment,
                customer_lifetime_value=float(customer.lifetime_value),
                is_vip=is_vip,
                amount=float(payment.amount),
                currency=payment.currency,
                failure_reason=payment.failure_reason,
                failure_category=payment.failure_category,
                retry_count=payment.retry_count,
                retry_eligible=is_eligible,
                timestamp=payment.timestamp,
                recovery_probability=decision.recovery_probability,
                tier=decision.tier,
                strategy=decision.strategy,
                recommended_action=decision.recommended_action,
                human_review_required=decision.human_review_required,
                priority_score=priority_score,
            )
        )

    # Sort queue descending by priority_score
    queue_items.sort(key=lambda x: x.priority_score, reverse=True)
    selected_items = queue_items[:limit]

    return RecoveryQueueResponse(
        total_pending=len(queue_items),
        items=selected_items,
    )
