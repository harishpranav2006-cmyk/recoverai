"""
RecoverAI — Revenue Analytics & Recovery Metrics (High-Performance SQL Aggregations)
===================================================================================
Calculates empirical revenue recovery performance, strategy efficiency,
and failure-category breakdown using ultra-fast database-level aggregations.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models.customer import Customer
from backend.models.payment import Payment
from backend.models.recovery import RecoveryCase, RecoveryOutcome, RetryAttempt

logger = logging.getLogger(__name__)


def calculate_recovery_metrics(db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Computes overall revenue recovery aggregates across all failed payments
    using fast database-level aggregations (O(1) execution time).
    """
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        # Total failed payments volume & count in a single query
        failed_agg = db.query(
            func.count(Payment.id).label("cnt"),
            func.coalesce(func.sum(Payment.amount), 0.0).label("val"),
        ).filter(Payment.payment_success == False).first()

        total_failed_count = failed_agg.cnt if failed_agg else 0
        total_failed_value = float(failed_agg.val if failed_agg else 0.0)

        # Recovered payments volume & count in a single query
        recovered_agg = db.query(
            func.count(Payment.id).label("cnt"),
            func.coalesce(
                func.sum(
                    case(
                        (Payment.recovered_amount.isnot(None), Payment.recovered_amount),
                        else_=Payment.amount,
                    )
                ),
                0.0,
            ).label("val"),
        ).filter(
            Payment.payment_success == False,
            Payment.recovered_after_failure == True,
        ).first()

        total_recovered_count = recovered_agg.cnt if recovered_agg else 0
        total_recovered_value = float(recovered_agg.val if recovered_agg else 0.0)

        unrecovered_value = max(0.0, total_failed_value - total_recovered_value)
        recovery_rate = (total_recovered_value / total_failed_value) if total_failed_value > 0 else 0.0

        # Counts
        total_customers = db.query(func.count(Customer.id)).scalar() or 0
        total_payments = db.query(func.count(Payment.id)).scalar() or 0
        active_cases = db.query(func.count(RecoveryCase.id)).filter(RecoveryCase.status.in_(["pending", "in_progress"])).scalar() or 0
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
    Computes recovered volume and success rate segmented by recovery strategy
    using fast SQL GROUP BY.
    """
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        rows = db.query(
            RecoveryOutcome.strategy_used,
            func.count(RecoveryOutcome.id).label("total_cases"),
            func.sum(case((RecoveryOutcome.success == True, 1), else_=0)).label("successful_recoveries"),
            func.coalesce(
                func.sum(case((RecoveryOutcome.success == True, RecoveryOutcome.amount_recovered), else_=0.0)),
                0.0,
            ).label("recovered_value"),
        ).group_by(RecoveryOutcome.strategy_used).all()

        results = []
        for r in rows:
            strat = r[0] or "UNKNOWN"
            tot = r[1] or 0
            succ = r[2] or 0
            val = float(r[3] or 0.0)
            rate = (succ / tot) if tot > 0 else 0.0
            results.append({
                "strategy": strat,
                "total_cases": tot,
                "successful_recoveries": succ,
                "recovered_value": round(val, 2),
                "success_rate": round(rate, 4),
                "success_rate_percentage": f"{rate * 100:.1f}%",
            })

        return sorted(results, key=lambda x: x["recovered_value"], reverse=True)
    finally:
        if own_session and db:
            db.close()


def calculate_recovery_by_failure_type(db: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Computes recovery rates grouped by initial failure reason using fast SQL GROUP BY.
    """
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        rows = db.query(
            Payment.failure_reason,
            func.count(Payment.id).label("total_failed"),
            func.sum(case((Payment.recovered_after_failure == True, 1), else_=0)).label("recovered_count"),
            func.coalesce(func.sum(Payment.amount), 0.0).label("total_amount"),
            func.coalesce(
                func.sum(
                    case(
                        (Payment.recovered_after_failure == True, func.coalesce(Payment.recovered_amount, Payment.amount)),
                        else_=0.0,
                    )
                ),
                0.0,
            ).label("recovered_amount"),
        ).filter(Payment.payment_success == False).group_by(Payment.failure_reason).all()

        results = []
        for r in rows:
            reason = r[0] or "unknown"
            tot = r[1] or 0
            rec = r[2] or 0
            tot_amt = float(r[3] or 0.0)
            rec_amt = float(r[4] or 0.0)
            rate = (rec / tot) if tot > 0 else 0.0
            results.append({
                "failure_reason": reason,
                "total_failed": tot,
                "recovered_count": rec,
                "total_amount": round(tot_amt, 2),
                "recovered_amount": round(rec_amt, 2),
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
    Computes recovery metrics grouped by customer segment using SQL JOIN + GROUP BY.
    """
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        rows = db.query(
            Customer.segment,
            func.count(Payment.id).label("total_failed_payments"),
            func.coalesce(func.sum(Payment.amount), 0.0).label("total_failed_value"),
            func.coalesce(
                func.sum(
                    case(
                        (Payment.recovered_after_failure == True, func.coalesce(Payment.recovered_amount, Payment.amount)),
                        else_=0.0,
                    )
                ),
                0.0,
            ).label("recovered_value"),
        ).join(Customer, Payment.customer_id == Customer.id).filter(
            Payment.payment_success == False
        ).group_by(Customer.segment).all()

        output = []
        for r in rows:
            seg = r[0] or "unknown"
            tot_payments = r[1] or 0
            tot_val = float(r[2] or 0.0)
            rec_val = float(r[3] or 0.0)
            rate = (rec_val / tot_val) if tot_val > 0 else 0.0
            output.append({
                "segment": seg,
                "total_failed_payments": tot_payments,
                "total_failed_value": round(tot_val, 2),
                "recovered_value": round(rec_val, 2),
                "recovery_rate": round(rate, 4),
                "recovery_rate_percentage": f"{rate * 100:.1f}%",
            })

        return sorted(output, key=lambda x: x["recovered_value"], reverse=True)
    finally:
        if own_session and db:
            db.close()
