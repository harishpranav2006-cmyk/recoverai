"""
RecoverAI — Autonomous Recovery Workflow Orchestrator
=====================================================
Integrates ML prediction, AI Agent orchestration, deterministic Decision Engine,
payment gateway simulation, customer outreach simulation, and revenue impact accounting.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import SessionLocal
from backend.models.payment import Payment
from backend.models.recovery import Message, RecoveryAction, RecoveryCase, RecoveryOutcome
from agent.agent import run_recovery_agent
from services.retry_service import execute_retry
from services.state_machine import CaseState, PaymentState, PaymentStateMachine
from simulator.outreach_simulator import simulate_customer_outreach

logger = logging.getLogger(__name__)


def run_recovery_workflow(
    payment_id: str,
    channel_override: Optional[str] = None,
    force_fresh: bool = False,
    seed: Optional[int] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Executes the complete autonomous end-to-end recovery lifecycle for a failed payment.
    """
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        # 1. Load Payment and Check Idempotency
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise KeyError(f"Payment with ID '{payment_id}' not found in database.")

        now = datetime.now(timezone.utc)

        # Idempotency Check: Return existing outcome if already resolved (unless force_fresh is requested)
        if not force_fresh and (payment.recovered_after_failure or payment.payment_success):
            existing_outcome = (
                db.query(RecoveryOutcome)
                .join(RecoveryCase, RecoveryOutcome.case_id == RecoveryCase.id)
                .filter(RecoveryCase.payment_id == payment_id)
                .first()
            )
            strat = existing_outcome.strategy_used if existing_outcome else "ALREADY_RESOLVED"
            rec_val = float(payment.recovered_amount or payment.amount)
            return {
                "payment_id": payment_id,
                "status": "RECOVERED",
                "idempotent": True,
                "decision": {
                    "tier": "HIGH_CONFIDENCE" if payment.payment_success else "SUPPRESS_OR_ESCALATE",
                    "strategy": strat,
                    "recommended_action": "ALREADY_RESOLVED",
                    "delay_hours": 0.0,
                    "recovery_probability": 1.0,
                    "reason_codes": ["PAYMENT_ALREADY_RECOVERED"],
                },
                "action": {
                    "type": "IDEMPOTENT_CACHE",
                    "status": "COMPLETED",
                },
                "outcome": {
                    "status": "RECOVERED",
                    "is_recovered": True,
                    "recovered_amount": rec_val,
                    "unrecovered_amount": 0.0,
                },
                "revenue_impact": {
                    "transaction_amount": float(payment.amount),
                    "recovered_amount": rec_val,
                    "currency": payment.currency,
                },
                "amount": float(payment.amount),
                "recovered_amount": rec_val,
                "strategy_used": strat,
                "message": "Payment is already successfully recovered.",
                "simulated": True,
                "timestamp": now.isoformat(),
            }

        # 2. Run AI Recovery Agent & Decision Engine
        agent_result = run_recovery_agent(payment_id=payment_id, channel_override=channel_override)
        strategy = agent_result["strategy"]
        tier = agent_result["tier"]
        recommended_action = agent_result["recommended_action"]
        delay_hours = agent_result.get("delay_hours") or 0.0

        # Retrieve or Initialize Recovery Case
        case_id = f"CASE_{payment_id}"
        case = db.query(RecoveryCase).filter(RecoveryCase.payment_id == payment_id).first()
        if not case:
            case = RecoveryCase(
                id=case_id,
                payment_id=payment_id,
                customer_id=payment.customer_id,
                status="in_progress",
                created_at=now,
                updated_at=now,
                recovery_probability=agent_result["recovery_probability"],
                recommended_action=recommended_action,
                amount=float(payment.amount),
            )
            db.add(case)
            db.flush()

        action_result: Dict[str, Any] = {}
        outcome_status = "PENDING"
        recovered_amount = 0.0

        # 3. Strategy Execution Route A: SMART_RETRY
        if strategy == "SMART_RETRY" and payment.retry_count < settings.max_retry_attempts:
            retry_res = execute_retry(
                payment_id=payment_id,
                delay_hours=delay_hours,
                force_fresh=force_fresh,
                seed=seed,
                db=db,
            )
            action_result = {
                "type": "SIMULATED_RETRY",
                "attempt_number": retry_res["attempt_number"],
                "status": "EXECUTED",
                "gateway_response": retry_res["gateway_response"],
            }
            if retry_res["success"]:
                outcome_status = "RECOVERED"
                recovered_amount = float(payment.amount)
            else:
                outcome_status = "FAILED_RETRY"

        # 4. Strategy Execution Route B: CUSTOMER_OUTREACH / PAYMENT_METHOD_UPDATE / RETENTION_INCENTIVE
        elif strategy in ["CUSTOMER_OUTREACH", "PAYMENT_METHOD_UPDATE", "RETENTION_INCENTIVE"]:
            msg_content = agent_result.get("customer_message") or "Action needed on your subscription payment."
            channel = agent_result.get("customer_message_channel") or channel_override or "WHATSAPP"

            outreach_res = simulate_customer_outreach(
                payment_id=payment_id,
                customer_id=payment.customer_id,
                channel=channel,
                message=msg_content,
                strategy=strategy,
                customer_clv=float(payment.customer_lifetime_value),
                seed=seed,
            )

            # Persist Message
            msg_record = Message(
                case_id=case.id,
                customer_id=payment.customer_id,
                channel=channel.lower(),
                tone="professional",
                content=msg_content,
                generated_by="agent",
                timestamp=now,
            )
            db.add(msg_record)

            # Persist RecoveryAction
            action_record = RecoveryAction(
                case_id=case.id,
                action_type=f"OUTREACH_{channel.upper()}",
                timestamp=now,
                details=f"Dispatched simulated {channel} message. Action: {outreach_res['customer_action']}",
                result=outreach_res["status"],
            )
            db.add(action_record)
            db.commit()

            action_result = {
                "type": f"SIMULATED_OUTREACH_{channel.upper()}",
                "status": outreach_res["status"],
                "customer_action": outreach_res["customer_action"],
            }

            # If customer took action (clicked payment link / updated card details), simulate payment retry
            if outreach_res["customer_action_taken"]:
                logger.info(f"Customer action simulated for '{payment_id}' ({outreach_res['customer_action']}). Triggering recovery attempt.")
                retry_res = execute_retry(
                    payment_id=payment_id,
                    delay_hours=0.0,
                    is_method_updated=True,
                    force_fresh=force_fresh,
                    seed=seed,
                    db=db,
                )
                action_result["subsequent_payment_attempt"] = retry_res
                if retry_res["success"]:
                    outcome_status = "RECOVERED"
                    recovered_amount = float(payment.amount)
                else:
                    outcome_status = "FAILED_AFTER_OUTREACH"
            else:
                outcome_status = "WAITING_FOR_CUSTOMER"

        # 5. Strategy Execution Route C: SUPPRESSION / HUMAN_REVIEW / VIP_ESCALATION
        else:
            action_record = RecoveryAction(
                case_id=case.id,
                action_type=strategy,
                timestamp=now,
                details=agent_result.get("explanation", "Policy action applied"),
                result="APPLIED",
            )
            db.add(action_record)
            if strategy == "SUPPRESSION":
                PaymentStateMachine.transition_payment(PaymentState.FAILED, PaymentState.SUPPRESSED, payment_id)
                case.status = "suppressed"
                outcome_status = "SUPPRESSED"
            else:
                case.status = "escalated"
                outcome_status = "ESCALATED_FOR_REVIEW"
            db.commit()

            action_result = {
                "type": strategy,
                "status": "APPLIED",
                "human_review_required": agent_result["human_review_required"],
            }

        # 6. Assemble Final Workflow Output
        workflow_output = {
            "payment_id": payment_id,
            "customer_id": payment.customer_id,
            "decision": {
                "tier": tier,
                "strategy": strategy,
                "recommended_action": recommended_action,
                "delay_hours": delay_hours,
                "recovery_probability": agent_result["recovery_probability"],
                "reason_codes": agent_result["reason_codes"],
            },
            "action": action_result,
            "outcome": {
                "status": outcome_status,
                "is_recovered": outcome_status == "RECOVERED",
                "recovered_amount": recovered_amount,
                "unrecovered_amount": float(payment.amount) if outcome_status != "RECOVERED" else 0.0,
            },
            "revenue_impact": {
                "transaction_amount": float(payment.amount),
                "recovered_amount": recovered_amount,
                "currency": payment.currency,
            },
            "simulated": True,
            "timestamp": now.isoformat(),
        }

        return workflow_output

    except Exception as e:
        if own_session and db:
            db.rollback()
        logger.error(f"Recovery workflow failed for payment '{payment_id}': {e}")
        raise e
    finally:
        if own_session and db:
            db.close()
