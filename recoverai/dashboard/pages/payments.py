"""
RecoverAI — Payments Directory Page (Fintech High-Contrast Dark Theme)
======================================================================
Searchable, filterable, and paginated payment transaction explorer with timeline inspection.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st

from dashboard.api_client import api_client
from dashboard.components import (
    render_event_timeline,
    render_payment_summary_card,
    render_payments_table,
)
from dashboard.config import COLORS


def render_payments_page() -> None:
    """Renders the payments directory with search, filters, pagination, and detail inspection."""
    st.markdown(
        f"""
        <div style="margin-bottom: 24px; animation: fadeInUp 0.5s ease-out both;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 900; letter-spacing: -0.5px;">
                <span style="background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-size: 200% 200%; animation: gradientShift 4s ease-in-out infinite;">
                    💳 Payments Directory
                </span>
            </h1>
            <div style="color: {COLORS['text_dim']}; font-size: 0.92rem; font-weight: 500; margin-top: 6px;">
                Browse and inspect 50,000 transaction records with multi-dimensional filtering and audit timelines.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Search & Filter Bar
    with st.expander("🔍 **Search & Multi-Dimensional Filters**", expanded=True):
        c_search, c_status, c_method = st.columns([2, 1, 1])
        with c_search:
            search_query = st.text_input("Search Payment ID / Customer ID", placeholder="e.g. P000004 or C00001", key="pmt_search_query")
        with c_status:
            default_status = st.session_state.get("payments_status_filter", "All")
            status_options = ["All", "failed", "succeeded", "recovered"]
            status_idx = status_options.index(default_status) if default_status in status_options else 0
            status_filter = st.selectbox("Status", status_options, index=status_idx, key="pmt_status_filter")
        with c_method:
            method_filter = st.selectbox("Method", ["All", "card", "upi", "netbanking", "wallet"], key="pmt_method_filter")

        c_fail, c_amt_min, c_amt_max = st.columns([2, 1, 1])
        with c_fail:
            failure_filter = st.selectbox(
                "Failure Reason",
                ["All", "insufficient_funds", "network_failure", "expired_card", "authentication_failure", "bank_declined", "payment_timeout", "invalid_payment_details"],
                key="pmt_fail_filter",
            )
        with c_amt_min:
            min_amount = st.number_input("Min Amount (₹)", min_value=0.0, value=0.0, step=500.0, key="pmt_min_amt")
        with c_amt_max:
            max_amount = st.number_input("Max Amount (₹)", min_value=0.0, value=0.0, step=1000.0, key="pmt_max_amt")

    # Pagination state management
    if "payments_page" not in st.session_state:
        st.session_state.payments_page = 1

    p_col1, p_col2, p_col3, p_col4 = st.columns([1, 2, 1, 1])
    with p_col1:
        if st.button("⬅️ Previous Page", disabled=st.session_state.payments_page <= 1, key="pmt_prev_btn"):
            st.session_state.payments_page -= 1
            st.rerun()
    with p_col2:
        st.markdown(f"<div style='text-align: center; padding-top: 6px; color: #FFFFFF;'><b>Page {st.session_state.payments_page}</b></div>", unsafe_allow_html=True)
    with p_col3:
        if st.button("Next Page ➡️", key="pmt_next_btn"):
            st.session_state.payments_page += 1
            st.rerun()
    with p_col4:
        if st.button("🔄 Refresh", key="pmt_refresh_btn", use_container_width=True):
            st.rerun()

    # Map filters to API params
    cust_id = search_query.strip().upper() if search_query and search_query.strip().upper().startswith("C") else None
    pmt_id = search_query.strip().upper() if search_query and search_query.strip().upper().startswith("P") else None

    # Fetch Payments via API
    with st.spinner("Fetching payment records from backend..."):
        resp, err = api_client.get_payments(
            page=st.session_state.payments_page,
            page_size=25,
            status=None if status_filter == "All" else status_filter,
            failure_reason=None if failure_filter == "All" else failure_filter,
            payment_method=None if method_filter == "All" else method_filter,
            customer_id=cust_id,
            min_amount=min_amount if min_amount > 0 else None,
            max_amount=max_amount if max_amount > 0 else None,
        )

    if err:
        st.error(f"Failed to fetch payments: {err}")
        return

    items = (resp or {}).get("items", [])
    total = (resp or {}).get("total", 0)
    total_pages = (resp or {}).get("total_pages", 1)

    st.markdown(f"**Showing {len(items)} of {total:,} payments (Page {st.session_state.payments_page} of {total_pages}):**")
    render_payments_table(items)

    st.markdown("---")

    # 2. Detailed Payment Inspector & Action Suite
    st.markdown(
        """
        <div style="font-size: 1.35rem; font-weight: 800; color: #FFFFFF; margin-bottom: 14px;">
            🔍 Deep Payment Inspector & Action Hub
        </div>
        """,
        unsafe_allow_html=True,
    )

    initial_insp_id = st.session_state.get("selected_payment_id", items[0]["id"] if items else "P000004")
    insp_id = st.text_input("Enter Specific Payment ID to Inspect", value=initial_insp_id, key="pmt_insp_id_input").strip().upper()

    if insp_id:
        st.session_state.selected_payment_id = insp_id
        with st.spinner(f"Loading details for {insp_id}..."):
            payment_detail, p_err = api_client.get_payment(insp_id)
            timeline_data, _ = api_client.get_payment_timeline(insp_id)

        if p_err or not payment_detail:
            st.error(f"Payment '{insp_id}' not found.")
        else:
            col_l, col_r = st.columns([1, 1])
            with col_l:
                render_payment_summary_card(payment_detail)
                
                # Payment Actions Toolbar
                st.markdown(
                    """
                    <div style="background: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 16px; margin-top: 10px;">
                        <div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-bottom: 10px;">⚡ Operational Actions:</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("🧠 Analyze Payment", use_container_width=True, key=f"btn_p_an_{insp_id}"):
                        with st.spinner("Analyzing..."):
                            an_res, an_err = api_client.analyze_recovery(insp_id)
                        if an_err:
                            st.error(f"Error: {an_err}")
                        else:
                            st.success(f"Strategy: {an_res.get('strategy')} (Tier: {an_res.get('tier')})")
                    if st.button("🎯 Open in Queue Workstation", use_container_width=True, key=f"btn_p_q_{insp_id}"):
                        from dashboard.app import navigate_to
                        navigate_to("Recovery Queue", selected_payment_id=insp_id)
                with b2:
                    if st.button("🤖 Run AI Recovery Agent", use_container_width=True, key=f"btn_p_ag_{insp_id}"):
                        with st.spinner("Running Agent..."):
                            ag_res, ag_err = api_client.run_agent(insp_id)
                        if ag_err:
                            st.error(f"Error: {ag_err}")
                        else:
                            st.success(f"Agent Action: {ag_res.get('decision', {}).get('strategy')}")
                    if st.button("👤 View Customer Profile", use_container_width=True, key=f"btn_p_cust_{insp_id}"):
                        from dashboard.app import navigate_to
                        navigate_to("Customers", selected_customer_id=payment_detail.get("customer_id"))

            with col_r:
                if timeline_data and "events" in timeline_data:
                    render_event_timeline(timeline_data.get("events", []))


if __name__ in ("__main__", "__mp_main__"):
    render_payments_page()
