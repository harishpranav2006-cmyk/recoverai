"""
RecoverAI — AI Decisions Audit Ledger Page (Clean & Schema-Safe)
================================================================
Transparent audit trail of autonomous policy decisions, reason codes, and human review escalations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st

from dashboard.api_client import api_client
from dashboard.components import (
    render_ai_decision_card,
    render_decisions_table,
)


def render_ai_decisions_page() -> None:
    """Renders the AI decision history audit ledger safely."""
    st.title("🤖 AI Decision Audit Ledger")
    st.caption("Complete transparent audit trail of calibrated ML scores, deterministic policy rules, and reasoning.")

    # 1. Filters
    with st.expander("🔍 **Decision Audit Filters**", expanded=True):
        c_tier, c_strat, c_hr = st.columns(3)
        with c_tier:
            tier_filter = st.selectbox("Policy Tier", ["All", "HIGH_CONFIDENCE", "ACTIONABLE_OUTREACH", "SUPPRESS_OR_ESCALATE"], key="dec_tier_filter")
        with c_strat:
            strategy_filter = st.selectbox("Recovery Strategy", ["All", "SMART_RETRY", "CUSTOMER_OUTREACH", "PAYMENT_METHOD_UPDATE", "GRACE_PERIOD_EXTEND", "HUMAN_REVIEW", "SUPPRESS_RETRY"], key="dec_strat_filter")
        with c_hr:
            hr_filter = st.selectbox("Human Review Flag", ["All", "Required (Yes)", "Autonomous (No)"], key="dec_hr_filter")

        c_pid, c_cid, c_ref = st.columns([2, 2, 1])
        with c_pid:
            pid_filter = st.text_input("Filter by Payment ID", placeholder="e.g. P000004", key="dec_pid_filter")
        with c_cid:
            cid_filter = st.text_input("Filter by Customer ID", placeholder="e.g. C00001", key="dec_cid_filter")
        with c_ref:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Refresh", key="dec_refresh_btn", use_container_width=True):
                st.rerun()

    # Pagination state management
    if "decisions_page" not in st.session_state:
        st.session_state.decisions_page = 1

    tier_val = None if tier_filter == "All" else tier_filter
    strat_val = None if strategy_filter == "All" else strategy_filter
    hr_val = True if hr_filter == "Required (Yes)" else (False if hr_filter == "Autonomous (No)" else None)
    pid_val = pid_filter.strip() if pid_filter.strip() else None
    cid_val = cid_filter.strip() if cid_filter.strip() else None

    # Fetch Decisions
    with st.spinner("Loading AI audit log..."):
        resp, err = api_client.get_decisions(
            page=st.session_state.decisions_page,
            page_size=25,
            tier=tier_val,
            strategy=strat_val,
            human_review_required=hr_val,
            payment_id=pid_val,
            customer_id=cid_val,
        )

    if err or not resp:
        st.error(f"Failed to load AI decisions: {err}")
        return

    items = resp.get("items", [])
    total = resp.get("total", 0)
    total_pages = max(1, resp.get("pages", 1))

    # Pagination
    p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
    with p_col1:
        if st.button("⬅️ Previous", disabled=(st.session_state.decisions_page <= 1), key="dec_prev_btn", use_container_width=True):
            st.session_state.decisions_page -= 1
            st.rerun()
    with p_col2:
        st.markdown(f"<div style='text-align: center; padding-top: 6px; font-weight: 700;'>Page {st.session_state.decisions_page} of {total_pages} ({total:,} decisions logged)</div>", unsafe_allow_html=True)
    with p_col3:
        if st.button("Next ➡️", disabled=(st.session_state.decisions_page >= total_pages), key="dec_next_btn", use_container_width=True):
            st.session_state.decisions_page += 1
            st.rerun()

    # Render Table
    render_decisions_table(items, total=total)

    # 2. Decision Deep-Dive Inspector
    if items:
        st.divider()
        st.markdown("### 🔍 AI Decision Deep-Dive Inspector")
        
        dec_options = [
            f"#{d.get('id')} — Payment {d.get('payment_id')} ({d.get('strategy', 'N/A')})"
            for d in items
            if d.get("id")
        ]
        
        if dec_options:
            selected_dec_str = st.selectbox("Select Decision to Inspect", dec_options, index=0, key="dec_inspect_sel")
            dec_id = int(selected_dec_str.split("—")[0].replace("#", "").strip())
            
            selected_decision = next((d for d in items if d.get("id") == dec_id), None)
            if selected_decision:
                render_ai_decision_card(selected_decision)


if __name__ in ("__main__", "__mp_main__"):
    render_ai_decisions_page()
