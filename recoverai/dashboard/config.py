"""
RecoverAI — Dashboard Configuration (Premium Fintech Dark Palette)
=======================================================================
Centralized high-contrast dark fintech styling, color tokens, animation constants, and metadata.
"""

from __future__ import annotations

import os

# API Configuration — Cloud Environment & Streamlit Secrets Resolution
def get_api_base_url() -> str:
    """
    Resolves the FastAPI backend base URL using the following priority:
    1. Streamlit secrets (`st.secrets["RECOVERAI_API_URL"]` or `st.secrets["API_BASE_URL"]`)
    2. Environment variables (`RECOVERAI_API_URL` or `API_BASE_URL`)
    3. Default local development fallback (`http://localhost:8000/api/v1`)
    """
    # 1. Check Streamlit Secrets (for Streamlit Community Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "RECOVERAI_API_URL" in st.secrets:
                val = str(st.secrets["RECOVERAI_API_URL"]).strip().rstrip("/")
                if val:
                    return val
            if "API_BASE_URL" in st.secrets:
                val = str(st.secrets["API_BASE_URL"]).strip().rstrip("/")
                if val:
                    return val
    except Exception:
        pass

    # 2. Check Environment Variables
    env_url = os.getenv("RECOVERAI_API_URL") or os.getenv("API_BASE_URL")
    if env_url and env_url.strip():
        return env_url.strip().rstrip("/")

    # 3. Local fallback
    return "http://localhost:8000/api/v1"


