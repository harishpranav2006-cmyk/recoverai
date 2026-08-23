"""
RecoverAI — Metric Cards Component (Clean Native Streamlit)
============================================================
Uses Streamlit's native st.metric() and st.columns() for reliable,
clean, user-friendly KPI display that always renders correctly.
"""

from __future__ import annotations

from typing import Any, Optional
import streamlit as st


def format_inr(val: Optional[float]) -> str:
    """Formats a number into Indian Rupee notation (₹XX,XX,XXX.XX or Cr/L)."""
    if val is None:
        return "₹0.00"
    if abs(val) >= 10_000_000:
        return f"₹{val / 10_000_000:,.2f} Cr"
    if abs(val) >= 100_000:
        return f"₹{val / 100_000:,.2f} L"
    return f"₹{val:,.2f}"


def format_percent(val: Optional[float]) -> str:
    """Formats a decimal into a clean percentage string."""
    if val is None:
        return "0.0%"
    return f"{val * 100:.1f}%" if val <= 1.0 else f"{val:.1f}%"


def render_kpi_card(
    title: str,
    value: str,
    subtitle: Optional[str] = None,
    badge: Optional[str] = None,
    badge_bg: str = "#1E3A8A",
    badge_color: str = "#93C5FD",
    badge_border: str = "#2563EB",
    icon: Optional[str] = None,
    icon_bg: str = "#1F2937",
    card_border: str = "#1F2937",
    accent_color: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Renders a single clean KPI metric card."""
    label_text = f"{icon} {title}" if icon else title
    st.metric(
        label=label_text,
        value=value,
        delta=subtitle or badge,
    )


def render_overview_kpis(overview: dict) -> None:
    """Renders the top 8 overview KPI cards using native Streamlit metrics — clean and reliable."""

    # Row 1: Core Financial KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            label="💳 Total Payments",
            value=f"{overview.get('total_payments', 0):,}",
            delta=f"{overview.get('total_customers', 0):,} Customers",
        )
    with c2:
        st.metric(
            label="⚠️ Failed Volume",
            value=format_inr(overview.get("failed_payment_value", 0.0)),
            delta=f"{overview.get('total_failed_payments', overview.get('failed_payments', 0)):,} Failed",
            delta_color="inverse",
        )
    with c3:
        st.metric(
            label="💎 Recovered Revenue",
            value=format_inr(overview.get("recovered_value", 0.0)),
            delta=f"{overview.get('recovered_payments', 0):,} Rescued",
        )
    with c4:
        rate = overview.get("recovery_rate", 0.0)
        st.metric(
            label="📈 Recovery Rate",
            value=format_percent(rate),
            delta="High Yield" if rate > 0.4 else "Building",
        )

    # Row 2: Operational KPIs
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.metric(
            label="🛡️ Unrecovered Volume",
            value=format_inr(overview.get("unrecovered_value", 0.0)),
            delta="Suppressed / Permanent",
            delta_color="off",
        )
    with r2:
        st.metric(
            label="⏳ Active Recovery Cases",
            value=f"{overview.get('active_recovery_cases', 0):,}",
            delta="Queue Processing",
            delta_color="off",
        )
    with r3:
        retries = overview.get("retry_attempts", overview.get("total_retry_attempts", 0))
        st.metric(
            label="⚡ Retry Invocations",
            value=f"{retries:,}",
            delta="Smart Retries",
            delta_color="off",
        )
    with r4:
        st.metric(
            label="🎯 Model Precision (Tier 1)",
            value="71.02%",
            delta="Calibrated ML",
        )
