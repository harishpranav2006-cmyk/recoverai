"""
RecoverAI — Autonomous Retry Execution Service
==============================================
Orchestrates simulated payment retries under strict Decision Engine safety constraints,
state machine validation, and full audit trail persistence.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import SessionLocal
from backend.models.payment import Payment
from backend.models.recovery import RecoveryCase, RecoveryAction, RecoveryOutcome, RetryAttempt
from backend.schemas.decision import DecisionResponse, RecommendedAction, RecoveryStrategy
from services.state_machine import PaymentState, PaymentStateMachine
from simulator.payment_simulator import simulate_payment_attempt

logger = logging.getLogger(__name__)


class RetryExecutionError(Exception):
    """Raised when a retry execution is blocked by safety or policy constraints."""
    pass


def execute_retry(
    payment_id: str,
    decision: Optional[DecisionResponse] = None,
    delay_hours: Optional[float] = None,
    is_method_updated: bool = False,
    force_fresh: bool = False,
    seed: Optional[int] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Executes a simulated payment retry attempt with full safety checks and DB persistence.
    """
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        # Step 1: Validate Payment exists
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise KeyError(f"Payment with ID '{payment_id}' not found.")

        # Step 2: Validate Payment is not already resolved/recovered
        if not force_fresh and (payment.payment_success or payment.recovered_after_failure):
            raise RetryExecutionError(f"Payment '{payment_id}' has already succeeded or been recovered. Retries blocked.")

        # Step 3: Hard Safety Check — Retry Limit
        if payment.retry_count >= settings.max_retry_attempts:
            raise RetryExecutionError(
                f"Payment '{payment_id}' has exhausted maximum retry attempts ({payment.retry_count}/{settings.max_retry_attempts})."
            )

        # Step 4: Validate Policy Permission
        if decision:
            if decision.strategy == RecoveryStrategy.SUPPRESSION or decision.recommended_action == RecommendedAction.APPLY_GRACE_PERIOD_AND_SUPPRESS:
                raise RetryExecutionError(f"Decision Engine suppressed retries for payment '{payment_id}'.")
            if payment.failure_reason in ["expired_card", "invalid_payment_details"] and not is_method_updated:
                raise RetryExecutionError(
                    f"Permanent failure '{payment.failure_reason}' cannot be blindly retried without payment method update."
                )

        # Step 5: Determine Execution Context
        attempt_number = payment.retry_count + 1
        effective_delay = delay_hours if delay_hours is not None else (decision.delay_hours if decision and decision.delay_hours is not None else settings.min_retry_delay_hours)
        rec_prob = decision.recovery_probability if decision else (payment.simulated_recovery_probability or 0.50)

        # Step 6: State Machine Transition (FAILED -> RETRY_SCHEDULED -> RETRYING)
        PaymentStateMachine.transition_payment(PaymentState.FAILED, PaymentState.RETRY_SCHEDULED, payment_id)
        PaymentStateMachine.transition_payment(PaymentState.RETRY_SCHEDULED, PaymentState.RETRYING, payment_id)

        # Step 7: Call Payment Gateway Simulator
        sim_result = simulate_payment_attempt(
            payment_id=payment.id,
            amount=float(payment.amount),
            failure_reason=payment.failure_reason or "",
            recovery_probability=float(rec_prob),
            attempt_number=attempt_number,
            delay_hours=float(effective_delay),
            payment_method=payment.payment_method or "card",
            is_method_updated=is_method_updated,
            seed=seed,
        )

        now = datetime.now(timezone.utc)
        case_id = f"CASE_{payment.id}"
        case = db.query(RecoveryCase).filter(RecoveryCase.payment_id == payment.id).first()
        if not case:
            case = RecoveryCase(
                id=case_id,
                payment_id=payment.id,
                customer_id=payment.customer_id,
                status="in_progress",
                created_at=now,
                updated_at=now,
                recovery_probability=float(rec_prob),
                recommended_action=decision.recommended_action if decision else "RETRY_AFTER_DELAY",
                amount=float(payment.amount),
            )
            db.add(case)
            db.flush()

        # Step 8: Persist RetryAttempt
        retry_record = RetryAttempt(
            payment_id=payment.id,
            case_id=case.id,
            attempt_number=attempt_number,
            timestamp=now,
            success=sim_result["success"],
            failure_reason=None if sim_result["success"] else sim_result["gateway_message"],
            simulated=True,
        )
        db.add(retry_record)

        # Step 9: Persist RecoveryAction
        action_record = RecoveryAction(
            case_id=case.id,
            action_type="SIMULATED_RETRY",
            timestamp=now,
            details=f"Attempt {attempt_number} with delay {effective_delay}h. Gateway Code: {sim_result['gateway_response_code']}",
            result="SUCCESS" if sim_result["success"] else "FAILED",
        )
        db.add(action_record)

        # Step 10: Process Outcome & State Transition
        if sim_result["success"]:
            PaymentStateMachine.transition_payment(PaymentState.RETRYING, PaymentState.RECOVERED, payment_id)
            payment.recovered_after_failure = True
            payment.recovered_amount = float(payment.amount)
            payment.recovery_time_hours = float(effective_delay)

            case.status = "recovered"
            case.recovered_amount = float(payment.amount)
            case.updated_at = now

            outcome_record = RecoveryOutcome(
                case_id=case.id,
                success=True,
                amount_recovered=float(payment.amount),
                recovery_time_hours=float(effective_delay),
                timestamp=now,
                strategy_used=decision.strategy if decision else "SMART_RETRY",
            )
            db.add(outcome_record)
            final_status = "RECOVERED"
        else:
            payment.retry_count = attempt_number
            if payment.retry_count >= settings.max_retry_attempts:
                PaymentStateMachine.transition_payment(PaymentState.RETRYING, PaymentState.PERMANENTLY_FAILED, payment_id)
                case.status = "failed"
                final_status = "PERMANENTLY_FAILED"
            else:
                PaymentStateMachine.transition_payment(PaymentState.RETRYING, PaymentState.FAILED, payment_id)
                case.status = "in_progress"
                final_status = "FAILED_RETRY"
            case.updated_at = now

        db.commit()

        return {
            "payment_id": payment_id,
            "attempt_number": attempt_number,
            "success": sim_result["success"],
            "status": final_status,
            "amount": float(payment.amount),
            "recovered_amount": float(payment.amount) if sim_result["success"] else 0.0,
            "gateway_response": {
                "code": sim_result["gateway_response_code"],
                "message": sim_result["gateway_message"],
            },
            "delay_hours": effective_delay,
            "timestamp": now.isoformat(),
            "simulated": True,
        }

    except Exception as e:
        if own_session and db:
            db.rollback()
        raise e
    finally:
        if own_session and db:
            db.close()
