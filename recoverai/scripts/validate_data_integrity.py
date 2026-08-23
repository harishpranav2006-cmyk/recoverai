"""
RecoverAI — Database & Dataset Data Integrity Validator
======================================================
Performs deep structural, relational, and business rule integrity audits on recoverai.db.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.database import SessionLocal
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


def validate_database_integrity() -> bool:
    print("\n" + "=" * 80)
    print("  RECOVERAI — DATABASE INTEGRITY & CONSISTENCY AUDIT")
    print("=" * 80 + "\n")

    db = SessionLocal()
    errors = []

    try:
        # 1. Total Record Counts
        cust_count = db.query(Customer).count()
        pmt_count = db.query(Payment).count()
        print(f"[COUNT] Total Customers : {cust_count:,} (Expected: 5,000)")
        print(f"[COUNT] Total Payments  : {pmt_count:,} (Expected: 50,000)")

        if cust_count != 5000:
            errors.append(f"Customer count is {cust_count}, expected 5000.")
        if pmt_count != 50000:
            errors.append(f"Payment count is {pmt_count}, expected 50000.")

        # 2. Foreign Key Integrity
        orphaned_pmts = (
            db.query(Payment)
            .outerjoin(Customer, Payment.customer_id == Customer.id)
            .filter(Customer.id == None)
            .count()
        )
        print(f"[RELATION] Orphaned Payments (invalid customer_id): {orphaned_pmts}")
        if orphaned_pmts > 0:
            errors.append(f"Found {orphaned_pmts} payments with invalid customer_id.")

        # 3. Negative Amounts & Anomalies
        neg_pmts = db.query(Payment).filter(Payment.amount < 0).count()
        print(f"[SANITY] Negative Payment Amounts: {neg_pmts}")
        if neg_pmts > 0:
            errors.append(f"Found {neg_pmts} payments with negative amounts.")

        # 4. Failure Reason Integrity
        invalid_fails = (
            db.query(Payment)
            .filter(Payment.payment_success == False, Payment.failure_reason == None)
            .count()
        )
        print(f"[SANITY] Failed Payments missing failure_reason: {invalid_fails}")
        if invalid_fails > 0:
            errors.append(f"Found {invalid_fails} failed payments without failure_reason.")

        # 5. Recovery Case Relational Integrity
        orphaned_cases = (
            db.query(RecoveryCase)
            .outerjoin(Payment, RecoveryCase.payment_id == Payment.id)
            .filter(Payment.id == None)
            .count()
        )
        print(f"[RELATION] Orphaned Recovery Cases: {orphaned_cases}")
        if orphaned_cases > 0:
            errors.append(f"Found {orphaned_cases} orphaned recovery cases.")

        # 6. Retry Attempts Integrity
        orphaned_retries = (
            db.query(RetryAttempt)
            .outerjoin(Payment, RetryAttempt.payment_id == Payment.id)
            .filter(Payment.id == None)
            .count()
        )
        print(f"[RELATION] Orphaned Retry Attempts: {orphaned_retries}")
        if orphaned_retries > 0:
            errors.append(f"Found {orphaned_retries} orphaned retry attempts.")

        # 7. Decisions Integrity
        orphaned_decisions = (
            db.query(AgentDecision)
            .outerjoin(Payment, AgentDecision.payment_id == Payment.id)
            .filter(Payment.id == None)
            .count()
        )
        print(f"[RELATION] Orphaned Agent Decisions: {orphaned_decisions}")
        if orphaned_decisions > 0:
            errors.append(f"Found {orphaned_decisions} orphaned agent decisions.")

        print("\n" + "-" * 80)
        if errors:
            print(f"❌ INTEGRITY AUDIT FAILED WITH {len(errors)} ERRORS:")
            for e in errors:
                print(f"  • {e}")
            return False
        else:
            print("✅ COMPLETE DATA INTEGRITY & RELATIONAL CONSISTENCY VERIFIED (0 ERRORS)")
            print("-" * 80 + "\n")
            return True

    finally:
        db.close()


if __name__ == "__main__":
    success = validate_database_integrity()
    if not success:
        sys.exit(1)
