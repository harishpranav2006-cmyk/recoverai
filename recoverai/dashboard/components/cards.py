"""
RecoverAI — Information & Decision Cards Component (Premium Glassmorphism Dark Theme)
====================================================================================
Modular dark-themed UI cards with glassmorphism, animated progress bars, hover interactions,
and the 7-step recovery pipeline stepper.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st

from dashboard.config import COLORS, STRATEGY_ICONS, TIER_COLORS
from dashboard.components.metrics import format_inr, format_percent


def render_payment_summary_card(payment: Dict[str, Any]) -> None:
    """Renders the core payment transaction summary with glassmorphism and gradient accent."""
    status_color = COLORS["success"] if payment.get("payment_success") or payment.get("recovered_after_failure") else COLORS["danger"]
    status_label = "RECOVERED" if payment.get("recovered_after_failure") else ("SUCCESS" if payment.get("payment_success") else "FAILED")

    st.markdown(
        f"""
        <div style="background: {COLORS['glass_bg_strong']}; border: 1px solid {COLORS['border']}; border-radius: 14px; padding: 22px; margin-bottom: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.5); backdrop-filter: blur(12px); position: relative; overflow: hidden; animation: fadeInUp 0.4s ease-out both; transition: all 0.3s ease;"
             onmouseover="this.style.borderColor='{status_color}50'" onmouseout="this.style.borderColor='{COLORS['border']}'">
            <!-- Accent Strip -->
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, {status_color}, {status_color}60, transparent);"></div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <span style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF;">💳 Payment <span style="color: #60A5FA;">{payment.get('id')}</span></span>
                <span style="background: {status_color}18; color: {status_color}; border: 1px solid {status_color}60; padding: 4px 14px; border-radius: 9999px; font-weight: 700; font-size: 0.78rem; backdrop-filter: blur(4px);">{status_label}</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.88rem;">
                <div style="padding: 8px 12px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};"><span style="color: {COLORS['text_secondary']}; font-size: 0.76rem;">Amount</span><br/><b style="color: #FFFFFF; font-size: 1.05rem;">{format_inr(payment.get('amount'))}</b></div>
                <div style="padding: 8px 12px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};"><span style="color: {COLORS['text_secondary']}; font-size: 0.76rem;">Method</span><br/><b style="color: #FFFFFF;">{str(payment.get('payment_method', '')).upper()}</b></div>
                <div style="padding: 8px 12px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};"><span style="color: {COLORS['text_secondary']}; font-size: 0.76rem;">Failure Reason</span><br/><b style="color: #F87171;">{str(payment.get('failure_reason', 'N/A')).replace('_', ' ').title()}</b></div>
                <div style="padding: 8px 12px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};"><span style="color: {COLORS['text_secondary']}; font-size: 0.76rem;">Category</span><br/><b style="color: #FFFFFF;">{str(payment.get('failure_category', 'N/A')).title()}</b></div>
                <div style="padding: 8px 12px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};"><span style="color: {COLORS['text_secondary']}; font-size: 0.76rem;">Retry Attempts</span><br/><b style="color: #FFFFFF;">{payment.get('retry_count', 0)} / 3</b></div>
                <div style="padding: 8px 12px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};"><span style="color: {COLORS['text_secondary']}; font-size: 0.76rem;">Timestamp</span><br/><b style="color: #FFFFFF;">{str(payment.get('timestamp', ''))[:19]}</b></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_customer_context_card(customer: Dict[str, Any]) -> None:
    """Renders the customer profile with glassmorphism and segment indicator."""
    segment = str(customer.get('segment', 'basic')).upper()
    seg_colors = {"ENTERPRISE": "#A855F7", "PREMIUM": "#3B82F6", "BASIC": "#6B7280", "FREE_TRIAL": "#F59E0B"}
    seg_color = seg_colors.get(segment, "#6B7280")
    
    st.markdown(
        f"""
        <div style="background: {COLORS['glass_bg_strong']}; border: 1px solid {COLORS['border']}; border-radius: 14px; padding: 22px; margin-bottom: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.5); backdrop-filter: blur(12px); position: relative; overflow: hidden; animation: fadeInUp 0.5s ease-out both; transition: all 0.3s ease;"
             onmouseover="this.style.borderColor='{seg_color}50'" onmouseout="this.style.borderColor='{COLORS['border']}'">
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, {seg_color}, {seg_color}60, transparent);"></div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <span style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF;">👤 Customer (<span style="color: #60A5FA;">{customer.get('id')}</span>)</span>
                <span style="background: {seg_color}18; color: {seg_color}; border: 1px solid {seg_color}60; padding: 4px 14px; border-radius: 9999px; font-weight: 700; font-size: 0.78rem;">{segment}</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.88rem;">
                <div style="padding: 8px 12px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};"><span style="color: {COLORS['text_secondary']}; font-size: 0.76rem;">Lifetime Value (CLV)</span><br/><b style="color: #FFFFFF; font-size: 1.05rem;">{format_inr(customer.get('lifetime_value'))}</b></div>
                <div style="padding: 8px 12px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};"><span style="color: {COLORS['text_secondary']}; font-size: 0.76rem;">Region</span><br/><b style="color: #FFFFFF;">{str(customer.get('region', 'N/A')).title()}</b></div>
                <div style="padding: 8px 12px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};"><span style="color: {COLORS['text_secondary']}; font-size: 0.76rem;">Successful Payments</span><br/><b style="color: #4ADE80;">{customer.get('successful_payments', 0)}</b></div>
                <div style="padding: 8px 12px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};"><span style="color: {COLORS['text_secondary']}; font-size: 0.76rem;">Failed Payments</span><br/><b style="color: #F87171;">{customer.get('failed_payments', 0)}</b></div>
                <div style="padding: 8px 12px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};"><span style="color: {COLORS['text_secondary']}; font-size: 0.76rem;">Historical Recovery Rate</span><br/><b style="color: #FFFFFF;">{format_percent(customer.get('historical_recovery_rate', 0.0))}</b></div>
                <div style="padding: 8px 12px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};"><span style="color: {COLORS['text_secondary']}; font-size: 0.76rem;">Account Age</span><br/><b style="color: #FFFFFF;">{customer.get('account_age_days', 0)} days</b></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ml_explainability_card(ml_data: Dict[str, Any]) -> None:
    """Renders ML prediction with animated progress bar and interactive SHAP factors."""
    prob = ml_data.get("recovery_probability", 0.0)
    prob_pct = prob * 100
    tier = ml_data.get("tier", "ACTIONABLE_OUTREACH")
    tier_color = TIER_COLORS.get(tier, COLORS["primary"])

    st.markdown(
        f"""
        <div style="background: {COLORS['glass_bg_strong']}; border: 1px solid {COLORS['border']}; border-radius: 14px; padding: 22px; margin-bottom: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.5); backdrop-filter: blur(12px); position: relative; overflow: hidden; animation: fadeInUp 0.5s ease-out both;">
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, {tier_color}, {tier_color}60, transparent);"></div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <span style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF;">🧠 Calibrated ML Prediction</span>
                <span style="background: {tier_color}18; color: {tier_color}; border: 1px solid {tier_color}60; padding: 4px 14px; border-radius: 9999px; font-weight: 700; font-size: 0.78rem; animation: pulseGlow 3s ease-in-out infinite;">{tier.replace('_', ' ')}</span>
            </div>
            <div style="margin-bottom: 18px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 8px;">
                    <span style="font-size: 0.86rem; color: {COLORS['text_secondary']}; font-weight: 600;">Calibrated Recovery Likelihood:</span>
                    <span style="font-size: 1.7rem; font-weight: 800; color: {tier_color}; animation: countUp 0.8s ease-out both;">{prob_pct:.1f}%</span>
                </div>
                <div style="width: 100%; height: 10px; background: {COLORS['border']}; border-radius: 9999px; overflow: hidden; position: relative;">
                    <div style="width: {min(max(prob_pct, 0), 100)}%; height: 100%; background: linear-gradient(90deg, {tier_color}, {tier_color}CC); border-radius: 9999px; box-shadow: 0 0 12px {tier_color}80; transition: width 1.5s cubic-bezier(0.4, 0, 0.2, 1);"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: {COLORS['text_dim']}; margin-top: 6px; font-weight: 600;">
                    <span>0% (Suppress)</span>
                    <span>45% (Outreach)</span>
                    <span>65% (Smart Retry)</span>
                    <span>100%</span>
                </div>
            </div>
            <div style="font-size: 0.78rem; color: {COLORS['text_secondary']}; margin-bottom: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;">
                SHAP Feature Attribution
            </div>
        """,
        unsafe_allow_html=True,
    )

    factors = ml_data.get("top_factors", ml_data.get("factors", []))
    if factors:
        for f in factors:
            factor_name = f.get("feature", f.get("factor", "")).replace("_", " ").title()
            val = f.get("importance", 0.0)
            is_positive = val >= 0 if isinstance(val, (int, float)) else True
            icon = "🟢 +" if is_positive else "🔴 −"
            color = "#4ADE80" if is_positive else "#F87171"
            val_str = f"{val:+.3f}" if isinstance(val, (int, float)) else ""
            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; padding: 8px 14px; background: {COLORS['bg_dark']}; border: 1px solid {COLORS['border']}; border-radius: 8px; margin-bottom: 5px; font-size: 0.84rem; transition: all 0.2s ease; cursor: default;"
                     onmouseover="this.style.borderColor='{color}40'; this.style.background='{color}08';" 
                     onmouseout="this.style.borderColor='{COLORS['border']}'; this.style.background='{COLORS['bg_dark']}';">
                    <span style="color: #FFFFFF;"><b>{icon}</b> {factor_name}</span>
                    <span style="font-weight: 700; color: {color};">{val_str}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("Feature importance explanation calculated via zero-leakage ML pipeline.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_ai_decision_card(decision: Dict[str, Any]) -> None:
    """Renders the Decision Engine output with glassmorphism and animated elements."""
    tier = decision.get("tier", "HIGH_CONFIDENCE")
    tier_color = TIER_COLORS.get(tier, COLORS["primary"])
    strategy = decision.get("strategy", "SMART_RETRY")
    icon = STRATEGY_ICONS.get(strategy, "⚡")

    delay_val = decision.get('delay_hours')
    delay_str = f"{float(delay_val):.0f} Hours" if (delay_val is not None and str(delay_val) != "None") else "Immediate"

    st.markdown(
        f"""
        <div style="background: {COLORS['glass_bg_strong']}; border: 1px solid {tier_color}40; border-radius: 14px; padding: 22px; margin-bottom: 16px; box-shadow: 0 4px 20px {tier_color}15; backdrop-filter: blur(12px); position: relative; overflow: hidden; animation: fadeInUp 0.6s ease-out both; transition: all 0.3s ease;"
             onmouseover="this.style.boxShadow='0 8px 32px {tier_color}25'" onmouseout="this.style.boxShadow='0 4px 20px {tier_color}15'">
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, {tier_color}, {tier_color}80, transparent);"></div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <span style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF;">{icon} AI Strategy: <span style="color: {tier_color};">{strategy.replace('_', ' ')}</span></span>
                <span style="background: {tier_color}; color: #000000; padding: 4px 14px; border-radius: 9999px; font-weight: 800; font-size: 0.78rem;">{tier.replace('_', ' ')}</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 16px; font-size: 0.86rem;">
                <div style="background: {COLORS['bg_dark']}; border: 1px solid {COLORS['border']}; padding: 12px; border-radius: 10px; transition: all 0.2s ease;" onmouseover="this.style.borderColor='{tier_color}40'" onmouseout="this.style.borderColor='{COLORS['border']}'">
                    <div style="color: {COLORS['text_dim']}; font-size: 0.72rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">Recommended Action</div>
                    <div style="font-weight: 800; font-size: 1rem; color: #FFFFFF; margin-top: 4px;">{str(decision.get('recommended_action', '')).replace('_', ' ').title()}</div>
                </div>
                <div style="background: {COLORS['bg_dark']}; border: 1px solid {COLORS['border']}; padding: 12px; border-radius: 10px; transition: all 0.2s ease;" onmouseover="this.style.borderColor='{tier_color}40'" onmouseout="this.style.borderColor='{COLORS['border']}'">
                    <div style="color: {COLORS['text_dim']}; font-size: 0.72rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">Execution Delay</div>
                    <div style="font-weight: 800; font-size: 1rem; color: #60A5FA; margin-top: 4px;">{delay_str}</div>
                </div>
                <div style="background: {COLORS['bg_dark']}; border: 1px solid {COLORS['border']}; padding: 12px; border-radius: 10px; transition: all 0.2s ease;" onmouseover="this.style.borderColor='{tier_color}40'" onmouseout="this.style.borderColor='{COLORS['border']}'">
                    <div style="color: {COLORS['text_dim']}; font-size: 0.72rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">Human Review Flag</div>
                    <div style="font-weight: 800; font-size: 1rem; color: {'#F87171' if decision.get('human_review_required') else '#4ADE80'}; margin-top: 4px;">{'⚠️ Required' if decision.get('human_review_required') else '✅ Autonomous'}</div>
                </div>
            </div>
            <div style="margin-bottom: 14px;">
                <span style="color: {COLORS['text_dim']}; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Policy Reason Codes:</span><br/>
                <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px;">
                {' '.join([f"<span style='background: #1E3A8A; color: #93C5FD; border: 1px solid #2563EB40; padding: 3px 10px; border-radius: 6px; font-size: 0.74rem; font-weight: 700;'>{r}</span>" for r in decision.get('reason_codes', [])])}
                </div>
            </div>
            <div style="font-size: 0.88rem; color: #FFFFFF; line-height: 1.5; background: rgba(5, 78, 59, 0.12); border-left: 4px solid #22C55E; padding: 12px 16px; border-radius: 0 10px 10px 0; backdrop-filter: blur(4px);">
                <b>Rationale:</b> {decision.get('explanation', decision.get('reasoning', 'Autonomous policy recommendation based on multi-factor telemetry.'))}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_customer_outreach_panel(outreach_data: Dict[str, Any]) -> None:
    """Renders the customer outreach message preview with glassmorphism."""
    channel = outreach_data.get("channel", "whatsapp").upper()
    channel_icons = {"WHATSAPP": "💬", "SMS": "📱", "EMAIL": "✉️"}
    channel_colors = {"WHATSAPP": "#25D366", "SMS": "#3B82F6", "EMAIL": "#F59E0B"}
    icon = channel_icons.get(channel, "💬")
    ch_color = channel_colors.get(channel, "#F59E0B")

    st.markdown(
        f"""
        <div style="background: {COLORS['glass_bg_strong']}; border: 1px solid {COLORS['border']}; border-radius: 14px; padding: 22px; margin-bottom: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.5); backdrop-filter: blur(12px); position: relative; overflow: hidden; animation: fadeInUp 0.6s ease-out both;">
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, {ch_color}, {ch_color}60, transparent);"></div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                <span style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF;">{icon} Personalized Outreach ({channel})</span>
                <span style="background: {ch_color}18; color: {ch_color}; border: 1px solid {ch_color}60; padding: 4px 14px; border-radius: 9999px; font-weight: 700; font-size: 0.78rem;">Tier 2 Communication</span>
            </div>
            <div style="background: {COLORS['bg_dark']}; border: 1px solid {COLORS['border']}; border-radius: 10px; padding: 16px; font-family: 'Inter', monospace; font-size: 0.88rem; color: #FFFFFF; margin-bottom: 14px; white-space: pre-wrap; line-height: 1.6;">
{outreach_data.get('content', 'No message body generated.')}
            </div>
            <div style="font-size: 0.76rem; color: {COLORS['text_secondary']}; display: flex; align-items: center; gap: 6px;">
                <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #22C55E;"></span>
                <b>Privacy Guard Active:</b> Internal ML probabilities, SHAP values, and system reason codes are strictly scrubbed before dispatch.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_guided_demo_stepper() -> None:
    """Renders the 7-step pipeline stepper with animated connecting arrows and glass styling."""
    steps = [
        ("📄", "Payment Failed", "Involuntary churn occurs", "#E11D48", "#FB7185", "#4C0519"),
        ("🧠", "ML Probability", "Calibrated prediction", "#2563EB", "#60A5FA", "#1E3A8A"),
        ("⚖️", "Decision Engine", "Deterministic 3-Tier", "#D97706", "#FBBF24", "#451A03"),
        ("🤖", "AI Agent", "Orchestrates context", "#059669", "#4ADE80", "#064E3B"),
        ("🚀", "Smart Action", "Timed retry or outreach", "#7C3AED", "#C084FC", "#3B0764"),
        ("⚙️", "Simulated Result", "Gateway execution", "#0891B2", "#22D3EE", "#164E63"),
        ("📊", "Revenue Impact", "Rescued ARR updated", "#EA580C", "#FB923C", "#EA580C"),
    ]
    
    steps_html = ""
    for idx, (icon, title, desc, border, color, bg) in enumerate(steps):
        step_number = idx + 1
        arrow = f'<div style="color: {COLORS["text_dim"]}; font-size: 1.1rem; font-weight: 800; opacity: 0.5;">→</div>' if idx < 6 else ""
        steps_html += f"""
            <div style="background: {COLORS['bg_dark']}; border: 1px solid {border}60; border-radius: 12px; padding: 12px 10px; text-align: center; flex: 1; min-width: 120px; transition: all 0.3s ease; cursor: default;"
                 onmouseover="this.style.borderColor='{border}'; this.style.boxShadow='0 0 15px {border}30';" 
                 onmouseout="this.style.borderColor='{border}60'; this.style.boxShadow='none';">
                <div style="color: {color}; font-size: 0.68rem; font-weight: 700; text-align: left; margin-bottom: 2px;">{step_number}</div>
                <div style="background: {bg}; width: 36px; height: 36px; border-radius: 10px; margin: 0 auto 8px auto; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; color: {color};">{icon}</div>
                <div style="font-weight: 800; font-size: 0.82rem; color: #FFFFFF;">{title}</div>
                <div style="font-size: 0.7rem; color: {COLORS['text_secondary']}; margin-top: 4px; line-height: 1.2;">{desc}</div>
            </div>
            {arrow}
        """
    
    st.markdown(
        f"""
        <div style="background: {COLORS['glass_bg_strong']}; border: 1px solid {COLORS['border']}; border-radius: 14px; padding: 22px; margin-bottom: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.5); backdrop-filter: blur(12px); animation: fadeInUp 0.5s ease-out both;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 18px;">
                <span style="font-size: 1.25rem;">🚀</span>
                <span style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF;">Autonomous Recovery Pipeline</span>
                <span style="font-size: 0.82rem; color: {COLORS['text_dim']}; margin-left: 6px;">How RecoverAI rescues involuntary churn end-to-end</span>
            </div>
            
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 6px; overflow-x: auto; padding-bottom: 6px;">
                {steps_html}
            </div>

            <div style="margin-top: 18px; background: rgba(5, 78, 59, 0.12); border: 1px solid #05966940; border-radius: 10px; padding: 10px 16px; text-align: center; font-size: 0.78rem; color: #4ADE80; font-weight: 700; backdrop-filter: blur(4px);">
                🛡️ Safety by Design: Policy Guardrails • Retry Limits • State Machine • Idempotency • Audit Trail
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
