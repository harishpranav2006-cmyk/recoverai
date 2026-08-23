"""
RecoverAI — Data Tables Component (Premium Glassmorphism Dark Theme)
====================================================================
Renders interactive data tables with colored status pills, tier badges,
row hover highlights, and glass-morphism container styling.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st

from dashboard.config import COLORS, TIER_COLORS, STATUS_BADGES
from dashboard.components.metrics import format_inr


def _status_pill(label: str, color: str) -> str:
    """Generates a colored pill HTML badge."""
    return f'<span style="background: {color}18; color: {color}; border: 1px solid {color}40; padding: 3px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.74rem; white-space: nowrap;">{label}</span>'


def _tier_pill(tier: str) -> str:
    """Generates a tier-colored pill badge."""
    tier_upper = str(tier).upper().replace(" ", "_")
    color = TIER_COLORS.get(tier_upper, COLORS["primary"])
    label = tier_upper.replace("_", " ")
    return _status_pill(label, color)


def _payment_status_pill(is_recovered: bool, is_failed: bool) -> str:
    """Generates the appropriate payment status pill."""
    if is_recovered:
        return _status_pill("✅ Recovered", "#22C55E")
    if is_failed:
        return _status_pill("❌ Failed", "#EF4444")
    return _status_pill("✓ Success", "#3B82F6")


def _table_header_row(headers: List[str]) -> str:
    """Generates a glass-styled table header."""
    cells = "".join([
        f'<th style="padding: 10px 14px; text-align: left; color: {COLORS["text_dim"]}; font-weight: 700; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 2px solid {COLORS["border"]}; white-space: nowrap;">{h}</th>'
        for h in headers
    ])
    return f"<tr>{cells}</tr>"


def _render_glass_table(title: str, icon: str, headers: List[str], rows_html: str, count: int = 0, subtitle: str = "") -> None:
    """Wraps a table in a glassmorphism container."""
    count_badge = f'<span style="background: {COLORS["primary"]}18; color: {COLORS["primary_light"]}; border: 1px solid {COLORS["primary"]}40; padding: 2px 10px; border-radius: 9999px; font-size: 0.72rem; font-weight: 700; margin-left: 10px;">{count} records</span>' if count else ""
    
    st.markdown(
        f"""
        <div style="background: {COLORS['glass_bg_strong']}; border: 1px solid {COLORS['border']}; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.5); backdrop-filter: blur(12px); animation: fadeInUp 0.5s ease-out both;">
            <div style="padding: 16px 20px; border-bottom: 1px solid {COLORS['border']};">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.15rem; margin-right: 8px;">{icon}</span>
                    <span style="font-weight: 800; font-size: 1.05rem; color: #FFFFFF;">{title}</span>
                    {count_badge}
                </div>
                {"<div style='font-size: 0.78rem; color: " + COLORS["text_dim"] + "; margin-top: 4px;'>" + subtitle + "</div>" if subtitle else ""}
            </div>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 0.86rem;">
                    <thead style="background: {COLORS['bg_dark']};">
                        {_table_header_row(headers)}
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _table_row(cells: List[str], hover_color: str = "rgba(59, 130, 246, 0.05)") -> str:
    """Generates a single table row with hover highlight."""
    cells_html = "".join([
        f'<td style="padding: 10px 14px; border-bottom: 1px solid {COLORS["border"]}; color: #FFFFFF; white-space: nowrap;">{c}</td>'
        for c in cells
    ])
    return f'<tr style="transition: background 0.15s ease;" onmouseover="this.style.background=\'{hover_color}\'" onmouseout="this.style.background=\'transparent\'">{cells_html}</tr>'


def render_recovery_queue_table(queue: List[Dict[str, Any]], on_select_callback: Optional[str] = None) -> None:
    """Renders the recovery queue with tier pills, probability bars, and hover highlights."""
    if not queue:
        st.info("Recovery queue is empty. Run simulations to populate.")
        return

    headers = ["Payment ID", "Tier", "Strategy", "Probability", "Amount", "Failure", "Delay"]
    rows = ""
    for item in queue[:50]:
        tier = str(item.get("tier", "")).upper().replace(" ", "_")
        strategy = str(item.get("strategy", "")).replace("_", " ").title()
        prob = item.get("recovery_probability", 0)
        prob_pct = prob * 100 if prob <= 1 else prob
        tier_color = TIER_COLORS.get(tier, COLORS["primary"])
        
        prob_bar = f"""
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 60px; height: 5px; background: {COLORS['border']}; border-radius: 99px; overflow: hidden;">
                    <div style="width: {min(prob_pct, 100)}%; height: 100%; background: {tier_color}; border-radius: 99px;"></div>
                </div>
                <span style="font-weight: 700; color: {tier_color}; font-size: 0.82rem;">{prob_pct:.0f}%</span>
            </div>
        """
        
        delay = item.get("delay_hours")
        delay_str = f"{float(delay):.0f}h" if delay is not None and str(delay) != "None" else "Now"
        
        rows += _table_row([
            f'<span style="color: #60A5FA; font-weight: 700;">{item.get("payment_id", "")}</span>',
            _tier_pill(tier),
            f'<span style="font-weight: 600;">{strategy}</span>',
            prob_bar,
            f'<span style="font-weight: 700;">{format_inr(item.get("amount"))}</span>',
            f'<span style="color: #F87171; font-size: 0.82rem;">{str(item.get("failure_reason", "")).replace("_", " ").title()}</span>',
            f'<span style="color: {COLORS["text_dim"]}; font-weight: 600;">{delay_str}</span>',
        ])

    _render_glass_table("Recovery Queue", "🎯", headers, rows, count=len(queue), subtitle="Prioritized by recovery probability and policy tier")


