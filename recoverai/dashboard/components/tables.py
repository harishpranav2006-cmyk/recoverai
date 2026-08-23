"""
RecoverAI — Data Tables Component (Clean Native Streamlit Dataframes)
=====================================================================
Renders interactive, searchable, sortable data tables with clean formatting,
progress bars, and status badges using native Streamlit dataframe configuration.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st

from dashboard.components.metrics import format_inr


def render_recovery_queue_table(queue: List[Dict[str, Any]], on_select_callback: Optional[str] = None) -> None:
    """Renders the recovery queue in an interactive, sortable, clean dataframe."""
    if not queue:
        st.info("Recovery queue is empty. Run simulations to populate.")
        return

    rows = []
    for item in queue:
        prob = float(item.get("recovery_probability", 0) or 0)
        prob_pct = prob if prob > 1.0 else prob * 100
        
        delay = item.get("delay_hours")
        delay_str = f"{float(delay):.0f}h" if (delay is not None and str(delay) != "None") else "Immediate (0h)"
        
        rows.append({
            "Payment ID": str(item.get("payment_id", "")),
            "Policy Tier": str(item.get("tier", "")).replace("_", " ").title(),
            "Strategy": str(item.get("strategy", "")).replace("_", " ").title(),
            "Recovery Likelihood (%)": round(prob_pct, 1),
            "Amount (₹)": float(item.get("amount", 0.0) or 0.0),
            "Failure Reason": str(item.get("failure_reason", "")).replace("_", " ").title(),
            "Delay": delay_str,
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        column_config={
            "Recovery Likelihood (%)": st.column_config.ProgressColumn(
                "Recovery Likelihood (%)",
                help="Calibrated ML probability",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "Amount (₹)": st.column_config.NumberColumn(
                "Amount",
                help="Payment value in INR",
                format="₹%.2f",
            ),
        },
        use_container_width=True,
        hide_index=True,
    )


def render_payments_table(payments: List[Dict[str, Any]], total: int = 0) -> None:
    """Renders payments table with clean columns and search."""
    if not payments:
        st.info("No payment records found matching your filters.")
        return

    rows = []
    for p in payments:
        is_recovered = bool(p.get("recovered_after_failure"))
        is_failed = not p.get("payment_success", True)
        status = "✅ Recovered" if is_recovered else ("❌ Failed" if is_failed else "✓ Succeeded")
        
        rows.append({
            "Payment ID": str(p.get("id", "")),
            "Amount (₹)": float(p.get("amount", 0.0) or 0.0),
            "Method": str(p.get("payment_method", "")).upper(),
            "Status": status,
            "Failure Reason": str(p.get("failure_reason", "None")).replace("_", " ").title(),
            "Timestamp": str(p.get("timestamp", ""))[:19],
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        column_config={
            "Amount (₹)": st.column_config.NumberColumn(
                "Amount",
                format="₹%.2f",
            ),
        },
        use_container_width=True,
        hide_index=True,
    )


def render_customers_table(customers: List[Dict[str, Any]], total: int = 0) -> None:
    """Renders customers table with CLV and recovery rate formatting."""
    if not customers:
        st.info("No customer records found matching your filters.")
        return

    rows = []
    for c in customers:
        total_payments = c.get("total_payments", c.get("successful_payments", 0) + c.get("failed_payments", 0))
        rec_rate = float(c.get("historical_recovery_rate", 0) or 0)
        rec_rate_pct = rec_rate if rec_rate > 1.0 else rec_rate * 100

        rows.append({
            "Customer ID": str(c.get("id", "")),
            "Segment": str(c.get("segment", "basic")).upper(),
            "Lifetime Value (₹)": float(c.get("lifetime_value", 0.0) or 0.0),
            "Total Payments": total_payments,
            "Failed Payments": c.get("failed_payments", 0),
            "Recovery Rate (%)": round(rec_rate_pct, 1),
            "Region": str(c.get("region", "N/A")).title(),
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        column_config={
            "Lifetime Value (₹)": st.column_config.NumberColumn(
                "Lifetime Value (CLV)",
                format="₹%.2f",
            ),
            "Recovery Rate (%)": st.column_config.ProgressColumn(
                "Recovery Rate",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
        use_container_width=True,
        hide_index=True,
    )


def render_decisions_table(decisions: List[Dict[str, Any]], total: int = 0) -> None:
    """Renders AI decision audit log with clean strategy columns."""
    if not decisions:
        st.info("No AI decisions found. Run the recovery agent to populate the decision log.")
        return

    rows = []
    for d in decisions:
        prob = float(d.get("recovery_probability", 0) or 0)
        prob_pct = prob if prob > 1.0 else prob * 100
        is_human = bool(d.get("human_review_required", False))

        rows.append({
            "Decision ID": str(d.get("id", "")),
            "Payment ID": str(d.get("payment_id", "")),
            "Policy Tier": str(d.get("tier", "")).replace("_", " ").title(),
            "Strategy": str(d.get("strategy", d.get("recommended_action", ""))).replace("_", " ").title(),
            "Probability (%)": round(prob_pct, 1),
            "Review Type": "⚠️ Human Review" if is_human else "✅ Autonomous",
            "Timestamp": str(d.get("timestamp", ""))[:19],
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        column_config={
            "Probability (%)": st.column_config.ProgressColumn(
                "Probability (%)",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
        use_container_width=True,
        hide_index=True,
    )
