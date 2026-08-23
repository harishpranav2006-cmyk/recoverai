"""
RecoverAI — Revenue Analytics & Recovery Metrics
================================================
Calculates empirical revenue recovery performance, strategy efficiency,
and failure-category breakdown from actual simulated records.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models.customer import Customer
from backend.models.payment import Payment
from backend.models.recovery import RecoveryCase, RecoveryOutcome, RetryAttempt

logger = logging.getLogger(__name__)


def calculate_recovery_metrics(db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Computes overall revenue recovery aggregates across all failed payments.
    """
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        # Total failed payments volume
        failed_payments = db.query(Payment).filter(Payment.payment_success == False).all()
        total_failed_count = len(failed_payments)
        total_failed_value = sum(float(p.amount) for p in failed_payments)

        # Recovered payments (where recovered_after_failure is True)
        recovered_payments = [p for p in failed_payments if p.recovered_after_failure]
        total_recovered_count = len(recovered_payments)
        total_recovered_value = sum(float(p.recovered_amount or p.amount) for p in recovered_payments)

        unrecovered_value = max(0.0, total_failed_value - total_recovered_value)
        recovery_rate = (total_recovered_value / total_failed_value) if total_failed_value > 0 else 0.0

        # Total customers and payments
        total_customers = db.query(func.count(Customer.id)).scalar() or 0
        total_payments = db.query(func.count(Payment.id)).scalar() or 0
        active_cases = db.query(func.count(RecoveryCase.id)).filter(RecoveryCase.status.in_(["pending", "in_progress"])).scalar() or 0

        # Total retry attempts recorded
        total_retry_attempts = db.query(func.count(RetryAttempt.id)).scalar() or 0

        return {
            "total_customers": total_customers,
            "total_payments": total_payments,
            "total_failed_payments": total_failed_count,
            "failed_payment_value": round(total_failed_value, 2),
            "recovered_payments": total_recovered_count,
            "recovered_value": round(total_recovered_value, 2),
            "unrecovered_value": round(unrecovered_value, 2),
            "recovery_rate": round(recovery_rate, 4),
            "recovery_rate_percentage": f"{recovery_rate * 100:.2f}%",
            "retry_attempts": total_retry_attempts,
            "active_recovery_cases": active_cases,
            "currency": "INR",
        }
    finally:
        if own_session and db:
            db.close()


def calculate_recovery_by_strategy(db: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Computes recovered volume and success rate segmented by recovery strategy.
    """
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        outcomes = db.query(RecoveryOutcome).all()
        strategy_stats: Dict[str, Dict[str, Any]] = {}

        for out in outcomes:
            strat = out.strategy_used or "UNKNOWN"
            if strat not in strategy_stats:
                strategy_stats[strat] = {
                    "strategy": strat,
                    "total_cases": 0,
                    "successful_recoveries": 0,
                    "recovered_value": 0.0,
                }
            strategy_stats[strat]["total_cases"] += 1
            if out.success:
                strategy_stats[strat]["successful_recoveries"] += 1
                strategy_stats[strat]["recovered_value"] += float(out.amount_recovered)

        results = []
        for strat, data in strategy_stats.items():
            tot = data["total_cases"]
            succ = data["successful_recoveries"]
            rate = (succ / tot) if tot > 0 else 0.0
            results.append({
                "strategy": strat,
                "total_cases": tot,
                "successful_recoveries": succ,
                "recovered_value": round(data["recovered_value"], 2),
                "success_rate": round(rate, 4),
                "success_rate_percentage": f"{rate * 100:.1f}%",
            })

        return sorted(results, key=lambda x: x["recovered_value"], reverse=True)
    finally:
        if own_session and db:
            db.close()


def calculate_recovery_by_failure_type(db: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Computes recovery rates grouped by initial failure reason.
    """
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        failed_payments = db.query(Payment).filter(Payment.payment_success == False).all()
        reason_stats: Dict[str, Dict[str, Any]] = {}

        for p in failed_payments:
            reason = p.failure_reason or "unknown"
            if reason not in reason_stats:
                reason_stats[reason] = {
                    "failure_reason": reason,
                    "total_failed": 0,
                    "recovered_count": 0,
                    "total_amount": 0.0,
                    "recovered_amount": 0.0,
                }
            reason_stats[reason]["total_failed"] += 1
            reason_stats[reason]["total_amount"] += float(p.amount)
            if p.recovered_after_failure:
                reason_stats[reason]["recovered_count"] += 1
                reason_stats[reason]["recovered_amount"] += float(p.recovered_amount or p.amount)

        results = []
        for reason, data in reason_stats.items():
            tot = data["total_failed"]
            rec = data["recovered_count"]
            rate = (rec / tot) if tot > 0 else 0.0
            results.append({
                "failure_reason": reason,
                "total_failed": tot,
                "recovered_count": rec,
                "total_amount": round(data["total_amount"], 2),
                "recovered_amount": round(data["recovered_amount"], 2),
                "recovery_rate": round(rate, 4),
                "recovery_rate_percentage": f"{rate * 100:.1f}%",
            })

        return sorted(results, key=lambda x: x["total_failed"], reverse=True)
    finally:
        if own_session and db:
            db.close()


calculate_recovery_by_failure_reason = calculate_recovery_by_failure_type


def calculate_recovery_by_segment(db: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Computes recovery metrics grouped by customer segment.
    """
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        customers = {c.id: c.segment for c in db.query(Customer).all()}
        failed_payments = db.query(Payment).filter(Payment.payment_success == False).all()

        segment_stats: Dict[str, Dict[str, Any]] = {}
        for p in failed_payments:
            seg = customers.get(p.customer_id, "unknown")
            if seg not in segment_stats:
                segment_stats[seg] = {
                    "segment": seg,
                    "total_failed_payments": 0,
                    "total_failed_value": 0.0,
                    "recovered_value": 0.0,
                }
            segment_stats[seg]["total_failed_payments"] += 1
            segment_stats[seg]["total_failed_value"] += float(p.amount)
            if p.recovered_after_failure:
                segment_stats[seg]["recovered_value"] += float(p.recovered_amount or p.amount)

        output = []
        for seg, data in segment_stats.items():
            tot = data["total_failed_value"]
            rec = data["recovered_value"]
            rate = (rec / tot) if tot > 0 else 0.0
            output.append({
                "segment": seg,
                "total_failed_payments": data["total_failed_payments"],
                "total_failed_value": round(tot, 2),
                "recovered_value": round(rec, 2),
                "recovery_rate": round(rate, 4),
                "recovery_rate_percentage": f"{rate * 100:.1f}%",
            })

        return sorted(output, key=lambda x: x["recovered_value"], reverse=True)
    finally:
        if own_session and db:
            db.close()
