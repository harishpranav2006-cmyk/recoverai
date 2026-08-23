"""
RecoverAI — Prioritized Recovery Queue Page (Clean & Operational)
================================================================
Operational workspace for triage, AI decision inspection, and simulated recovery workflow execution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st

from dashboard.api_client import api_client
from dashboard.components import (
    render_ai_decision_card,
    render_customer_context_card,
    render_customer_outreach_panel,
    render_event_timeline,
    render_ml_explainability_card,
    render_payment_summary_card,
    render_recovery_queue_table,
)


def render_recovery_queue_page() -> None:
    """Renders the prioritized recovery queue and interactive execution workstation."""
    st.title("🎯 Prioritized Recovery Queue")
    st.caption("Actionable failed payments ranked by calibrated recovery likelihood, customer value, and retry safety.")

    # 1. Filters Sidebar / Expander
    with st.expander("🔍 **Queue Filters & Prioritization Settings**", expanded=True):
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            tier_filter = st.selectbox(
                "Policy Tier",
                ["All", "HIGH_CONFIDENCE", "ACTIONABLE_OUTREACH", "SUPPRESS_OR_ESCALATE"],
                key="rq_tier_filter",
            )
        with f2:
            strategy_filter = st.selectbox(
                "Recovery Strategy",
                ["All", "SMART_RETRY", "CUSTOMER_OUTREACH", "PAYMENT_METHOD_UPDATE", "GRACE_PERIOD_EXTEND", "HUMAN_REVIEW", "SUPPRESS_RETRY"],
                key="rq_strategy_filter",
            )
        with f3:
            failure_filter = st.selectbox(
                "Failure Reason",
                ["All", "insufficient_funds", "network_failure", "expired_card", "authentication_failure", "bank_declined", "payment_timeout", "invalid_payment_details"],
                key="rq_failure_filter",
            )
        with f4:
            segment_filter = st.selectbox(
                "Customer Segment",
                ["All", "enterprise", "premium", "basic", "free_trial"],
                key="rq_segment_filter",
            )

        f5, f6, f7 = st.columns([1, 1, 1])
        with f5:
            human_review = st.selectbox("Human Review", ["All", "Required (Yes)", "Autonomous (No)"], key="rq_hr_filter")
        with f6:
            retry_eligible = st.selectbox("Retry Eligible", ["All", "Eligible (<3 retries)", "Exhausted (3+ retries)"], key="rq_re_filter")
        with f7:
            limit = st.slider("Queue Size Limit", min_value=10, max_value=100, value=25, step=5, key="rq_limit")

    # Map filters to API params
    tier_val = None if tier_filter == "All" else tier_filter
    strat_val = None if strategy_filter == "All" else strategy_filter
    fail_val = None if failure_filter == "All" else failure_filter
    seg_val = None if segment_filter == "All" else segment_filter
    hr_val = True if human_review == "Required (Yes)" else (False if human_review == "Autonomous (No)" else None)
    re_val = True if retry_eligible == "Eligible (<3 retries)" else (False if retry_eligible == "Exhausted (3+ retries)" else None)

    # 2. Fetch Queue Items
    with st.spinner("Fetching prioritized queue..."):
        queue_resp, q_err = api_client.get_recovery_queue(
            tier=tier_val,
            strategy=strat_val,
            failure_reason=fail_val,
            customer_segment=seg_val,
            human_review_required=hr_val,
            retry_eligible=re_val,
            limit=limit,
        )

    if q_err:
        st.error(f"Failed to load recovery queue: {q_err}")
        return

    if isinstance(queue_resp, dict):
        queue_items = queue_resp.get("items", [])
    elif isinstance(queue_resp, list):
        queue_items = queue_resp
    else:
        queue_items = []

    st.markdown(f"**Found {len(queue_items)} actionable payments requiring recovery policy evaluation:**")
    render_recovery_queue_table(queue_items)

    st.divider()

    # 3. Interactive Payment Inspection & Recovery Execution Workstation
    st.markdown("### ⚡ Payment Recovery Workstation & Action Suite")

    available_payment_ids = [
        item.get("payment_id") or item.get("id")
        for item in queue_items
        if isinstance(item, dict) and (item.get("payment_id") or item.get("id"))
    ]
    default_id = (
        st.session_state.get("selected_payment_id")
        if st.session_state.get("selected_payment_id") in available_payment_ids
        else (available_payment_ids[0] if available_payment_ids else "P000004")
    )

    c_sel, c_mode = st.columns([2, 2])
    with c_sel:
        selected_payment_id = st.selectbox(
            "Select Payment ID to Inspect & Recover",
            options=available_payment_ids if available_payment_ids else [default_id],
            index=available_payment_ids.index(default_id) if default_id in available_payment_ids else 0,
            key="rq_selected_payment_id",
        )
        st.session_state.selected_payment_id = selected_payment_id
    with c_mode:
        channel_select = st.selectbox("Preferred Outreach Channel", ["whatsapp", "email", "sms"], index=0, key="rq_channel")

    if not selected_payment_id:
        return

    # Fetch Payment & Customer Details
    with st.spinner(f"Loading telemetry for {selected_payment_id}..."):
        payment_data, p_err = api_client.get_payment(selected_payment_id)
        ml_data, m_err = api_client.predict_payment(selected_payment_id)
        decision_data, d_err = api_client.analyze_recovery(selected_payment_id)

    if p_err or not payment_data:
        st.error(f"Could not load payment {selected_payment_id}: {p_err}")
        return

    customer_data = payment_data.get("customer", {})

    # Display 2-Column Inspection View
    col_left, col_right = st.columns(2)

    with col_left:
        render_payment_summary_card(payment_data)
        if customer_data:
            render_customer_context_card(customer_data)

    with col_right:
        if ml_data:
            render_ml_explainability_card(ml_data)
        if decision_data:
            render_ai_decision_card(decision_data)

    # Outreach Preview if Applicable
    outreach_info = (decision_data or {}).get("customer_outreach")
    if outreach_info:
        render_customer_outreach_panel(outreach_info)

    # 4. Action Suite Toolbar
    with st.container(border=True):
        st.markdown("### 🚀 Autonomous Recovery Actions")
        st.caption("Execute focused operations or trigger full end-to-end recovery pipeline.")

        act1, act2, act3, act4 = st.columns(4)
        with act1:
            if st.button("🧠 Analyze Payment", use_container_width=True, key="btn_rq_analyze"):
                with st.spinner(f"Analyzing {selected_payment_id} through Decision Engine..."):
                    res, err = api_client.analyze_recovery(selected_payment_id)
                if err:
                    st.error(f"Analysis failed: {err}")
                else:
                    st.success(f"✅ Evaluated: Tier={res.get('tier')} | Strategy={res.get('strategy')}")
        with act2:
            if st.button("🤖 Run AI Agent", use_container_width=True, key="btn_rq_agent"):
                with st.spinner(f"Executing AI Recovery Agent for {selected_payment_id}..."):
                    res, err = api_client.run_agent(selected_payment_id, channel=channel_select)
                if err:
                    st.error(f"Agent execution failed: {err}")
                else:
                    st.success(f"✅ Agent completed: Decision={res.get('decision', {}).get('strategy')}")
        with act3:
            if st.button("⚡ Simulate Gateway", use_container_width=True, key="btn_rq_sim"):
                with st.spinner(f"Simulating gateway retry for {selected_payment_id}..."):
                    res, err = api_client.simulate_payment(selected_payment_id, force_fresh=True)
                if err:
                    st.error(f"Simulation failed: {err}")
                else:
                    st.info(f"Gateway Response: {res.get('gateway_response_code')} | Outcome: {res.get('outcome_status')}")
        with act4:
            if st.button("👤 View Customer", use_container_width=True, key="btn_rq_view_cust"):
                from dashboard.app import navigate_to
                navigate_to("Customers", selected_customer_id=customer_data.get("id"))

    # 5. Full Workflow Execution
    with st.expander("🚀 **Execute Full Autonomous Recovery Workflow (with Confirmation)**", expanded=True):
        st.markdown(
            f"Ready to execute full workflow for **`{selected_payment_id}`** (Amount: ₹{payment_data.get('amount', 0):,.2f}, Strategy: **{decision_data.get('strategy', 'SMART_RETRY')}**)."
        )

        wf_c1, wf_c2, wf_c3 = st.columns([2, 1, 1])
        with wf_c1:
            run_btn = st.button("🚀 Confirm & Run Recovery Workflow", type="primary", use_container_width=True, key="btn_rq_workflow")
        with wf_c2:
            force_fresh_wf = st.checkbox("Force Fresh Execution", value=False, key="rq_force_fresh")
        with wf_c3:
            seed_val_wf = st.number_input("Simulator Seed", value=42, step=1, key="rq_seed")

        if run_btn:
            with st.spinner(f"Executing autonomous recovery workflow for {selected_payment_id}..."):
                workflow_res, w_err = api_client.run_workflow(
                    payment_id=selected_payment_id,
                    channel=channel_select,
                    force_fresh=force_fresh_wf,
                    seed=seed_val_wf,
                )

            if w_err or not workflow_res:
                st.error(f"❌ Workflow execution failed: {w_err}")
            else:
                sim_outcome = workflow_res.get("simulated_outcome", {})
                outcome_status = sim_outcome.get("outcome_status", "UNKNOWN")
                is_success = outcome_status == "RECOVERED"

                if is_success:
                    st.success(
                        f"🎉 **SIMULATED RECOVERY SUCCEEDED** | Gateway Response: `{sim_outcome.get('gateway_response_code', 'N/A')}` | "
                        f"Recovered Amount: **₹{sim_outcome.get('recovered_amount', 0.0):,.2f}** | "
                        f"Payment Status: **{workflow_res.get('payment_state', 'N/A')}** (Attempts: {sim_outcome.get('attempt_number', 1)})"
                    )
                else:
                    st.warning(
                        f"⚠️ **SIMULATION RESULT: {outcome_status}** | Gateway Response: `{sim_outcome.get('gateway_response_code', 'N/A')}` | "
                        f"Payment Status: **{workflow_res.get('payment_state', 'N/A')}**"
                    )

    # 6. Chronological Event Timeline
    st.divider()
    with st.spinner("Loading payment event timeline..."):
        timeline_data, _ = api_client.get_payment_timeline(selected_payment_id)
        if timeline_data and "events" in timeline_data:
            render_event_timeline(timeline_data.get("events", []))


if __name__ in ("__main__", "__mp_main__"):
    render_recovery_queue_page()
