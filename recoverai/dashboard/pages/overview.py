"""
RecoverAI — Executive Overview Page (Clean, Professional & Modern)
==================================================================
Clean executive dashboard presenting key financial recovery KPIs,
interactive scenario testing sandbox, and core recovery intelligence charts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st

from dashboard.api_client import api_client
from dashboard.components import (
    create_failure_analysis_chart,
    create_recovery_trend_chart,
    create_revenue_breakdown_donut,
    create_segment_recovery_chart,
    create_strategy_performance_chart,
    render_guided_demo_stepper,
    render_overview_kpis,
)

DEMO_SCENARIOS_CATALOG = {
    "HIGH_RECOVERY_CASE": {
        "payment_id": "P000004",
        "description": "High Confidence (p=0.73) → Smart Retry (Immediate/4h)",
        "icon": "⚡",
    },
    "MEDIUM_RECOVERY_CASE": {
        "payment_id": "P000001",
        "description": "Actionable Outreach (p=0.52) → WhatsApp Customer Link",
        "icon": "💬",
    },
    "LOW_RECOVERY_CASE": {
        "payment_id": "P000002",
        "description": "Low Probability (p=0.28) → Suppress & Prevent Fatigue",
        "icon": "🛑",
    },
    "HIGH_VALUE_CUSTOMER": {
        "payment_id": "P000007",
        "description": "Enterprise VIP (CLV ₹5.2L) → High-Touch Escalation",
        "icon": "👑",
    },
    "MULTIPLE_RETRY_CASE": {
        "payment_id": "P000008",
        "description": "Exhausted Retries (3 Attempts) → Retry Blocked",
        "icon": "⚠️",
    },
    "TEMPORARY_FAILURE_CASE": {
        "payment_id": "P000003",
        "description": "Gateway Network Glitch → Scheduled 4h Delay",
        "icon": "⏳",
    },
    "PERMANENT_FAILURE_CASE": {
        "payment_id": "P000005",
        "description": "Expired Card → Payment Method Update Link",
        "icon": "💳",
    },
}


def render_overview_page() -> None:
    """Renders the executive overview dashboard."""

    # 1. Clean Top Header
    hdr_left, hdr_right = st.columns([3, 1])
    with hdr_left:
        st.title("Executive Overview")
        st.caption("Autonomous Involuntary Churn Prevention & Revenue Recovery System")
    with hdr_right:
        st.markdown("<br>", unsafe_allow_html=True)
        st.success("🟢 Live Telemetry: 50K Records")

    # 2. Fetch Overview Data
    with st.spinner("Loading telemetry..."):
        overview, err = api_client.get_overview()

    if err or not overview:
        st.error(f"⚠️ {err or 'Failed to load overview data from API.'}")
        if st.button("🔄 Retry Connection"):
            st.rerun()
        return

    # 3. Pipeline Stepper (How RecoverAI Works)
    render_guided_demo_stepper()

    # 4. Executive KPI Cards (Native Streamlit Metrics)
    st.markdown("### 📊 Key Performance Indicators")
    render_overview_kpis(overview)

    st.divider()

    # 5. Quick Action Navigation Bar
    st.caption("QUICK ACTIONS")
    d1, d2, d3, d4, d5 = st.columns(5)
    with d1:
        if st.button("🎯 Recovery Queue", use_container_width=True):
            from dashboard.app import navigate_to
            navigate_to("Recovery Queue")
    with d2:
        if st.button("⚠️ Failed Payments", use_container_width=True):
            from dashboard.app import navigate_to
            navigate_to("Payments", payments_status_filter="failed")
    with d3:
        if st.button("👤 Customer CLV", use_container_width=True):
            from dashboard.app import navigate_to
            navigate_to("Customers")
    with d4:
        if st.button("📈 Financial Analytics", use_container_width=True):
            from dashboard.app import navigate_to
            navigate_to("Analytics")
    with d5:
        if st.button("🤖 AI Decision Audit", use_container_width=True):
            from dashboard.app import navigate_to
            navigate_to("AI Decisions")

    st.divider()

    # 6. Scenario Testing Sandbox
    with st.container(border=True):
        st.markdown("### ⚡ Quick Autonomous Recovery Sandbox")
        st.caption("Test end-to-end recovery decisions across standard failure archetypes: ML inference → policy routing → simulated retry.")

        sc_col1, sc_col2 = st.columns([3, 1])
        with sc_col1:
            scenario_options = ["ALL_7_SCENARIOS (Run Complete Benchmark Batch)"] + [
                f"{k}: {v['description']}" for k, v in DEMO_SCENARIOS_CATALOG.items()
            ]
            selected_scenario_str = st.selectbox("Select Scenario to Test", scenario_options, index=0)
        with sc_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            run_scenario_btn = st.button("🚀 Run Recovery Test", type="primary", use_container_width=True)

        if run_scenario_btn:
            if "ALL_7_SCENARIOS" in selected_scenario_str:
                with st.spinner("Simulating benchmark recovery batch..."):
                    demo_res, demo_err = api_client.simulate_demo(seed=42)

                if demo_err or not demo_res:
                    st.error(f"❌ Batch test failed: {demo_err}")
                else:
                    st.success(f"✅ Executed all {demo_res.get('total_scenarios', 7)} benchmark scenarios successfully!")
                    scenarios = demo_res.get("scenarios", [])
                    if scenarios:
                        df_rows = []
                        for s in scenarios:
                            p_id = s.get("payment_id")
                            sc_name = s.get("scenario_name", "").replace("_", " ").title()
                            prob = s.get("recovery_probability", 0.0)
                            strat = s.get("strategy", "N/A")
                            outcome = s.get("outcome_status", "UNKNOWN")
                            rec_amt = s.get("recovered_amount", 0.0)
                            df_rows.append({
                                "Scenario": sc_name,
                                "Payment ID": p_id,
                                "Amount (₹)": f"₹{s.get('amount', 0):,.2f}",
                                "Failure Reason": str(s.get("failure_reason", "")).replace("_", " ").title(),
                                "ML Probability": f"{prob * 100:.1f}%",
                                "Policy Tier": s.get("tier", "").replace("_", " ").title(),
                                "AI Strategy": strat,
                                "Simulated Outcome": outcome,
                                "Recovered (₹)": f"₹{rec_amt:,.2f}",
                            })
                        st.dataframe(pd.DataFrame(df_rows), use_container_width=True, hide_index=True)
            else:
                scenario_key = selected_scenario_str.split(":")[0].strip()
                target_pid = DEMO_SCENARIOS_CATALOG[scenario_key]["payment_id"]

                with st.spinner(f"Testing recovery for {target_pid}..."):
                    wf_res, wf_err = api_client.run_workflow(
                        payment_id=target_pid,
                        channel="whatsapp",
                        force_fresh=True,
                        seed=42,
                    )

                if wf_err or not wf_res:
                    st.error(f"❌ Execution failed for {target_pid}: {wf_err}")
                else:
                    outcome = wf_res.get("simulated_outcome", {})
                    outcome_status = outcome.get("outcome_status", "UNKNOWN")
                    is_rec = outcome_status == "RECOVERED"

                    if is_rec:
                        st.success(
                            f"🎉 **PAYMENT RECOVERED** | Payment: `{target_pid}` | Strategy: **{wf_res.get('strategy', 'N/A')}** | "
                            f"Recovered Amount: **₹{outcome.get('recovered_amount', 0.0):,.2f}**"
                        )
                    else:
                        st.warning(
                            f"⚠️ **STATUS: {outcome_status}** | Payment: `{target_pid}` | Strategy: **{wf_res.get('strategy', 'N/A')}**"
                        )

                    if st.button(f"🔍 Open {target_pid} in Recovery Queue Workstation", key=f"btn_inspect_{target_pid}"):
                        from dashboard.app import navigate_to
                        navigate_to("Recovery Queue", selected_payment_id=target_pid)

    # 7. Recovery Analytics Charts
    st.markdown("### 📈 Recovery Analytics & Performance Trends")

    t_toggle_col, _ = st.columns([1, 3])
    with t_toggle_col:
        trend_interval = st.radio("Trend Interval", ["monthly", "daily"], horizontal=True, key="overview_trend_interval")

    c_left, c_right = st.columns([2, 1])
    with c_left:
        trends_data, _ = api_client.get_trends(interval=trend_interval)
        st.plotly_chart(create_recovery_trend_chart(trends_data), use_container_width=True)
    with c_right:
        st.plotly_chart(create_revenue_breakdown_donut(overview), use_container_width=True)

    c_strat, c_fail = st.columns(2)
    with c_strat:
        strategy_data, _ = api_client.get_strategy_analytics()
        st.plotly_chart(create_strategy_performance_chart(strategy_data), use_container_width=True)
    with c_fail:
        failure_data, _ = api_client.get_failure_analytics()
        st.plotly_chart(create_failure_analysis_chart(failure_data), use_container_width=True)


if __name__ in ("__main__", "__mp_main__"):
    render_overview_page()
