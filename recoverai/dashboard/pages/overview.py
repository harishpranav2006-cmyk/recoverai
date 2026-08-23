"""
RecoverAI — Executive Overview Page (Premium Glassmorphism Dark Theme)
=====================================================================
Animated hero header, pipeline stepper, executive KPI dashboard,
interactive scenario testing sandbox, and core recovery charts.
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
from dashboard.config import COLORS

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
    """Renders the premium executive overview dashboard."""

    # 1. Animated Hero Header with gradient text
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px; flex-wrap: wrap; gap: 12px; animation: fadeInUp 0.5s ease-out both;">
            <div>
                <h1 style="margin: 0; font-size: 2.2rem; font-weight: 900; letter-spacing: -0.5px; line-height: 1.2;">
                    <span style="background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-size: 200% 200%; animation: gradientShift 4s ease-in-out infinite;">
                        Executive Overview
                    </span>
                </h1>
                <div style="color: {COLORS['text_dim']}; font-size: 0.92rem; font-weight: 500; margin-top: 6px;">
                    Autonomous Involuntary Churn Prevention & Revenue Recovery System
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="background: {COLORS['success_bg']}; color: #4ADE80; border: 1px solid #05966960; padding: 5px 14px; border-radius: 9999px; font-size: 0.78rem; font-weight: 700; display: flex; align-items: center; gap: 6px; backdrop-filter: blur(8px);">
                    <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #4ADE80; box-shadow: 0 0 8px #4ADE80; animation: pulseGreen 2s ease-in-out infinite;"></span>
                    Live Telemetry (50K Records)
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    # 4. Executive KPI Cards (2x4 Grid)
    render_overview_kpis(overview)

    # 5. Quick Action Navigation Bar
    st.markdown(
        f"""
        <div style="margin: 14px 0 6px 0; font-size: 0.78rem; font-weight: 700; color: {COLORS['text_dim']}; text-transform: uppercase; letter-spacing: 1px;">
            Quick Navigation
        </div>
        """,
        unsafe_allow_html=True,
    )
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
        if st.button("📊 Financial Analytics", use_container_width=True):
            from dashboard.app import navigate_to
            navigate_to("Analytics")
    with d5:
        if st.button("🤖 AI Decision Audit", use_container_width=True):
            from dashboard.app import navigate_to
            navigate_to("AI Decisions")

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # 6. Scenario Sandbox
    with st.container():
        st.markdown(
            f"""
            <div style="background: {COLORS['glass_bg_strong']}; border: 1px solid {COLORS['border']}; border-radius: 14px; padding: 18px 22px; margin-bottom: 20px; box-shadow: 0 4px 16px rgba(0,0,0,0.5); backdrop-filter: blur(12px); animation: fadeInUp 0.6s ease-out both; position: relative; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: {COLORS['gradient_primary']};"></div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF; margin-bottom: 4px;">
                    ⚡ Quick Autonomous Recovery Sandbox
                </div>
                <div style="font-size: 0.85rem; color: {COLORS['text_dim']};">
                    Test end-to-end recovery decisions across standard failure archetypes: ML inference → policy routing → simulated retry.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        sc_col1, sc_col2 = st.columns([3, 1])
        with sc_col1:
            scenario_options = ["ALL_7_SCENARIOS (Run Complete Benchmark Batch)"] + [
                f"{k}: {v['description']}" for k, v in DEMO_SCENARIOS_CATALOG.items()
            ]
            selected_scenario_str = st.selectbox("Select Scenario to Test", scenario_options, index=0, label_visibility="collapsed")
        with sc_col2:
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
                    badge_color = "#22C55E" if is_rec else ("#F59E0B" if outcome_status == "WAITING_FOR_CUSTOMER" else "#EF4444")

                    st.markdown(
                        f"""
                        <div style="background: {badge_color}10; border: 1.5px solid {badge_color}60; border-radius: 12px; padding: 16px 20px; margin-top: 10px; backdrop-filter: blur(8px); animation: fadeInUp 0.4s ease-out both;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <span style="font-size: 1.05rem; font-weight: 800; color: {badge_color};">
                                    {'✅ PAYMENT RECOVERED' if is_rec else f'⚠️ STATUS: {outcome_status}'}
                                </span>
                                <span style="background: {badge_color}; color: #000000; padding: 2px 10px; border-radius: 9999px; font-weight: 800; font-size: 0.74rem;">SIMULATED</span>
                            </div>
                            <div style="font-size: 0.88rem; color: #FFFFFF; line-height: 1.6;">
                                <b>Payment ID:</b> <code>{target_pid}</code> &nbsp;|&nbsp;
                                <b>Policy Tier:</b> <b style="color: #60A5FA;">{wf_res.get('tier', 'N/A')}</b> &nbsp;|&nbsp;
                                <b>Strategy:</b> <b>{wf_res.get('strategy', 'N/A')}</b> &nbsp;|&nbsp;
                                <b>Recovered:</b> <b style="color: #4ADE80;">₹{outcome.get('recovered_amount', 0.0):,.2f}</b>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if st.button(f"🔍 Open {target_pid} in Recovery Queue Workstation", key=f"btn_inspect_{target_pid}"):
                        from dashboard.app import navigate_to
                        navigate_to("Recovery Queue", selected_payment_id=target_pid)

    # 7. Recovery Analytics Charts
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px; animation: fadeInUp 0.7s ease-out both;">
            <span style="font-size: 1.25rem;">📊</span>
            <span style="font-weight: 800; font-size: 1.15rem; color: #FFFFFF;">Recovery Analytics & Performance Trends</span>
            <div style="flex: 1; height: 1px; background: linear-gradient(90deg, {COLORS['primary']}40, transparent); margin-left: 8px;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
