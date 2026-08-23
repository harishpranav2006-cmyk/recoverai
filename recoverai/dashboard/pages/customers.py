"""
RecoverAI — Customer Intelligence Page (Clean & Schema-Safe)
============================================================
Customer directory, CLV tracking, historical recovery performance, and customer-level audit histories.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st

from dashboard.api_client import api_client
from dashboard.components import (
    render_customer_context_card,
    render_customers_table,
    render_payments_table,
)
from dashboard.config import COLORS


def render_customers_page() -> None:
    """Renders the customers directory with search, segmentation, and deep profile inspection."""
    st.markdown(
        f"""
        <div style="margin-bottom: 24px; animation: fadeInUp 0.5s ease-out both;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 900; letter-spacing: -0.5px;">
                <span style="background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-size: 200% 200%; animation: gradientShift 4s ease-in-out infinite;">
                    👤 Customer Intelligence & Portfolios
                </span>
            </h1>
            <div style="color: {COLORS['text_dim']}; font-size: 0.92rem; font-weight: 500; margin-top: 6px;">
                Customer profiles, lifetime value (CLV), segment tiering, and historical recovery yield.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Search & Segment Filters
    with st.expander("🔍 **Customer Filters & Sorting**", expanded=True):
        c_search, c_seg, c_reg = st.columns([2, 1, 1])
        with c_search:
            search_query = st.text_input("Search Customer ID", placeholder="e.g. C00001", key="cust_search_query")
        with c_seg:
            seg_filter = st.selectbox("Segment", ["All", "enterprise", "premium", "basic", "free_trial"], key="cust_seg_filter")
        with c_reg:
            reg_filter = st.selectbox("Region", ["All", "North", "South", "East", "West", "Central"], key="cust_reg_filter")

        c_sort, c_order, c_ref = st.columns([2, 2, 1])
        with c_sort:
            sort_by = st.selectbox("Sort By", ["lifetime_value", "successful_payments", "failed_payments", "historical_recovery_rate"], key="cust_sort_by")
        with c_order:
            sort_order = st.selectbox("Sort Order", ["desc", "asc"], key="cust_sort_order")
        with c_ref:
            if st.button("🔄 Refresh", key="cust_refresh_btn", use_container_width=True):
                st.rerun()

    # Pagination state management
    if "customers_page" not in st.session_state:
        st.session_state.customers_page = 1

    p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
    with p_col1:
        if st.button("⬅️ Prev Page", disabled=st.session_state.customers_page <= 1, key="cust_prev_btn"):
            st.session_state.customers_page -= 1
            st.rerun()
    with p_col2:
        st.markdown(f"<div style='text-align: center; padding-top: 6px; color: #FFFFFF;'><b>Page {st.session_state.customers_page}</b></div>", unsafe_allow_html=True)
    with p_col3:
        if st.button("Next Page ➡️", key="cust_next_btn"):
            st.session_state.customers_page += 1
            st.rerun()

    # Fetch Customers via API
    with st.spinner("Fetching customer portfolios..."):
        resp, err = api_client.get_customers(
            page=st.session_state.customers_page,
            page_size=25,
            search=search_query.strip().upper() if search_query else None,
            segment=None if seg_filter == "All" else seg_filter,
            region=None if reg_filter == "All" else reg_filter,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    if err:
        st.error(f"Failed to fetch customers: {err}")
        return

    items = (resp or {}).get("items", [])
    total = (resp or {}).get("total", 0)
    total_pages = (resp or {}).get("total_pages", 1)

    st.markdown(f"**Showing {len(items)} of {total:,} customers (Page {st.session_state.customers_page} of {total_pages}):**")
    render_customers_table(items)

    st.markdown("---")

    # 2. Customer Profile & Payment History
    st.markdown(
        """
        <div style="font-size: 1.25rem; font-weight: 800; color: #FFFFFF; margin-bottom: 14px;">
            🔍 Customer Profile & Transaction Ledger
        </div>
        """,
        unsafe_allow_html=True,
    )

    initial_cid = st.session_state.get("selected_customer_id", items[0].get("id", "C00001") if items else "C00001")
    cust_input = st.text_input("Enter Customer ID to Inspect Ledger", value=initial_cid, key="cust_detail_id_input").strip().upper()

    if cust_input:
        st.session_state.selected_customer_id = cust_input
        with st.spinner(f"Loading history for {cust_input}..."):
            cust_detail, c_err = api_client.get_customer(cust_input)
            cust_history, _ = api_client.get_customer_history(cust_input)

        if c_err or not cust_detail:
            st.error(f"Customer '{cust_input}' not found.")
        else:
            render_customer_context_card(cust_detail)

            payments_list = (cust_history or {}).get("payments", [])
            if payments_list:
                st.markdown(f"**Transaction Ledger ({len(payments_list)} Payments):**")
                render_payments_table(payments_list)

                # Quick payment inspection action bar from customer ledger
                st.markdown(
                    """
                    <div style="background: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 14px; margin-top: 14px;">
                        <div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-bottom: 8px;">💳 Inspect Payment from Customer Ledger:</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                p_options = [p.get("payment_id") or p.get("id") for p in payments_list if (p.get("payment_id") or p.get("id"))]
                if p_options:
                    pick_p = st.selectbox("Select Payment from Ledger to Inspect", p_options, index=0, key="cust_pick_p")
                    
                    c_act1, c_act2, c_act3 = st.columns(3)
                    with c_act1:
                        if st.button("💳 Open in Payments Directory", use_container_width=True, key="btn_c_open_pmt"):
                            from dashboard.app import navigate_to
                            navigate_to("Payments", selected_payment_id=pick_p)
                    with c_act2:
                        if st.button("🎯 Open in Recovery Queue", use_container_width=True, key="btn_c_open_rq"):
                            from dashboard.app import navigate_to
                            navigate_to("Recovery Queue", selected_payment_id=pick_p)
                    with c_act3:
                        if st.button("🧠 Analyze Payment", use_container_width=True, key="btn_c_analyze_p"):
                            with st.spinner(f"Analyzing {pick_p}..."):
                                res, err = api_client.analyze_recovery(pick_p)
                            if err:
                                st.error(f"Error: {err}")
                            else:
                                st.success(f"Strategy: {res.get('strategy')} (Tier: {res.get('tier')})")


if __name__ in ("__main__", "__mp_main__"):
    render_customers_page()
