"""
RecoverAI — Financial & Recovery Analytics Page (Clean & Modern)
================================================================
Empirical recovery yield, strategy conversion benchmarks, failure diagnostics, and cohort trends.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st

from dashboard.api_client import api_client
from dashboard.components import (
    create_failure_analysis_chart,
    create_recovery_trend_chart,
    create_revenue_breakdown_donut,
    create_segment_recovery_chart,
    create_strategy_performance_chart,
)


def render_analytics_page() -> None:
    """Renders the comprehensive financial and recovery analytics dashboard."""
    st.title("📊 Financial & Recovery Analytics")
    st.caption("Empirical recovery yield, strategy conversion benchmarks, failure diagnostics, and cohort trends.")

    # 1. Fetch Overview & Analytics Datasets
    with st.spinner("Compiling recovery analytics..."):
        overview, o_err = api_client.get_overview()
        strategy_data, s_err = api_client.get_strategy_analytics()
        failure_data, f_err = api_client.get_failure_analytics()
        segment_data, seg_err = api_client.get_segment_analytics()

    if o_err or not overview:
        st.error(f"Failed to load analytics: {o_err}")
        if st.button("🔄 Retry Connection", key="analytics_retry_btn"):
            st.cache_data.clear()
            st.rerun()
        return


    # 2. Executive Analytics Metrics
    total_val = float(overview.get("failed_payment_value", 0.0) or 0.0)
    rec_val = float(overview.get("recovered_value", 0.0) or 0.0)
    unrec_val = float(overview.get("unrecovered_value", 0.0) or 0.0)
    rate = float(overview.get("recovery_rate", 0.0) or 0.0)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(label="Total Involuntary At-Risk", value=f"₹{total_val:,.2f}")
    with m2:
        st.metric(label="AI Recovered Value", value=f"₹{rec_val:,.2f}", delta=f"{rate * 100:.1f}% Yield")
    with m3:
        st.metric(label="Net Unrecovered Volume", value=f"₹{unrec_val:,.2f}", delta_color="inverse")
    with m4:
        st.metric(label="Total Failed Transactions", value=f"{overview.get('total_failed_payments', 0):,}")

    st.divider()

    # 3. Time-Series Trends & Revenue Breakdown
    st.markdown("### 📈 Recovery Velocity Trends & Revenue Breakdown")
    t_toggle_col, _ = st.columns([1, 3])
    with t_toggle_col:
        trend_interval = st.radio("Trend Interval", ["monthly", "daily"], horizontal=True, key="analytics_trend_interval")

    c_left, c_right = st.columns([2, 1])
    with c_left:
        trends_data, _ = api_client.get_trends(interval=trend_interval)
        st.plotly_chart(create_recovery_trend_chart(trends_data), use_container_width=True)
    with c_right:
        st.plotly_chart(create_revenue_breakdown_donut(overview), use_container_width=True)

    st.divider()

    # 4. Strategy & Failure Mode Deep Dives
    st.markdown("### 🎯 Decision Strategy & Failure Classification")
    c_strat, c_fail = st.columns(2)
    with c_strat:
        st.plotly_chart(create_strategy_performance_chart(strategy_data), use_container_width=True)
    with c_fail:
        st.plotly_chart(create_failure_analysis_chart(failure_data), use_container_width=True)

    st.divider()

    # 5. Customer Segment Yield
    st.markdown("### 👥 Customer Segment Recovery Analysis")
    st.plotly_chart(create_segment_recovery_chart(segment_data), use_container_width=True)


if __name__ in ("__main__", "__mp_main__"):
    render_analytics_page()
