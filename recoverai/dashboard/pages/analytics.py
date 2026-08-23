"""
RecoverAI — Financial & Recovery Analytics Page (Fintech High-Contrast Dark Theme)
==================================================================================
Deep analytical insights, strategy comparisons, failure diagnostics, and time-series trends.
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
    format_inr,
    format_percent,
    render_kpi_card,
)
from dashboard.config import COLORS


def render_analytics_page() -> None:
    """Renders the comprehensive financial and recovery analytics dashboard."""
    st.markdown(
        f"""
        <div style="margin-bottom: 24px; animation: fadeInUp 0.5s ease-out both;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 900; letter-spacing: -0.5px;">
                <span style="background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-size: 200% 200%; animation: gradientShift 4s ease-in-out infinite;">
                    📊 Financial & Recovery Analytics
                </span>
            </h1>
            <div style="color: {COLORS['text_dim']}; font-size: 0.92rem; font-weight: 500; margin-top: 6px;">
                Empirical recovery yield, strategy conversion benchmarks, failure diagnostics, and cohort trends.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Controls & Filters
    with st.expander("🔍 **Analytics Controls & Filters**", expanded=True):
        an_c1, an_c2, an_c3 = st.columns([2, 2, 1])
        with an_c1:
            interval_choice = st.radio("Time-Series Interval", ["monthly", "daily"], horizontal=True, key="an_interval")
        with an_c2:
            st.markdown("<div style='padding-top: 24px; color: #E5E7EB; font-size: 0.85rem;'>Live database aggregation over 50,000 payments</div>", unsafe_allow_html=True)
        with an_c3:
            if st.button("🔄 Refresh Analytics", key="an_refresh_btn", use_container_width=True):
                st.rerun()

    # 2. Fetch Real-Time Analytics
    with st.spinner("Aggregating recovery metrics from database..."):
        overview, o_err = api_client.get_overview()
        strategy_data, _ = api_client.get_strategy_analytics()
        failure_data, _ = api_client.get_failure_analytics()
        segment_data, _ = api_client.get_segment_analytics()
        trends_data, _ = api_client.get_trends(interval=interval_choice)

    if o_err or not overview:
        st.error(f"Failed to load analytics: {o_err}")
        return

    # 3. Executive KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            title="TOTAL FAILED VOLUME",
            value=format_inr(overview.get("failed_payment_value", 0.0)),
            subtitle=f"{overview.get('total_failed_payments', overview.get('failed_payments', 0)):,} Involuntary Failures",
            icon="⚠️",
            icon_bg="#78350F",
            card_border="#D97706",
            badge="Leakage",
            badge_bg="#450A0A",
            badge_color="#F87171",
            badge_border="#EF4444",
        )
    with k2:
        render_kpi_card(
            title="RESCUED ARR",
            value=format_inr(overview.get("recovered_value", 0.0)),
            subtitle=f"{overview.get('recovered_payments', 0):,} Payments Rescued",
            icon="💎",
            icon_bg="#064E3B",
            card_border="#059669",
            badge="Net Yield",
            badge_bg="#064E3B",
            badge_color="#4ADE80",
            badge_border="#22C55E",
        )
    with k3:
        render_kpi_card(
            title="NET RECOVERY RATE",
            value=format_percent(overview.get("recovery_rate", 0.0)),
            subtitle="Overall Financial Yield",
            icon="📈",
            icon_bg="#581C87",
            card_border="#9333EA",
            badge="Empirical",
            badge_bg="#064E3B",
            badge_color="#4ADE80",
            badge_border="#22C55E",
        )
    with k4:
        render_kpi_card(
            title="SUPPRESSED LOSS",
            value=format_inr(overview.get("unrecovered_value", 0.0)),
            subtitle="Permanently Ineligible",
            icon="🛑",
            icon_bg="#4C0519",
            card_border="#BE123C",
            badge="Protected",
            badge_bg="#4C0519",
            badge_color="#FB7185",
            badge_border="#F43F5E",
        )

    st.markdown("---")

    # 4. Time-Series Trends & Revenue Breakdown
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px; animation: fadeInUp 0.5s ease-out both;">
            <span style="font-size: 1.25rem;">📈</span>
            <span style="font-weight: 800; font-size: 1.15rem; color: #FFFFFF;">Recovery Velocity Trends & Revenue Breakdown</span>
            <div style="flex: 1; height: 1px; background: linear-gradient(90deg, {COLORS['primary']}40, transparent); margin-left: 8px;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_trend, c_donut = st.columns([2, 1])
    with c_trend:
        st.plotly_chart(create_recovery_trend_chart(trends_data), use_container_width=True)
    with c_donut:
        st.plotly_chart(create_revenue_breakdown_donut(overview), use_container_width=True)

    st.markdown("---")

    # 5. Strategy & Failure Breakdowns
    c_strat, c_fail = st.columns(2)
    with c_strat:
        st.plotly_chart(create_strategy_performance_chart(strategy_data), use_container_width=True)
    with c_fail:
        st.plotly_chart(create_failure_analysis_chart(failure_data), use_container_width=True)

    st.markdown("---")

    # 6. Customer Segment Yield
    st.plotly_chart(create_segment_recovery_chart(segment_data), use_container_width=True)

    # 7. Aggregated Data Export Table
    if strategy_data:
        with st.expander("📄 **Strategy Performance Data Export**", expanded=False):
            strat_df = pd.DataFrame(strategy_data)
            st.dataframe(strat_df, use_container_width=True, hide_index=True)
            csv_data = strat_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Strategy Performance CSV",
                data=csv_data,
                file_name="recoverai_strategy_performance.csv",
                mime="text/csv",
                key="btn_download_strat_csv",
            )


if __name__ in ("__main__", "__mp_main__"):
    render_analytics_page()
