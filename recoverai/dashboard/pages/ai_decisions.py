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
from dashboard.config import COLORS


def render_ai_decisions_page() -> None:
    """Renders the AI decision history audit ledger safely."""
    st.markdown(
        f"""
        <div style="margin-bottom: 24px; animation: fadeInUp 0.5s ease-out both;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 900; letter-spacing: -0.5px;">
                <span style="background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-size: 200% 200%; animation: gradientShift 4s ease-in-out infinite;">
                    🤖 AI Decision Audit Ledger
                </span>
            </h1>
            <div style="color: {COLORS['text_dim']}; font-size: 0.92rem; font-weight: 500; margin-top: 6px;">
                Complete transparent audit trail of calibrated ML scores, deterministic policy rules, and reasoning.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
            if st.button("🔄 Refresh", key="dec_refresh_btn", use_container_width=True):
                st.rerun()

    # Pagination state management
    if "decisions_page" not in st.session_state:
        st.session_state.decisions_page = 1

    p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
    with p_col1:
        if st.button("⬅️ Prev Page", disabled=st.session_state.decisions_page <= 1, key="dec_prev"):
            st.session_state.decisions_page -= 1
            st.rerun()
    with p_col2:
        st.markdown(f"<div style='text-align: center; padding-top: 6px; color: #FFFFFF;'><b>Page {st.session_state.decisions_page}</b></div>", unsafe_allow_html=True)
    with p_col3:
        if st.button("Next Page ➡️", key="dec_next"):
            st.session_state.decisions_page += 1
            st.rerun()

    hr_val = True if hr_filter == "Required (Yes)" else (False if hr_filter == "Autonomous (No)" else None)

    # Fetch Decisions via API
    with st.spinner("Loading AI decision records..."):
        resp, err = api_client.get_decisions(
            page=st.session_state.decisions_page,
            page_size=25,
            payment_id=pid_filter.strip().upper() if pid_filter else None,
            customer_id=cid_filter.strip().upper() if cid_filter else None,
            tier=None if tier_filter == "All" else tier_filter,
            strategy=None if strategy_filter == "All" else strategy_filter,
            human_review_required=hr_val,
        )

    if err:
        st.error(f"Failed to fetch decisions: {err}")
        return

    items = (resp or {}).get("items", [])
    total = (resp or {}).get("total", 0)
    total_pages = (resp or {}).get("total_pages", 1)

    st.markdown(f"**Showing {len(items)} of {total:,} decision audits (Page {st.session_state.decisions_page} of {total_pages}):**")
    render_decisions_table(items)

    st.markdown("---")

    # 2. Decision Deep Inspector & Action Suite
    st.markdown(
        """
        <div style="font-size: 1.25rem; font-weight: 800; color: #FFFFFF; margin-bottom: 14px;">
            🔍 Deep Decision Audit Inspector & Re-Evaluation Hub
        </div>
        """,
        unsafe_allow_html=True,
    )

    if items:
        indices = list(range(len(items)))
        sel_idx = st.selectbox(
            "Select Decision Record to Inspect",
            options=indices,
            format_func=lambda i: f"Decision #{i+1} — {items[i].get('payment_id', 'N/A')} ({str(items[i].get('strategy', 'N/A')).replace('_', ' ').title()})",
            key="dec_sel_idx",
        )
        selected_decision = items[sel_idx]
        render_ai_decision_card(selected_decision)

        p_id = selected_decision.get("payment_id")
        c_id = selected_decision.get("customer_id")

        # Action Toolbar
        st.markdown(
            """
            <div style="background: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 14px; margin-top: 14px;">
                <div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-bottom: 8px;">⚡ Decision Navigation & Operational Actions:</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        d_act1, d_act2, d_act3, d_act4 = st.columns(4)
        with d_act1:
            if st.button("🎯 Open in Queue Workstation", use_container_width=True, key=f"btn_d_rq_{sel_idx}"):
                if p_id:
                    from dashboard.app import navigate_to
                    navigate_to("Recovery Queue", selected_payment_id=p_id)
        with d_act2:
            if st.button("💳 View in Payments Directory", use_container_width=True, key=f"btn_d_pmt_{sel_idx}"):
                if p_id:
                    from dashboard.app import navigate_to
                    navigate_to("Payments", selected_payment_id=p_id)
        with d_act3:
            if st.button("👤 View Customer Profile", use_container_width=True, key=f"btn_d_cust_{sel_idx}"):
                if c_id:
                    from dashboard.app import navigate_to
                    navigate_to("Customers", selected_customer_id=c_id)
        with d_act4:
            if st.button("🔄 Re-Evaluate Decision Engine", use_container_width=True, key=f"btn_d_eval_{sel_idx}"):
                if p_id:
                    with st.spinner(f"Re-evaluating policy rules for {p_id}..."):
                        eval_res, eval_err = api_client.analyze_recovery(p_id)
                    if eval_err:
                        st.error(f"Re-evaluation error: {eval_err}")
                    else:
                        st.success(f"✅ Live Policy Re-evaluated: Strategy={eval_res.get('strategy')}, Tier={eval_res.get('tier')}")
    else:
        st.info("No decision records currently match filters.")


if __name__ in ("__main__", "__mp_main__"):
    render_ai_decisions_page()
