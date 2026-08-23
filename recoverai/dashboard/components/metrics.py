"""
RecoverAI — Metric Cards Component (Premium Glassmorphism Dark Fintech)
=======================================================================
Renders high-impact fintech KPI cards with glassmorphism, gradient accents,
animated counters, and hover-lift micro-animations.
"""

from __future__ import annotations

from typing import Optional
import streamlit as st

from dashboard.config import COLORS


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
) -> None:
    """Renders a premium glassmorphism KPI card with gradient accent strip and hover animation."""
    accent = accent_color or card_border
    icon_html = (
        f"""<div style="background: {icon_bg}; width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; margin-right: 10px; flex-shrink: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">{icon}</div>"""
        if icon
        else ""
    )
    badge_html = (
        f"""<span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; padding: 3px 10px; border-radius: 9999px; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.3px; white-space: nowrap;">{badge}</span>"""
        if badge
        else ""
    )
    subtitle_html = (
        f"""<div style="color: {COLORS['text_secondary']}; font-size: 0.78rem; font-weight: 500; margin-top: 6px;">{subtitle}</div>"""
        if subtitle
        else ""
    )

    card_html = f"""
    <div style="
        background: {COLORS['glass_bg_strong']};
        border: 1px solid {card_border};
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.03);
        backdrop-filter: blur(12px);
        margin-bottom: 14px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fadeInUp 0.5s ease-out both;
        cursor: default;
    " onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 8px 28px rgba(0,0,0,0.6), 0 0 20px {accent}30';" 
       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 16px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.03)';">
        <!-- Gradient Accent Strip -->
        <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, {accent}, {accent}80, transparent); border-radius: 14px 14px 0 0;"></div>
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="display: flex; align-items: center;">
                {icon_html}
                <span style="color: {COLORS['text_secondary']}; font-size: 0.74rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;">
                    {title}
                </span>
            </div>
            {badge_html}
        </div>
        <div style="color: #FFFFFF; font-size: 1.9rem; font-weight: 800; line-height: 1.1; letter-spacing: -0.5px; animation: countUp 0.6s ease-out both;">
            {value}
        </div>
        {subtitle_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_overview_kpis(overview: dict) -> None:
    """Renders the top 8 overview KPI cards across 2 rows of 4 columns with staggered animations."""
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card(
            title="TOTAL PAYMENTS",
            value=f"{overview.get('total_payments', 0):,}",
            subtitle=f"{overview.get('total_customers', 0):,} Customers Tracked",
            icon="💳",
            icon_bg="#1E3A8A",
            card_border="#2563EB",
            badge="50K Records",
            badge_bg="#1E3A8A",
            badge_color="#93C5FD",
            badge_border="#3B82F6",
        )
    with c2:
        render_kpi_card(
            title="FAILED VOLUME",
            value=format_inr(overview.get("failed_payment_value", 0.0)),
            subtitle=f"{overview.get('total_failed_payments', overview.get('failed_payments', 0)):,} Failed Transactions",
            icon="⚠️",
            icon_bg="#78350F",
            card_border="#D97706",
            badge="Involuntary Churn",
            badge_bg="#450A0A",
            badge_color="#F87171",
            badge_border="#EF4444",
        )
    with c3:
        render_kpi_card(
            title="RECOVERED REVENUE",
            value=format_inr(overview.get("recovered_value", 0.0)),
            subtitle=f"{overview.get('recovered_payments', 0):,} Payments Rescued",
            icon="💎",
            icon_bg="#064E3B",
            card_border="#059669",
            badge="Rescued by AI",
            badge_bg="#064E3B",
            badge_color="#4ADE80",
            badge_border="#22C55E",
        )
    with c4:
        rate = overview.get("recovery_rate", 0.0)
        render_kpi_card(
            title="RECOVERY RATE",
            value=format_percent(rate),
            subtitle="Empirical Recovery Success",
            icon="📈",
            icon_bg="#581C87",
            card_border="#9333EA",
            badge="High Yield",
            badge_bg="#064E3B",
            badge_color="#4ADE80",
            badge_border="#22C55E",
        )

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        render_kpi_card(
            title="UNRECOVERED VOLUME",
            value=format_inr(overview.get("unrecovered_value", 0.0)),
            subtitle="Permanent / Suppressed Loss",
            icon="🛡️",
            icon_bg="#4C0519",
            card_border="#BE123C",
            badge="Suppressed Risk",
            badge_bg="#4C0519",
            badge_color="#FB7185",
            badge_border="#F43F5E",
        )
    with r2:
        render_kpi_card(
            title="ACTIVE RECOVERY CASES",
            value=f"{overview.get('active_recovery_cases', 0):,}",
            subtitle="Queue Processing In Flight",
            icon="⏳",
            icon_bg="#78350F",
            card_border="#D97706",
            badge="Active",
            badge_bg="#451A03",
            badge_color="#FBBF24",
            badge_border="#F59E0B",
        )
    with r3:
        retries = overview.get("retry_attempts", overview.get("total_retry_attempts", 0))
        render_kpi_card(
            title="RETRY INVOCATIONS",
            value=f"{retries:,}",
            subtitle="Precision-Scheduled Attempts",
            icon="⚡",
            icon_bg="#1E3A8A",
            card_border="#2563EB",
            badge="Smart Retries",
            badge_bg="#1E3A8A",
            badge_color="#93C5FD",
            badge_border="#3B82F6",
        )
    with r4:
        render_kpi_card(
            title="MODEL PRECISION (TIER 1)",
            value="71.02%",
            subtitle="Measured on Chronological Split",
            icon="🎯",
            icon_bg="#581C87",
            card_border="#9333EA",
            badge="Calibrated ML",
            badge_bg="#581C87",
            badge_color="#C084FC",
            badge_border="#A855F7",
        )