def render_payments_table(payments: List[Dict[str, Any]], total: int = 0) -> None:
    """Renders payments table with status pills and amount formatting."""
    if not payments:
        st.info("No payment records found matching your filters.")
        return

    headers = ["Payment ID", "Amount", "Method", "Status", "Failure Reason", "Timestamp"]
    rows = ""
    for p in payments:
        is_recovered = bool(p.get("recovered_after_failure"))
        is_failed = not p.get("payment_success", True)
        rows += _table_row([
            f'<span style="color: #60A5FA; font-weight: 700;">{p.get("id", "")}</span>',
            f'<span style="font-weight: 700;">{format_inr(p.get("amount"))}</span>',
            f'<span style="font-weight: 600;">{str(p.get("payment_method", "")).upper()}</span>',
            _payment_status_pill(is_recovered, is_failed),
            f'<span style="color: #F87171; font-size: 0.82rem;">{str(p.get("failure_reason", "N/A")).replace("_", " ").title()}</span>',
            f'<span style="color: {COLORS["text_dim"]}; font-size: 0.82rem;">{str(p.get("timestamp", ""))[:19]}</span>',
        ])

    _render_glass_table("Payment Records", "💳", headers, rows, count=total or len(payments))


def render_customers_table(customers: List[Dict[str, Any]], total: int = 0) -> None:
    """Renders customers table with segment pills and CLV formatting."""
    if not customers:
        st.info("No customer records found matching your filters.")
        return

    seg_colors = {"ENTERPRISE": "#A855F7", "PREMIUM": "#3B82F6", "BASIC": "#6B7280", "FREE_TRIAL": "#F59E0B"}

    headers = ["Customer ID", "Segment", "Lifetime Value", "Payments", "Failed", "Recovery Rate", "Region"]
    rows = ""
    for c in customers:
        seg = str(c.get("segment", "basic")).upper()
        seg_color = seg_colors.get(seg, "#6B7280")
        total_payments = c.get("total_payments", c.get("successful_payments", 0) + c.get("failed_payments", 0))
        rows += _table_row([
            f'<span style="color: #60A5FA; font-weight: 700;">{c.get("id", "")}</span>',
            _status_pill(seg, seg_color),
            f'<span style="font-weight: 700;">{format_inr(c.get("lifetime_value"))}</span>',
            f'{total_payments}',
            f'<span style="color: #F87171; font-weight: 700;">{c.get("failed_payments", 0)}</span>',
            f'<span style="font-weight: 700;">{float(c.get("historical_recovery_rate", 0) or 0) * 100:.0f}%</span>',
            f'{str(c.get("region", "N/A")).title()}',
        ])

    _render_glass_table("Customer Portfolio", "👤", headers, rows, count=total or len(customers))


def render_decisions_table(decisions: List[Dict[str, Any]], total: int = 0) -> None:
    """Renders AI decision log with tier pills and strategy indicators."""
    if not decisions:
        st.info("No AI decisions found. Run the recovery agent to populate the decision log.")
        return

    headers = ["ID", "Payment", "Tier", "Strategy", "Probability", "Human Review", "Timestamp"]
    rows = ""
    for d in decisions:
        tier = str(d.get("tier", "")).upper().replace(" ", "_")
        is_human = d.get("human_review_required", False)
        prob = d.get("recovery_probability", 0)
        prob_pct = prob * 100 if prob <= 1 else prob
        
        rows += _table_row([
            f'<span style="color: {COLORS["text_dim"]}; font-weight: 600;">#{d.get("id", "")}</span>',
            f'<span style="color: #60A5FA; font-weight: 700;">{d.get("payment_id", "")}</span>',
            _tier_pill(tier),
            f'<span style="font-weight: 600;">{str(d.get("strategy", d.get("recommended_action", ""))).replace("_", " ").title()}</span>',
            f'<span style="font-weight: 700; color: {TIER_COLORS.get(tier, COLORS["primary"])};">{prob_pct:.0f}%</span>',
            f'<span style="color: {"#F87171" if is_human else "#4ADE80"}; font-weight: 700;">{"⚠️ Yes" if is_human else "✅ Auto"}</span>',
            f'<span style="color: {COLORS["text_dim"]}; font-size: 0.82rem;">{str(d.get("timestamp", ""))[:19]}</span>',
        ])

    _render_glass_table("AI Decision Audit Log", "🤖", headers, rows, count=total or len(decisions), subtitle="Complete audit trail of autonomous recovery decisions")