def get_api_timeout_seconds() -> int:
    """Resolves API client timeout from secrets, environment, or default (15s)."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "API_TIMEOUT_SECONDS" in st.secrets:
            return int(st.secrets["API_TIMEOUT_SECONDS"])
    except Exception:
        pass
    return int(os.getenv("API_TIMEOUT_SECONDS", "15"))


API_BASE_URL = get_api_base_url()
API_TIMEOUT_SECONDS = get_api_timeout_seconds()

# Application Metadata
APP_TITLE = "RecoverAI — Autonomous AI Revenue Recovery"
APP_SUBTITLE = "Autonomous AI Revenue Recovery Platform"
APP_ICON = "⚡"
BUILDATHON_TRACK = "Razorpay AI Buildathon Prototype"
SIMULATION_NOTICE = "Synthetic Data • Simulated Payments • Buildathon Prototype"
APP_VERSION = "2.0.0"

# Centralized High-Contrast Dark Fintech Palette
# Canonical keys and backwards-compatible aliases for all components
COLORS = {
    # Core Surfaces & Backgrounds
    "bg_dark": "#0B0F17",           # Deep main background (#0B0F17)
    "background": "#0B0F17",        # Alias for main background
    "bg_light": "#111827",          # Elevated surface background
    "bg_secondary": "#172033",      # Secondary background
    "sidebar_bg": "#070A10",        # Deep sidebar background
    "surface": "#111827",           # Main card & surface background (#111827)
    "surface_alt": "#172033",       # Alternate surface background (#172033)
    "card_bg": "#111827",           # Alias for card surface
    "card_bg_alt": "#172033",       # Alias for alternate card surface
    
    # Glass-morphism Surfaces
    "glass_bg": "rgba(17, 24, 39, 0.75)",         # Translucent glass background
    "glass_bg_strong": "rgba(17, 24, 39, 0.88)",  # Stronger glass effect
    "glass_border": "rgba(59, 130, 246, 0.15)",   # Subtle blue glass border
    "glass_border_hover": "rgba(59, 130, 246, 0.35)",  # Hover glass border
    
    # Borders & Dividers
    "border": "#1F2937",            # High-contrast container border (#1F2937)
    "border_light": "#374151",      # Lighter border for hover states
    "card_border": "#1F2937",       # Alias for card border
    "card_border_glow": "#2563EB",  # Primary glow border accent
    
    # Core Brand & Semantic Accents
    "primary": "#3B82F6",           # Primary fintech blue (#3B82F6)
    "primary_dark": "#1D4ED8",      # Deep blue
    "primary_light": "#60A5FA",     # Light sky blue
    "primary_glow": "rgba(59, 130, 246, 0.25)",  # Blue glow for shadows
    "accent": "#3B82F6",            # Alias for primary accent
    "success": "#22C55E",           # Recovery success green (#22C55E)
    "success_glow": "#4ADE80",      # Light emerald green
    "success_bg": "rgba(34, 197, 94, 0.12)",     # Success background tint
    "warning": "#F59E0B",           # Outreach & action amber (#F59E0B)
    "warning_glow": "#FBBF24",      # Light gold
    "warning_bg": "rgba(245, 158, 11, 0.12)",    # Warning background tint
    "danger": "#EF4444",            # Failure & loss red (#EF4444)
    "danger_glow": "#F87171",       # Light rose red
    "danger_bg": "rgba(239, 68, 68, 0.12)",      # Danger background tint
    "error": "#EF4444",             # Alias for danger red
    "info": "#06B6D4",              # Telemetry & info cyan (#06B6D4)
    "purple": "#A855F7",            # Agent & AI purple accent
    "purple_glow": "rgba(168, 85, 247, 0.25)",   # Purple glow
    "cyan": "#06B6D4",              # Cyan accent
    "navy": "#FFFFFF",              # High-contrast white for headers
    
    # High-Contrast Typography
    "text_primary": "#FFFFFF",      # Primary bold headers & values (#FFFFFF)
    "text": "#FFFFFF",              # Alias for primary text
    "text_dark": "#FFFFFF",         # Alias for dark-mode primary text
    "text_secondary": "#E5E7EB",    # High-contrast secondary text (#E5E7EB)
    "text_muted": "#E5E7EB",        # Alias for secondary text (accessible contrast)
    "text_dim": "#9CA3AF",          # Tertiary / metadata text
    
    # Gradients
    "gradient_primary": "linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)",
    "gradient_success": "linear-gradient(135deg, #22C55E 0%, #16A34A 100%)",
    "gradient_warning": "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)",
    "gradient_danger": "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)",
    "gradient_purple": "linear-gradient(135deg, #A855F7 0%, #7C3AED 100%)",
    "gradient_hero": "linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%)",
}

# Tiers & Strategies Styling Map
TIER_COLORS = {
    "HIGH_CONFIDENCE": "#22C55E",       # Green
    "ACTIONABLE_OUTREACH": "#F59E0B",   # Amber
    "SUPPRESS_OR_ESCALATE": "#EF4444",  # Red
}

STRATEGY_ICONS = {
    "SMART_RETRY": "⚡",
    "CUSTOMER_OUTREACH": "💬",
    "PAYMENT_METHOD_UPDATE": "💳",
    "GRACE_PERIOD_EXTEND": "⏳",
    "HUMAN_REVIEW": "👤",
    "SUPPRESS_RETRY": "🛑",
    "SUPPRESSION": "🛑",
}

STATUS_BADGES = {
    "RECOVERED": ("#22C55E", "✅ Recovered"),
    "FAILED": ("#EF4444", "❌ Failed"),
    "RETRY_SCHEDULED": ("#60A5FA", "🕒 Retry Scheduled"),
    "RETRYING": ("#A855F7", "🔄 Retrying"),
    "WAITING_FOR_CUSTOMER": ("#F59E0B", "⏳ Waiting for Customer"),
    "SUPPRESSED": ("#9CA3AF", "🛑 Suppressed"),
    "ESCALATED_HUMAN_REVIEW": ("#EC4899", "👤 Escalated to Support"),
}


# -------------------------------------------------------------------------
# CSS Animation Keyframes (reusable across components)
# -------------------------------------------------------------------------
CSS_ANIMATIONS = """
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 8px rgba(59, 130, 246, 0.3); }
    50% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.6); }
}
@keyframes pulseGreen {
    0%, 100% { box-shadow: 0 0 6px #22C55E; }
    50% { box-shadow: 0 0 18px #22C55E; }
}
@keyframes pulseRed {
    0%, 100% { box-shadow: 0 0 6px #EF4444; }
    50% { box-shadow: 0 0 18px #EF4444; }
}
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
@keyframes countUp {
    from { opacity: 0; transform: scale(0.8); }
    to { opacity: 1; transform: scale(1); }
}
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes borderGlow {
    0%, 100% { border-color: rgba(59, 130, 246, 0.2); }
    50% { border-color: rgba(59, 130, 246, 0.5); }
}
"""
