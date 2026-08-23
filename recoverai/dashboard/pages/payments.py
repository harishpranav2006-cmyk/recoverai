"""
RecoverAI — Payments Directory Page (Clean & Filterable)
========================================================
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


def render_payments_page() -> None:
    """Renders the payments directory with search, filters, pagination, and detail inspection."""
    st.title("💳 Payments Directory")
    st.caption("Browse and inspect 50,000 transaction records with multi-dimensional filtering and audit timelines.")

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

        c_sort, c_order, c_psize = st.columns([2, 2, 1])
        with c_sort:
            sort_by = st.selectbox("Sort By", ["timestamp", "amount", "retry_count"], key="pmt_sort_by")
        with c_order:
            sort_order = st.selectbox("Sort Order", ["desc", "asc"], key="pmt_sort_order")
        with c_psize:
            page_size = st.selectbox("Page Size", [15, 25, 50, 100], index=1, key="pmt_page_size")

    # Map filter values
    status_val = None if status_filter == "All" else status_filter
    method_val = None if method_filter == "All" else method_filter
    fail_val = None if failure_filter == "All" else failure_filter
    min_amt_val = min_amount if min_amount > 0 else None
    max_amt_val = max_amount if max_amount > 0 else None
    search_val = search_query.strip() if search_query.strip() else None

    # Track pagination in session state
    if "payments_page" not in st.session_state:
        st.session_state.payments_page = 1

    # Fetch Payments
    with st.spinner("Fetching transaction records..."):
        resp, err = api_client.get_payments(
            page=st.session_state.payments_page,
            page_size=page_size,
            status=status_val,
            payment_method=method_val,
            failure_reason=fail_val,
            min_amount=min_amt_val,
            max_amount=max_amt_val,
            search=search_val,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    if err or not resp:
        st.error(f"Failed to load payments: {err}")
        return

    items = resp.get("items", [])
    total = resp.get("total", 0)
    total_pages = max(1, resp.get("pages", 1))

    # Pagination controls
    p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
    with p_col1:
        if st.button("⬅️ Previous", disabled=(st.session_state.payments_page <= 1), key="pmt_prev_btn", use_container_width=True):
            st.session_state.payments_page -= 1
            st.rerun()
    with p_col2:
        st.markdown(f"<div style='text-align: center; padding-top: 6px; font-weight: 700;'>Page {st.session_state.payments_page} of {total_pages} ({total:,} total records)</div>", unsafe_allow_html=True)
    with p_col3:
        if st.button("Next ➡️", disabled=(st.session_state.payments_page >= total_pages), key="pmt_next_btn", use_container_width=True):
            st.session_state.payments_page += 1
            st.rerun()

    # Render Table
    render_payments_table(items, total=total)

    # 2. Detail Inspector
    if items:
        st.divider()
        st.markdown("### 🔍 Payment Detail & Event Timeline Inspector")
        item_ids = [it.get("id") for it in items if it.get("id")]
        selected_id = st.selectbox("Select Payment to Inspect", item_ids, index=0, key="pmt_detail_sel")

        if selected_id:
            with st.spinner(f"Loading details for {selected_id}..."):
                payment_detail, p_err = api_client.get_payment(selected_id)
                timeline_detail, _ = api_client.get_payment_timeline(selected_id)

            if payment_detail:
                render_payment_summary_card(payment_detail)

            if timeline_detail and "events" in timeline_detail:
                render_event_timeline(timeline_detail.get("events", []))


if __name__ in ("__main__", "__mp_main__"):
    render_payments_page()
