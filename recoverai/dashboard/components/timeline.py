"""
RecoverAI — Event Timeline Component (Clean & Readable)
======================================================
Renders chronological payment and recovery lifecycle events using
clean Streamlit containers and status indicators.
"""

from __future__ import annotations

from typing import Any, Dict, List
import streamlit as st


def render_event_timeline(events: List[Dict[str, Any]]) -> None:
    """Renders a chronological event timeline cleanly using native Streamlit elements."""
    if not events:
        st.info("No events recorded for this payment.")
        return

    with st.container(border=True):
        st.markdown(f"### ⏱️ Payment Event Timeline ({len(events)} Events)")
        st.caption("Chronological audit history of payment failure, ML scoring, and recovery actions.")
        st.divider()

        event_icons = {
            "PAYMENT_FAILED": "❌",
            "ML_PREDICTION": "🧠",
            "DECISION_MADE": "⚖️",
            "AGENT_STARTED": "🤖",
            "AGENT_COMPLETED": "✅",
            "RETRY_SCHEDULED": "🕒",
            "RETRY_ATTEMPT": "⚡",
            "RETRY_SUCCESS": "✅",
            "RETRY_FAILED": "❌",
            "RECOVERY_SUCCESS": "💎",
            "OUTREACH_SENT": "💬",
            "SUPPRESSED": "🛑",
        }

        for idx, event in enumerate(events):
            event_type = str(event.get("event_type", event.get("type", ""))).upper().replace(" ", "_")
            icon = event_icons.get(event_type, "📌")
            title = str(event.get("event_type", event.get("type", "Event"))).replace("_", " ").title()
            timestamp = str(event.get("timestamp", ""))[:19]
            detail = event.get("detail", event.get("details", event.get("description", "")))

            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"{icon} **{title}**")
                if detail:
                    st.caption(str(detail))
            with c2:
                st.markdown(f"`{timestamp}`")
            
            if idx < len(events) - 1:
                st.markdown("---")
