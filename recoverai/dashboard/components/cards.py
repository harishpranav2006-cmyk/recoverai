"""
RecoverAI — Information & Decision Cards Component (Clean & User-Friendly)
==========================================================================
Clean, executive-grade information cards for payments, customer context,
ML predictions with SHAP explainability, and AI decision rationale.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st

from dashboard.config import COLORS, STRATEGY_ICONS, TIER_COLORS
from dashboard.components.metrics import format_inr, format_percent


def render_payment_summary_card(payment: Dict[str, Any]) -> None:
    """Renders a clean, structured summary of a payment transaction."""
    is_rec = bool(payment.get("recovered_after_failure"))
    is_success = bool(payment.get("payment_success"))
    
    if is_rec:
        status_badge = "✅ Recovered"
    elif is_success:
        status_badge = "✓ Succeeded"
    else:
        status_badge = "❌ Failed"

    with st.container(border=True):
        col_hdr1, col_hdr2 = st.columns([3, 1])
        with col_hdr1:
            st.markdown(f"### 💳 Payment `{payment.get('id', 'N/A')}`")
        with col_hdr2:
            st.markdown(f"**Status:** {status_badge}")

        st.divider()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.caption("Transaction Amount")
            st.markdown(f"**{format_inr(payment.get('amount'))}**")
            st.caption("Payment Method")
            st.markdown(f"**{str(payment.get('payment_method', '')).upper()}**")
        with c2:
            st.caption("Failure Reason")
            fail_reason = str(payment.get('failure_reason', 'N/A')).replace('_', ' ').title()
            st.markdown(f"<span style='color: #F87171; font-weight: 700;'>{fail_reason}</span>", unsafe_allow_html=True)
            st.caption("Failure Category")
            st.markdown(f"**{str(payment.get('failure_category', 'N/A')).title()}**")
        with c3:
            st.caption("Retry Attempts")
            st.markdown(f"**{payment.get('retry_count', 0)} of 3 maximum**")
            st.caption("Timestamp")
            st.markdown(f"`{str(payment.get('timestamp', ''))[:19]}`")


def render_customer_context_card(customer: Dict[str, Any]) -> None:
    """Renders the customer profile and financial context."""
    segment = str(customer.get('segment', 'basic')).upper()
    seg_icons = {"ENTERPRISE": "👑 Enterprise", "PREMIUM": "⭐ Premium", "BASIC": "👤 Basic", "FREE_TRIAL": "🌱 Free Trial"}
    seg_label = seg_icons.get(segment, f"👤 {segment}")

    with st.container(border=True):
        col_hdr1, col_hdr2 = st.columns([3, 1])
        with col_hdr1:
            st.markdown(f"### 👤 Customer Profile `{customer.get('id', 'N/A')}`")
        with col_hdr2:
            st.markdown(f"**Tier:** `{segment}`")

        st.divider()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.caption("Customer Lifetime Value (CLV)")
            st.markdown(f"**{format_inr(customer.get('lifetime_value'))}**")
            st.caption("Customer Segment")
            st.markdown(f"**{seg_label}**")
        with c2:
            st.caption("Successful Payments")
            st.markdown(f"<span style='color: #4ADE80; font-weight: 700;'>{customer.get('successful_payments', 0)}</span>", unsafe_allow_html=True)
            st.caption("Failed Payments")
            st.markdown(f"<span style='color: #F87171; font-weight: 700;'>{customer.get('failed_payments', 0)}</span>", unsafe_allow_html=True)
        with c3:
            st.caption("Historical Recovery Rate")
            st.markdown(f"**{format_percent(customer.get('historical_recovery_rate', 0.0))}**")
            st.caption("Account Age & Region")
            st.markdown(f"**{customer.get('account_age_days', 0)} days** ({str(customer.get('region', 'N/A')).title()})")


def render_ml_explainability_card(ml_data: Dict[str, Any]) -> None:
    """Renders ML prediction with calibrated probability bar and top SHAP factors."""
    prob = float(ml_data.get("recovery_probability", 0.0) or 0.0)
    prob_pct = prob * 100 if prob <= 1.0 else prob
    tier = ml_data.get("tier", "ACTIONABLE_OUTREACH")
    tier_color = TIER_COLORS.get(tier, "#3B82F6")

    with st.container(border=True):
        st.markdown("### 🧠 AI Recovery Probability")
        
        # Big metric & progress bar
        col_prob1, col_prob2 = st.columns([1, 2])
        with col_prob1:
            st.metric(label="Calibrated Likelihood", value=f"{prob_pct:.1f}%")
        with col_prob2:
            st.caption(f"Assigned Tier: **{tier.replace('_', ' ')}**")
            st.progress(min(max(prob_pct / 100.0, 0.0), 1.0))
            st.caption("🔴 <45% Suppress | 🟡 45-65% Outreach | 🟢 >65% Smart Retry")

        st.divider()
        st.markdown("**Key Influencing Factors (SHAP Explainability):**")
        
        factors = ml_data.get("top_factors", ml_data.get("factors", []))
        if factors:
            for f in factors:
                factor_name = f.get("feature", f.get("factor", "")).replace("_", " ").title()
                val = f.get("importance", 0.0)
                is_pos = val >= 0 if isinstance(val, (int, float)) else True
                icon = "🟢 Positively increases recovery chance" if is_pos else "🔴 Increases risk of failure"
                val_str = f"{val:+.3f}" if isinstance(val, (int, float)) else ""
                
                c_f1, c_f2 = st.columns([3, 1])
                with c_f1:
                    st.markdown(f"• **{factor_name}** — *{icon}*")
                with c_f2:
                    st.markdown(f"`{val_str}`")
        else:
            st.info("Feature importance explanation calculated via zero-leakage ML pipeline.")


def render_ai_decision_card(decision: Dict[str, Any]) -> None:
    """Renders the Decision Engine output with clean policy rationale."""
    tier = decision.get("tier", "HIGH_CONFIDENCE")
    strategy = decision.get("strategy", "SMART_RETRY")
    icon = STRATEGY_ICONS.get(strategy, "⚡")
    delay_val = decision.get('delay_hours')
    delay_str = f"{float(delay_val):.0f} Hours" if (delay_val is not None and str(delay_val) != "None") else "Immediate (0h)"
    is_human = decision.get('human_review_required', False)

    with st.container(border=True):
        st.markdown(f"### {icon} Recommended Strategy: **{strategy.replace('_', ' ')}**")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.caption("Action Plan")
            st.markdown(f"**{str(decision.get('recommended_action', strategy)).replace('_', ' ').title()}**")
        with c2:
            st.caption("Execution Delay")
            st.markdown(f"**{delay_str}**")
        with c3:
            st.caption("Review Status")
            if is_human:
                st.markdown("<span style='color: #F87171; font-weight: 700;'>⚠️ Human Review Required</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span style='color: #4ADE80; font-weight: 700;'>✅ Autonomous Execution</span>", unsafe_allow_html=True)

        st.divider()

        reasons = decision.get('reason_codes', [])
        if reasons:
            st.markdown("**Policy Reason Codes:**")
            badges = " ".join([f"`{r}`" for r in reasons])
            st.markdown(badges)

        explanation = decision.get('explanation', decision.get('reasoning', 'Autonomous policy recommendation based on real-time telemetry.'))
        st.info(f"💡 **AI Rationale:** {explanation}")


def render_customer_outreach_panel(outreach_data: Dict[str, Any]) -> None:
    """Renders customer outreach preview in a clean communication box."""
    channel = outreach_data.get("channel", "whatsapp").upper()
    channel_icons = {"WHATSAPP": "💬 WhatsApp Message", "SMS": "📱 SMS Alert", "EMAIL": "✉️ Email Outreach"}
    title = channel_icons.get(channel, f"💬 {channel} Outreach")

    with st.container(border=True):
        st.markdown(f"### {title}")
        st.caption("Tier 2 Personalized Customer Engagement")
        
        content = outreach_data.get('content', 'No message body generated.')
        st.text_area("Message Preview (Ready to Send)", value=content, height=120, disabled=True)
        
        st.caption("🔒 **Privacy Guard:** ML internal scores and bank diagnostics are scrubbed before customer delivery.")


def render_guided_demo_stepper() -> None:
    """Renders a clean, crystal-clear 7-step pipeline overview that everyone can understand."""
    with st.expander("ℹ️ **How RecoverAI Works (7-Step Autonomous Recovery Pipeline)**", expanded=True):
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1:
            st.markdown("**1. Failed**\n\n❌ Payment fails at gateway")
        with c2:
            st.markdown("**2. ML Score**\n\n🧠 Calibrate recovery likelihood")
        with c3:
            st.markdown("**3. Policy**\n\n⚖️ Match into 3-Tier strategy")
        with c4:
            st.markdown("**4. AI Agent**\n\n🤖 Plan retry schedule & channel")
        with c5:
            st.markdown("**5. Action**\n\n🚀 Execute retry or outreach")
        with c6:
            st.markdown("**6. Outcome**\n\n⚙️ Real-time gateway feedback")
        with c7:
            st.markdown("**7. Rescued**\n\n💎 Revenue recovered to ARR")
        
        st.success("🛡️ **Safety Guardrails:** Max 3 retries • Exponential backoff • Zero spam • Human review for VIP disputes")
