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


def render_customers_page() -> None:
    """Renders the customers directory with search, segmentation, and deep profile inspection."""
    st.title("👤 Customer Intelligence & Portfolios")
    st.caption("Customer profiles, lifetime value (CLV), segment tiering, and historical recovery yield.")

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
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Refresh", key="cust_refresh_btn", use_container_width=True):
                st.rerun()

    # Track pagination in session state
    if "customers_page" not in st.session_state:
        st.session_state.customers_page = 1

    seg_val = None if seg_filter == "All" else seg_filter
    reg_val = None if reg_filter == "All" else reg_filter
    search_val = search_query.strip() if search_query.strip() else None

    # Fetch Customers
    with st.spinner("Fetching customer portfolios..."):
        resp, err = api_client.get_customers(
            page=st.session_state.customers_page,
            page_size=25,
            segment=seg_val,
            region=reg_val,
            search=search_val,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    if err or not resp:
        st.error(f"Failed to load customers: {err}")
        return

    items = resp.get("items", [])
    total = resp.get("total", 0)
    total_pages = max(1, resp.get("pages", 1))

    # Pagination controls
    p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
    with p_col1:
        if st.button("⬅️ Previous", disabled=(st.session_state.customers_page <= 1), key="cust_prev_btn", use_container_width=True):
            st.session_state.customers_page -= 1
            st.rerun()
    with p_col2:
        st.markdown(f"<div style='text-align: center; padding-top: 6px; font-weight: 700;'>Page {st.session_state.customers_page} of {total_pages} ({total:,} customers)</div>", unsafe_allow_html=True)
    with p_col3:
        if st.button("Next ➡️", disabled=(st.session_state.customers_page >= total_pages), key="cust_next_btn", use_container_width=True):
            st.session_state.customers_page += 1
            st.rerun()

    # Render Table
    render_customers_table(items, total=total)

    # 2. Deep Customer Profile & History Inspector
    if items:
        st.divider()
        st.markdown("### 🔍 Customer Profile & Transaction History")
        
        available_cust_ids = [c.get("id") for c in items if c.get("id")]
        preselected_id = st.session_state.get("selected_customer_id")
        def_idx = available_cust_ids.index(preselected_id) if preselected_id in available_cust_ids else 0
        
        selected_cid = st.selectbox("Select Customer to Inspect", available_cust_ids, index=def_idx, key="cust_detail_sel")

        if selected_cid:
            with st.spinner(f"Loading full profile for {selected_cid}..."):
                cust_profile, c_err = api_client.get_customer(selected_cid)
                history_resp, _ = api_client.get_customer_history(selected_cid)

            if cust_profile:
                render_customer_context_card(cust_profile)

            if history_resp:
                payments_list = history_resp.get("payments", []) if isinstance(history_resp, dict) else (history_resp if isinstance(history_resp, list) else [])
                st.markdown(f"#### 💳 Payment History for `{selected_cid}` ({len(payments_list)} transactions)")
                render_payments_table(payments_list)



if __name__ in ("__main__", "__mp_main__"):
    render_customers_page()
