"""
Verification script for all 7 dashboard page data contracts and chart rendering.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, r"E:\education\razor pay buildthon\recoverai")

from dashboard.api_client import api_client
from dashboard.components.charts import (
    create_failure_analysis_chart,
    create_probability_gauge_chart,
    create_recovery_trend_chart,
    create_revenue_breakdown_donut,
    create_segment_recovery_chart,
    create_strategy_performance_chart,
)
from dashboard.components.metrics import format_inr, format_percent

def verify_all() -> None:
    print("=== Testing API Client & Chart Generation Contracts ===")
    
    # 1. Overview
    overview, err = api_client.get_overview()
    assert err is None, f"Overview error: {err}"
    assert overview is not None
    donut_fig = create_revenue_breakdown_donut(overview)
    assert donut_fig is not None
    print("✓ Overview & Donut chart OK")

    # 2. Trends
    trends, err = api_client.get_trends(interval="monthly")
    assert err is None, f"Trends error: {err}"
    assert trends is not None
    trend_fig = create_recovery_trend_chart(trends)
    assert trend_fig is not None
    print("✓ Monthly Trends chart OK")

    # 3. Strategy
    strat, err = api_client.get_strategy_analytics()
    assert err is None, f"Strategy error: {err}"
    assert strat is not None
    strat_fig = create_strategy_performance_chart(strat)
    assert strat_fig is not None
    print("✓ Strategy Performance chart OK")

    # 4. Failure
    fail, err = api_client.get_failure_analytics()
    assert err is None, f"Failure error: {err}"
    assert fail is not None
    fail_fig = create_failure_analysis_chart(fail)
    assert fail_fig is not None
    print("✓ Failure Breakdown chart OK")

    # 5. Segment
    seg, err = api_client.get_segment_analytics()
    assert err is None, f"Segment error: {err}"
    assert seg is not None
    seg_fig = create_segment_recovery_chart(seg)
    assert seg_fig is not None
    print("✓ Segment Yield chart OK")

    # 6. Recovery Queue
    queue, err = api_client.get_recovery_queue(limit=10)
    assert err is None, f"Queue error: {err}"
    assert queue is not None
    print(f"✓ Recovery Queue OK ({len(queue)} items)")

    # 7. Payments
    payments, err = api_client.get_payments(page=1, page_size=10)
    assert err is None, f"Payments error: {err}"
    assert payments is not None
    print(f"✓ Payments Directory OK ({payments.get('total')} total)")

    # 8. Customers
    customers, err = api_client.get_customers(page=1, page_size=10)
    assert err is None, f"Customers error: {err}"
    assert customers is not None
    print(f"✓ Customers Intelligence OK ({customers.get('total')} total)")

    # 9. Decisions
    decisions, err = api_client.get_decisions(page=1, page_size=10)
    assert err is None, f"Decisions error: {err}"
    assert decisions is not None
    print(f"✓ AI Decisions Ledger OK ({decisions.get('total')} total)")

    # 10. Health
    health, err = api_client.get_health()
    assert err is None, f"Health error: {err}"
    assert health is not None
    print("✓ System Diagnostics Health OK")

    print("\nALL 7 DASHBOARD DATA PIPELINES VERIFIED 100% OPERATIONAL WITH 0 ERRORS.")

if __name__ == "__main__":
    verify_all()
