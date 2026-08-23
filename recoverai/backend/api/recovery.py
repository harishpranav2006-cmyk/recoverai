"""
RecoverAI — Recovery & Agent API Routes
=======================================
Provides REST endpoints for analyzing failed payments, executing the AI recovery
agent, and querying decision history and audit trails.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.agent import AgentDecision, ModelPrediction
from backend.models.recovery import RecoveryCase
from agent.agent import run_recovery_agent
from agent.tools import get_payment_details, predict_recovery_probability, recommend_recovery_strategy

router = APIRouter(prefix="/recovery", tags=["Recovery Agent"])


class AnalyzeRequest(BaseModel):
    payment_id: str


class AgentRunRequest(BaseModel):
    payment_id: str
    channel: Optional[str] = None


@router.post("/analyze")
def analyze_payment(req: AnalyzeRequest) -> Dict[str, Any]:
    """
    Directly evaluates a failed payment against ML prediction and Decision Engine policy.
    """
    try:
        payment = get_payment_details(req.payment_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Payment '{req.payment_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving payment: {e}")

    try:
        ml_pred = predict_recovery_probability(payment)
        decision = recommend_recovery_strategy(
            payment=payment,
            recovery_probability=float(ml_pred["recovery_probability"]),
            context={"factors": ml_pred.get("factors", [])},
        )
        return decision.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decision Engine evaluation failed: {e}")


@router.post("/agent/run")
def execute_recovery_agent(req: AgentRunRequest) -> Dict[str, Any]:
    """
    Executes the full Autonomous AI Recovery Agent workflow for the payment.
    """
    try:
        result = run_recovery_agent(payment_id=req.payment_id, channel_override=req.channel)
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Payment '{req.payment_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recovery Agent execution failed: {e}")


@router.get("/{payment_id}/decision")
def get_latest_decision(payment_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Retrieves the most recent persisted decision for a payment.
    """
    decision = (
        db.query(AgentDecision)
        .filter(AgentDecision.payment_id == payment_id)
        .order_by(AgentDecision.timestamp.desc())
        .first()
    )
    if not decision:
        raise HTTPException(status_code=404, detail=f"No decision found for payment '{payment_id}'.")

    return {
        "id": decision.id,
        "case_id": decision.case_id,
        "payment_id": decision.payment_id,
        "recovery_probability": decision.recovery_probability,
        "recommended_action": decision.recommended_action,
        "delay_hours": decision.delay_hours,
        "reasoning": decision.reasoning,
        "customer_message_required": decision.customer_message_required,
        "human_escalation_required": decision.human_escalation_required,
        "timestamp": decision.timestamp.isoformat() if decision.timestamp else None,
    }


@router.get("/{payment_id}/history")
def get_payment_history(payment_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns complete audit trail of agent decisions and ML predictions for a payment.
    """
    decisions = (
        db.query(AgentDecision)
        .filter(AgentDecision.payment_id == payment_id)
        .order_by(AgentDecision.timestamp.asc())
        .all()
    )
    predictions = (
        db.query(ModelPrediction)
        .filter(ModelPrediction.payment_id == payment_id)
        .order_by(ModelPrediction.timestamp.asc())
        .all()
    )

    return {
        "payment_id": payment_id,
        "total_decisions": len(decisions),
        "total_predictions": len(predictions),
        "decisions": [
            {
                "id": d.id,
                "recommended_action": d.recommended_action,
                "recovery_probability": d.recovery_probability,
                "delay_hours": d.delay_hours,
                "reasoning": d.reasoning,
                "timestamp": d.timestamp.isoformat() if d.timestamp else None,
            }
            for d in decisions
        ],
        "predictions": [
            {
                "id": p.id,
                "model_version": p.model_version,
                "probability": p.probability,
                "top_features": json.loads(p.top_features) if p.top_features else [],
                "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            }
            for p in predictions
        ],
    }


@router.post("/{payment_id}/execute")
def execute_approved_recovery_action(payment_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Executes the approved simulated recovery action for a payment under Decision Engine safety rules.
    """
    from services.retry_service import execute_retry, RetryExecutionError
    try:
        result = execute_retry(payment_id=payment_id, db=db)
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Payment '{payment_id}' not found.")
    except RetryExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retry execution failed: {e}")


@router.post("/{payment_id}/simulate")
def simulate_recovery_lifecycle(payment_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Runs the complete simulated recovery workflow: Agent -> Decision -> Action -> Simulated Outcome -> Revenue Impact.
    """
    from services.recovery_workflow import run_recovery_workflow
    try:
        result = run_recovery_workflow(payment_id=payment_id, db=db)
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Payment '{payment_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation workflow failed: {e}")


@router.get("/{payment_id}/outcome")
def get_recovery_outcome(payment_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Retrieves the latest simulated recovery outcome and case details for a payment.
    """
    from backend.models.recovery import RecoveryOutcome, RecoveryCase
    case = db.query(RecoveryCase).filter(RecoveryCase.payment_id == payment_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"No recovery case found for payment '{payment_id}'.")

    outcome = db.query(RecoveryOutcome).filter(RecoveryOutcome.case_id == case.id).order_by(RecoveryOutcome.timestamp.desc()).first()
    return {
        "payment_id": payment_id,
        "case_id": case.id,
        "case_status": case.status,
        "amount": case.amount,
        "recovered_amount": case.recovered_amount or (outcome.amount_recovered if outcome else 0.0),
        "is_recovered": case.status == "recovered" or (outcome.success if outcome else False),
        "strategy_used": outcome.strategy_used if outcome else None,
        "timestamp": outcome.timestamp.isoformat() if outcome and outcome.timestamp else case.updated_at.isoformat(),
        "simulated": True,
    }
