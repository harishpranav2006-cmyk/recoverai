"""
RecoverAI — Event Timeline Component (Premium Glassmorphism Dark Theme)
======================================================================
Renders chronological payment and recovery events with staggered animations,
gradient connector lines, and pulsing event markers.
"""

from __future__ import annotations

from typing import Any, Dict, List
import streamlit as st

from dashboard.config import COLORS


def render_event_timeline(events: List[Dict[str, Any]]) -> None:
    """Renders a vertical event timeline with animated staggered reveals and gradient connectors."""
    if not events:
        st.info("No events recorded for this payment.")
        return

    st.markdown(
        f"""
        <div style="background: {COLORS['glass_bg_strong']}; border: 1px solid {COLORS['border']}; border-radius: 14px; padding: 22px; box-shadow: 0 4px 16px rgba(0,0,0,0.5); backdrop-filter: blur(12px); animation: fadeInUp 0.4s ease-out both;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 18px;">
                <span style="font-size: 1.25rem;">⏱️</span>
                <span style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF;">Payment Event Timeline</span>
                <span style="background: {COLORS['primary']}18; color: {COLORS['primary_light']}; border: 1px solid {COLORS['primary']}40; padding: 2px 10px; border-radius: 9999px; font-size: 0.72rem; font-weight: 700;">{len(events)} Events</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

    event_colors = {
        "PAYMENT_FAILED": ("#EF4444", "#F87171", "❌"),
        "ML_PREDICTION": ("#3B82F6", "#60A5FA", "🧠"),
        "DECISION_MADE": ("#F59E0B", "#FBBF24", "⚖️"),
        "AGENT_STARTED": ("#A855F7", "#C084FC", "🤖"),
        "AGENT_COMPLETED": ("#A855F7", "#C084FC", "✅"),
        "RETRY_SCHEDULED": ("#3B82F6", "#60A5FA", "🕒"),
        "RETRY_ATTEMPT": ("#06B6D4", "#22D3EE", "⚡"),
        "RETRY_SUCCESS": ("#22C55E", "#4ADE80", "✅"),
        "RETRY_FAILED": ("#EF4444", "#F87171", "❌"),
        "RECOVERY_SUCCESS": ("#22C55E", "#4ADE80", "💎"),
        "OUTREACH_SENT": ("#F59E0B", "#FBBF24", "💬"),
        "SUPPRESSED": ("#6B7280", "#9CA3AF", "🛑"),
    }
    default_color = (COLORS["primary"], COLORS["primary_light"], "📌")

    for idx, event in enumerate(events):
        event_type = str(event.get("event_type", event.get("type", ""))).upper().replace(" ", "_")
        border_color, text_color, icon = event_colors.get(event_type, default_color)
        delay = min(0.1 + idx * 0.08, 1.2)
        is_last = idx == len(events) - 1

        timestamp = str(event.get("timestamp", ""))[:19]
        title = str(event.get("event_type", event.get("type", "Event"))).replace("_", " ").title()
        detail = event.get("detail", event.get("details", event.get("description", "")))

        connector_html = "" if is_last else f"""
            <div style="position: absolute; left: 19px; top: 38px; bottom: -6px; width: 2px; background: linear-gradient(180deg, {border_color}80, {border_color}20, transparent);"></div>
        """

        st.markdown(
            f"""
            <div style="display: flex; gap: 16px; position: relative; margin-bottom: 6px; animation: slideInLeft {delay + 0.3}s ease-out both;">
                <!-- Connector Line -->
                {connector_html}
                <!-- Pulsing Event Marker -->
                <div style="flex-shrink: 0; width: 40px; height: 40px; border-radius: 12px; background: {border_color}18; border: 2px solid {border_color}80; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; z-index: 1; transition: all 0.2s ease; box-shadow: 0 0 8px {border_color}30;"
                     onmouseover="this.style.boxShadow='0 0 20px {border_color}60'; this.style.transform='scale(1.1)';"
                     onmouseout="this.style.boxShadow='0 0 8px {border_color}30'; this.style.transform='scale(1)';">
                    {icon}
                </div>
                <!-- Event Content -->
                <div style="flex: 1; background: {COLORS['bg_dark']}; border: 1px solid {COLORS['border']}; border-radius: 10px; padding: 12px 16px; transition: all 0.2s ease;"
                     onmouseover="this.style.borderColor='{border_color}40';" onmouseout="this.style.borderColor='{COLORS['border']}';">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 700; color: {text_color}; font-size: 0.88rem;">{title}</span>
                        <span style="font-size: 0.72rem; color: {COLORS['text_dim']}; font-weight: 600; background: {COLORS['surface']}; padding: 2px 8px; border-radius: 6px;">{timestamp}</span>
                    </div>
                    {"<div style='font-size: 0.82rem; color: " + COLORS['text_secondary'] + "; line-height: 1.4;'>" + str(detail) + "</div>" if detail else ""}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
