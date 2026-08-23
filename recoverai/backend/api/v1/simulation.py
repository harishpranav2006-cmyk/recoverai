"""
RecoverAI — Simulation Endpoints (v1)
=====================================
Exposes simulated payment retries, complete workflow runs, and demo scenario batch runs.
All endpoints explicitly return `"simulated": true` to guarantee safety isolation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.payment import Payment
from services.recovery_workflow import run_recovery_workflow
from services.retry_service import RetryExecutionError, execute_retry

router = APIRouter(prefix="/simulation", tags=["Payment & Outreach Simulator"])

DEMO_SCENARIO_KEYS = [
    ("HIGH_RECOVERY_CASE", "High Confidence - Smart Retry Eligible"),
    ("MEDIUM_RECOVERY_CASE", "Actionable Outreach - Customer Link"),
    ("LOW_RECOVERY_CASE", "Low Recovery - Suppression & CS Review"),
    ("TEMPORARY_FAILURE_CASE", "Transient Network Failure - 4h Delay"),
    ("PERMANENT_FAILURE_CASE", "Expired Card - Payment Method Update"),
    ("MULTIPLE_RETRY_CASE", "Retry Limit Fatigue - Suppressed"),
    ("HIGH_VALUE_CUSTOMER", "VIP Enterprise - High Touch Escalation"),
]


@router.post("/payment/{payment_id}", summary="Simulate Payment Retry")
def simulate_payment_retry(
    payment_id: str,
    delay_hours: Optional[float] = Query(None, description="Optional retry delay in hours"),
    is_method_updated: bool = Query(False, description="Simulate that customer updated card/UPI details"),
    force_fresh: bool = Query(True, description="Force fresh simulation execution"),
    seed: Optional[int] = Query(42, description="Deterministic pseudo-random seed"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Executes a simulated payment retry attempt through the gateway simulator.
    """
    try:
        result = execute_retry(
            payment_id=payment_id,
            delay_hours=delay_hours,
            is_method_updated=is_method_updated,
            force_fresh=force_fresh,
            seed=seed,
            db=db,
        )
        result["simulated"] = True
        return result
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RetryExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Simulation error: {str(exc)}")


@router.post("/workflow/{payment_id}", summary="Simulate Complete Recovery Workflow")
def simulate_workflow(
    payment_id: str,
    channel: Optional[str] = Query(None, description="Optional channel override (whatsapp, email, sms)"),
    force_fresh: bool = Query(True, description="Force fresh simulation execution"),
    seed: Optional[int] = Query(42, description="Deterministic pseudo-random seed"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Simulates the entire autonomous recovery lifecycle for a failed payment.
    """
    try:
        result = run_recovery_workflow(
            payment_id=payment_id,
            channel_override=channel,
            force_fresh=force_fresh,
            seed=seed,
            db=db,
        )
        result["simulated"] = True
        return result
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Simulation error: {str(exc)}")


@router.post("/demo", summary="Run Configured Demo Scenarios")
def run_demo_simulation(
    seed: Optional[int] = Query(42, description="Deterministic seed"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Executes simulated workflows across all 7 benchmark failure scenarios.
    """
    scenario_results: List[Dict[str, Any]] = []

    for scenario_key, scenario_title in DEMO_SCENARIO_KEYS:
        query = db.query(Payment).filter(Payment.demo_scenario == scenario_key)
        if scenario_key == "MULTIPLE_RETRY_CASE":
            query = query.filter(Payment.retry_count >= 3)
        elif scenario_key == "HIGH_RECOVERY_CASE":
            query = query.filter(Payment.retry_count == 0, Payment.failure_reason == "network_failure")
        elif scenario_key in ["MEDIUM_RECOVERY_CASE", "HIGH_VALUE_CUSTOMER"]:
            query = query.filter(Payment.retry_count < 3)

        payment = query.first()
        if not payment:
            payment = db.query(Payment).filter(Payment.demo_scenario == scenario_key).first()
        if not payment:
            continue

        try:
            workflow_res = run_recovery_workflow(
                payment_id=payment.id,
                force_fresh=True,
                seed=seed,
                db=db,
            )
            scenario_results.append({
                "scenario_key": scenario_key,
                "scenario_title": scenario_title,
                "payment_id": payment.id,
                "amount": float(payment.amount),
                "failure_reason": payment.failure_reason,
                "probability": workflow_res["decision"]["recovery_probability"],
                "tier": workflow_res["decision"]["tier"],
                "strategy": workflow_res["decision"]["strategy"],
                "action": workflow_res["action"]["type"],
                "outcome_status": workflow_res["outcome"]["status"],
                "recovered_amount": workflow_res["outcome"]["recovered_amount"],
                "is_recovered": workflow_res["outcome"]["is_recovered"],
            })
        except Exception as exc:
            scenario_results.append({
                "scenario_key": scenario_key,
                "scenario_title": scenario_title,
                "payment_id": payment.id,
                "error": str(exc),
            })

    return {
        "status": "completed",
        "simulated": True,
        "scenarios_executed": len(scenario_results),
        "results": scenario_results,
    }
