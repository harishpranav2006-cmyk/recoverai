"""
RecoverAI — Autonomous AI Revenue Recovery Demo Runner
======================================================
Executes end-to-end simulated recovery workflows across the 7 representative
failure scenarios and outputs a formatted terminal report.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.database import SessionLocal
from backend.models.payment import Payment
from services.analytics import calculate_recovery_metrics
from services.recovery_workflow import run_recovery_workflow


DEMO_SCENARIO_KEYS = [
    ("HIGH_RECOVERY_CASE", "High Confidence - Smart Retry Eligible"),
    ("MEDIUM_RECOVERY_CASE", "Actionable Outreach - Customer Link"),
    ("LOW_RECOVERY_CASE", "Low Recovery - Suppression & CS Review"),
    ("TEMPORARY_FAILURE_CASE", "Transient Network Failure - 4h Delay"),
    ("PERMANENT_FAILURE_CASE", "Expired Card - Payment Method Update"),
    ("MULTIPLE_RETRY_CASE", "Retry Limit Fatigue - Suppressed"),
    ("HIGH_VALUE_CUSTOMER", "VIP Enterprise - High Touch Escalation"),
]


def run_demo() -> None:
    print("\n" + "=" * 100)
    print("  RECOVERAI — AUTONOMOUS AI REVENUE RECOVERY DEMO")
    print("  Razorpay AI Buildathon — AI Revenue Recovery Track")
    print("=" * 100 + "\n")

    db = SessionLocal()
    results = []

    try:
        for scenario_key, scenario_desc in DEMO_SCENARIO_KEYS:
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

            # Run autonomous recovery workflow (live simulation demo)
            res = run_recovery_workflow(payment_id=payment.id, force_fresh=True, seed=42, db=db)
            results.append({
                "scenario": scenario_desc,
                "payment_id": payment.id,
                "amount": f"₹{payment.amount:,.2f}",
                "failure_reason": payment.failure_reason,
                "prob": f"{res['decision']['recovery_probability']:.1%}",
                "tier": res["decision"]["tier"],
                "strategy": res["decision"]["strategy"],
                "action": res["action"]["type"],
                "outcome": res["outcome"]["status"],
                "recovered": f"₹{res['outcome']['recovered_amount']:,.2f}" if res['outcome']['is_recovered'] else "₹0.00",
            })

    finally:
        db.close()

    # Print Table
    header = (
        f"{'Scenario':<42} | {'Payment':<8} | {'Amount':<10} | {'Failure Reason':<20} | "
        f"{'Prob':<6} | {'Strategy':<22} | {'Outcome':<16} | {'Recovered'}"
    )
    print(header)
    print("-" * len(header))

    for r in results:
        row = (
            f"{r['scenario']:<42} | {r['payment_id']:<8} | {r['amount']:<10} | {r['failure_reason']:<20} | "
            f"{r['prob']:<6} | {r['strategy']:<22} | {r['outcome']:<16} | {r['recovered']}"
        )
        print(row)

    print("-" * len(header))

    # Print Aggregate Analytics
    metrics = calculate_recovery_metrics()
    print("\n" + "=" * 60)
    print("  OVERALL SIMULATED RECOVERY METRICS")
    print("=" * 60)
    print(f"  Total Failed Payments Tracked : {metrics['total_failed_payments']:,}")
    print(f"  Total Failed Payment Volume   : ₹{metrics['failed_payment_value']:,.2f}")
    print(f"  Total Recovered Volume        : ₹{metrics['recovered_value']:,.2f}")
    print(f"  Unrecovered Volume            : ₹{metrics['unrecovered_value']:,.2f}")
    print(f"  Overall Recovery Rate         : {metrics['recovery_rate_percentage']}")
    print(f"  Total Retry Attempts Logged   : {metrics['retry_attempts']:,}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_demo()
