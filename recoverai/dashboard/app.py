"""
RecoverAI — Autonomous AI Revenue Recovery Dashboard
====================================================
Main Streamlit application entrypoint with premium glassmorphism dark theme,
micro-animations, interactive navigation, and polished fintech aesthetics.
"""

from __future__ import annotations

import base64
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

from dashboard.api_client import api_client
from dashboard.config import (
    APP_ICON, APP_SUBTITLE, APP_TITLE, APP_VERSION, COLORS,
    CSS_ANIMATIONS, SIMULATION_NOTICE,
)
from dashboard.pages import (
    render_ai_decisions_page,
    render_analytics_page,
    render_customers_page,
    render_overview_page,
    render_payments_page,
    render_recovery_queue_page,
    render_system_page,
)

PAGES = [
    "🏠 Overview",
    "🎯 Recovery Queue",
    "💳 Payments",
    "👤 Customers",
    "🤖 AI Decisions",
    "📊 Analytics",
    "⚙️ System",
]


def init_session_state() -> None:
    """Initializes global session state variables for cross-page navigation and action results."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = PAGES[0]
    if "selected_payment_id" not in st.session_state:
        st.session_state.selected_payment_id = "P000004"
    if "selected_customer_id" not in st.session_state:
        st.session_state.selected_customer_id = "C00001"
    if "selected_decision_id" not in st.session_state:
        st.session_state.selected_decision_id = None
    if "last_action_result" not in st.session_state:
        st.session_state.last_action_result = None
    if "api_latency_ms" not in st.session_state:
        st.session_state.api_latency_ms = None


def navigate_to(page_keyword: str, **kwargs: Any) -> None:
    """
    Programmatic navigation helper.
    Sets any extra state variables and switches active page cleanly without key collisions.
    """
    for k, v in kwargs.items():
        st.session_state[k] = v

    for p in PAGES:
        if page_keyword.lower() in p.lower():
            st.session_state.current_page = p
            break
    st.rerun()


def _get_logo_base64() -> Optional[str]:
    """Load the logo image and return its base64-encoded data URI."""
    logo_path = Path(__file__).parent / "logo.jpg"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/jpeg;base64,{data}"
    return None


def apply_custom_css() -> None:
    """Injects premium glassmorphism dark theme CSS with micro-animations."""
    logo_uri = _get_logo_base64()
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

            {CSS_ANIMATIONS}

            /* Hide Streamlit Default MPA Navigation List */
            [data-testid="stSidebarNav"],
            ul[data-testid="stSidebarNavItems"],
            div[data-testid="stSidebarNavSeparator"] {{
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
            }}

            /* Global Root & Typography */
            html, body, [class*="css"], .stApp {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                background-color: {COLORS['bg_dark']} !important;
                color: {COLORS['text_primary']} !important;
            }}

            /* Main Container Padding */
            .main .block-container {{
                padding-top: 1.5rem !important;
                padding-bottom: 3rem !important;
                max-width: 1440px !important;
                background-color: {COLORS['bg_dark']} !important;
            }}

            /* Top App Header & Toolbar */
            header[data-testid="stHeader"] {{
                background-color: {COLORS['bg_dark']} !important;
                backdrop-filter: blur(12px) !important;
            }}

            /* ================================================================
               CUSTOM SCROLLBAR
               ================================================================ */
            ::-webkit-scrollbar {{
                width: 6px;
                height: 6px;
            }}
            ::-webkit-scrollbar-track {{
                background: {COLORS['bg_dark']};
            }}
            ::-webkit-scrollbar-thumb {{
                background: #374151;
                border-radius: 10px;
            }}
            ::-webkit-scrollbar-thumb:hover {{
                background: {COLORS['primary']};
            }}

            /* ================================================================
               SIDEBAR — PREMIUM DARK STYLING
               ================================================================ */
            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, #070A10 0%, #0B0F17 100%) !important;
                border-right: 1px solid {COLORS['border']} !important;
            }}
            [data-testid="stSidebar"] > div:first-child {{
                background: transparent !important;
            }}

            /* ================================================================
               GLASSMORPHISM METRIC CARDS
               ================================================================ */
            .stMetric {{
                background: {COLORS['glass_bg_strong']} !important;
                border: 1px solid {COLORS['border']} !important;
                padding: 16px 20px !important;
                border-radius: 14px !important;
                box-shadow: 0 4px 16px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.03) !important;
                backdrop-filter: blur(12px) !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                animation: fadeInUp 0.5s ease-out both;
            }}
            .stMetric:hover {{
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 24px rgba(0,0,0,0.6), 0 0 20px {COLORS['primary_glow']} !important;
                border-color: {COLORS['glass_border_hover']} !important;
            }}
            .stMetric label {{
                color: {COLORS['text_secondary']} !important;
                font-size: 0.78rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.8px !important;
            }}
            .stMetric [data-testid="stMetricValue"] {{
                color: {COLORS['text_primary']} !important;
                font-weight: 800 !important;
                animation: countUp 0.6s ease-out both;
            }}

            /* ================================================================
               BUTTONS — INTERACTIVE WITH GLOW & LIFT
               ================================================================ */
            /* Primary Button */
            .stButton > button[kind="primary"] {{
                background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 50%, #3B82F6 100%) !important;
                background-size: 200% 200% !important;
                color: {COLORS['text_primary']} !important;
                font-weight: 700 !important;
                border-radius: 10px !important;
                border: 1px solid rgba(96, 165, 250, 0.4) !important;
                padding: 0.55rem 1.3rem !important;
                box-shadow: 0 0 15px rgba(37, 99, 235, 0.3), 0 4px 12px rgba(0,0,0,0.3) !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                position: relative !important;
                overflow: hidden !important;
            }}
            .stButton > button[kind="primary"]::after {{
                content: '';
                position: absolute;
                top: 0; left: -100%; width: 100%; height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent);
                transition: left 0.5s ease;
            }}
            .stButton > button[kind="primary"]:hover {{
                background-position: 100% 50% !important;
                box-shadow: 0 0 30px rgba(96, 165, 250, 0.5), 0 8px 24px rgba(0,0,0,0.4) !important;
                transform: translateY(-2px) !important;
                border-color: #60A5FA !important;
            }}
            .stButton > button[kind="primary"]:hover::after {{
                left: 100%;
            }}
            .stButton > button[kind="primary"]:active {{
                transform: translateY(0px) scale(0.98) !important;
                box-shadow: 0 0 10px rgba(37, 99, 235, 0.4) !important;
            }}

            /* Secondary Buttons */
            .stButton > button[kind="secondary"], .stButton > button {{
                background: {COLORS['glass_bg_strong']} !important;
                color: {COLORS['text_primary']} !important;
                border: 1px solid {COLORS['border']} !important;
                border-radius: 10px !important;
                font-weight: 600 !important;
                backdrop-filter: blur(8px) !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
            }}
            .stButton > button:hover {{
                border-color: {COLORS['primary']} !important;
                color: {COLORS['primary_light']} !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 16px rgba(0,0,0,0.4), 0 0 12px {COLORS['primary_glow']} !important;
                background: rgba(59, 130, 246, 0.08) !important;
            }}
            .stButton > button:active {{
                transform: translateY(0px) scale(0.97) !important;
            }}

            /* ================================================================
               NAVIGATION RADIO PILLS IN SIDEBAR
               ================================================================ */
            [data-testid="stSidebar"] div[role="radiogroup"] > label {{
                background-color: transparent !important;
                padding: 10px 16px !important;
                border-radius: 10px !important;
                margin-bottom: 3px !important;
                color: {COLORS['text_dim']} !important;
                font-weight: 600 !important;
                font-size: 0.92rem !important;
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
                border-left: 3px solid transparent !important;
            }}
            [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
                background-color: rgba(59, 130, 246, 0.06) !important;
                color: {COLORS['text_primary']} !important;
                border-left-color: rgba(59, 130, 246, 0.3) !important;
            }}
            [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"],
            [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {{
                background: linear-gradient(90deg, rgba(59, 130, 246, 0.12) 0%, transparent 100%) !important;
                border-left: 3px solid {COLORS['primary']} !important;
                color: {COLORS['text_primary']} !important;
                font-weight: 700 !important;
                box-shadow: inset 0 0 20px rgba(59, 130, 246, 0.05) !important;
            }}

            /* ================================================================
               FORM INPUTS — GLASS STYLE
               ================================================================ */
            div[data-baseweb="select"] > div,
            div[data-baseweb="input"] > div,
            .stTextInput > div > div > input,
            .stNumberInput > div > div > input {{
                background-color: {COLORS['surface']} !important;
                color: {COLORS['text_primary']} !important;
                border: 1px solid {COLORS['border']} !important;
                border-radius: 10px !important;
                transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
            }}
            .stTextInput > div > div > input:focus,
            .stNumberInput > div > div > input:focus {{
                border-color: {COLORS['primary']} !important;
                box-shadow: 0 0 0 2px {COLORS['primary_glow']} !important;
            }}

            /* ================================================================
               EXPANDERS — GLASS PANELS
               ================================================================ */
            .streamlit-expanderHeader {{
                background: {COLORS['glass_bg_strong']} !important;
                color: {COLORS['text_primary']} !important;
                border: 1px solid {COLORS['border']} !important;
                border-radius: 12px !important;
                font-weight: 700 !important;
                backdrop-filter: blur(8px) !important;
                transition: all 0.2s ease !important;
            }}
            .streamlit-expanderHeader:hover {{
                border-color: {COLORS['glass_border_hover']} !important;
            }}
            .streamlit-expanderContent {{
                background-color: {COLORS['bg_dark']} !important;
                border: 1px solid {COLORS['border']} !important;
                border-top: none !important;
                border-radius: 0 0 12px 12px !important;
            }}

            /* ================================================================
               DATAFRAMES — THEMED
               ================================================================ */
            [data-testid="stDataFrame"] {{
                background: {COLORS['glass_bg_strong']} !important;
                border: 1px solid {COLORS['border']} !important;
                border-radius: 12px !important;
                overflow: hidden !important;
                backdrop-filter: blur(8px) !important;
            }}

            /* ================================================================
               HORIZONTAL RULES
               ================================================================ */
            hr {{
                border-color: {COLORS['border']} !important;
                margin: 1.5rem 0 !important;
                opacity: 0.5 !important;
            }}

            /* ================================================================
               TABS STYLING
               ================================================================ */
            .stTabs [data-baseweb="tab-list"] {{
                gap: 4px !important;
                background: {COLORS['surface']} !important;
                border-radius: 12px !important;
                padding: 4px !important;
                border: 1px solid {COLORS['border']} !important;
            }}
            .stTabs [data-baseweb="tab"] {{
                border-radius: 8px !important;
                font-weight: 600 !important;
                padding: 8px 16px !important;
                transition: all 0.2s ease !important;
            }}
            .stTabs [aria-selected="true"] {{
                background: {COLORS['primary']} !important;
                color: white !important;
            }}

            /* ================================================================
               TOAST/SUCCESS/ERROR BANNERS
               ================================================================ */
            .stAlert {{
                border-radius: 12px !important;
                backdrop-filter: blur(8px) !important;
                animation: fadeInUp 0.4s ease-out both !important;
            }}

            /* ================================================================
               PLOTLY CHART CONTAINERS
               ================================================================ */
            [data-testid="stPlotlyChart"] {{
                background: {COLORS['glass_bg_strong']} !important;
                border: 1px solid {COLORS['border']} !important;
                border-radius: 14px !important;
                padding: 8px !important;
                box-shadow: 0 4px 16px rgba(0,0,0,0.4) !important;
                backdrop-filter: blur(8px) !important;
                transition: all 0.3s ease !important;
            }}
            [data-testid="stPlotlyChart"]:hover {{
                border-color: {COLORS['glass_border_hover']} !important;
                box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 15px {COLORS['primary_glow']} !important;
            }}

            /* ================================================================
               SELECTBOX DROPDOWN
               ================================================================ */
            div[data-baseweb="popover"] {{
                background-color: {COLORS['surface']} !important;
                border: 1px solid {COLORS['border']} !important;
                border-radius: 10px !important;
            }}

            /* ================================================================
               CHECKBOX & RADIO STYLING
               ================================================================ */
            .stCheckbox label, .stRadio label {{
                transition: color 0.2s ease !important;
            }}
            .stCheckbox label:hover, .stRadio label:hover {{
                color: {COLORS['primary_light']} !important;
            }}

            /* ================================================================
               DOWNLOAD BUTTON
               ================================================================ */
            .stDownloadButton > button {{
                background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
                color: white !important;
                border: 1px solid #34D399 !important;
                border-radius: 10px !important;
                font-weight: 700 !important;
            }}
            .stDownloadButton > button:hover {{
                box-shadow: 0 0 20px rgba(52, 211, 153, 0.4) !important;
                transform: translateY(-1px) !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Main dashboard application orchestration."""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state()
    apply_custom_css()

    logo_uri = _get_logo_base64()

    # 1. Sidebar Navigation & Branding
    with st.sidebar:
        # Premium Logo & Branding Header
        logo_html = f'<img src="{logo_uri}" style="width: 40px; height: 40px; border-radius: 10px; box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);"/>' if logo_uri else '<span style="font-size: 1.8rem; filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.6));">⚡</span>'
        
        st.markdown(
            f"""
            <div style="padding: 12px 0 18px 0; border-bottom: 1px solid {COLORS['border']}; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    {logo_html}
                    <div>
                        <div style="font-size: 1.35rem; font-weight: 900; color: #FFFFFF; letter-spacing: -0.5px; line-height: 1.2;">
                            Recover<span style="background: linear-gradient(135deg, #3B82F6, #60A5FA); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AI</span>
                        </div>
                        <div style="font-size: 0.7rem; color: {COLORS['text_dim']}; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">
                            {APP_SUBTITLE}
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        current_idx = (
            PAGES.index(st.session_state.current_page)
            if st.session_state.current_page in PAGES
            else 0
        )

        nav_choice = st.radio(
            "NAVIGATION",
            PAGES,
            index=current_idx,
            label_visibility="collapsed",
        )

        # Update state when user clicks radio
        if nav_choice != st.session_state.current_page:
            st.session_state.current_page = nav_choice
            st.rerun()

        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("---")

        # 2. Live API Health Probe with animated status indicators
        t0 = time.perf_counter()
        health_data, h_err = api_client.get_health()
        latency = (time.perf_counter() - t0) * 1000
        st.session_state.api_latency_ms = round(latency, 1)

        if not isinstance(health_data, dict):
            health_data = {}

        api_connected = bool(health_data) and (
            health_data.get("status") in ["healthy", "alive", "ready"]
            or health_data.get("database") == "connected"
        )
        db_ok = api_connected and (health_data.get("database") in ["connected", "healthy"])
        ml_ok = api_connected and (health_data.get("ml_model") in ["available", "loaded"])

        pulse_anim = "animation: pulseGreen 2s ease-in-out infinite;" if api_connected else "animation: pulseRed 2s ease-in-out infinite;"
        
        st.markdown(
            f"""
            <div style="background: {COLORS['glass_bg_strong']}; border: 1px solid {COLORS['border']}; border-radius: 12px; padding: 16px; font-size: 0.8rem; color: #FFFFFF; box-shadow: 0 4px 16px rgba(0,0,0,0.5); backdrop-filter: blur(12px); animation: fadeInUp 0.5s ease-out both;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; color: #FFFFFF;">
                        <span style="display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: {'#22C55E' if api_connected else '#EF4444'}; {pulse_anim}"></span>
                        <span>{'All Systems Active' if api_connected else 'API Disconnected'}</span>
                    </div>
                    <span style="font-size: 0.7rem; color: {COLORS['text_dim']}; background: {COLORS['surface']}; padding: 2px 8px; border-radius: 6px; font-weight: 600;">{st.session_state.api_latency_ms}ms</span>
                </div>
                <div style="display: flex; flex-direction: column; gap: 6px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};">
                        <span style="color: {COLORS['text_secondary']}; font-size: 0.78rem;">✓ REST API</span>
                        <span style="color: {'#4ADE80' if api_connected else '#F87171'}; font-weight: 700; font-size: 0.78rem;">{'Healthy' if api_connected else 'Offline'}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};">
                        <span style="color: {COLORS['text_secondary']}; font-size: 0.78rem;">✓ ML Model</span>
                        <span style="color: {'#4ADE80' if ml_ok else '#F87171'}; font-weight: 700; font-size: 0.78rem;">{'Loaded' if ml_ok else 'Unavailable'}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; background: {COLORS['bg_dark']}; border-radius: 8px; border: 1px solid {COLORS['border']};">
                        <span style="color: {COLORS['text_secondary']}; font-size: 0.78rem;">✓ SQLite DB</span>
                        <span style="color: {'#4ADE80' if db_ok else '#F87171'}; font-weight: 700; font-size: 0.78rem;">{'50K Records' if db_ok else 'Disconnected'}</span>
                    </div>
                </div>
            </div>
            
            <div style="background: {COLORS['bg_dark']}; border: 1px solid {COLORS['border']}; border-radius: 10px; padding: 10px; margin-top: 12px; text-align: center; backdrop-filter: blur(8px);">
                <div style="font-size: 0.72rem; font-weight: 700; margin-bottom: 2px;">
                    <span style="background: linear-gradient(90deg, #38BDF8, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                        Synthetic Data • Simulated Sandbox
                    </span>
                </div>
                <div style="font-size: 0.68rem; color: {COLORS['text_dim']};">Razorpay AI Buildathon • v{APP_VERSION}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🔄 Refresh System Status", use_container_width=True):
            st.rerun()

    # 3. Route to Page based on st.session_state.current_page
    current_page = st.session_state.current_page
    if "🏠 Overview" in current_page:
        render_overview_page()
    elif "🎯 Recovery Queue" in current_page:
        render_recovery_queue_page()
    elif "💳 Payments" in current_page:
        render_payments_page()
    elif "👤 Customers" in current_page:
        render_customers_page()
    elif "🤖 AI Decisions" in current_page:
        render_ai_decisions_page()
    elif "📊 Analytics" in current_page:
        render_analytics_page()
    elif "⚙️ System" in current_page:
        render_system_page()

    # 4. Footer with branding
    st.markdown(
        f"""
        <div style="margin-top: 60px; padding: 20px 0; border-top: 1px solid {COLORS['border']}; text-align: center; animation: fadeIn 1s ease-out both;">
            <div style="display: flex; justify-content: center; align-items: center; gap: 8px; margin-bottom: 6px;">
                <span style="font-size: 0.85rem; font-weight: 700; color: {COLORS['text_secondary']};">
                    Recover<span style="color: {COLORS['primary']};">AI</span>
                </span>
                <span style="color: {COLORS['text_dim']}; font-size: 0.7rem;">•</span>
                <span style="font-size: 0.72rem; color: {COLORS['text_dim']};">v{APP_VERSION}</span>
            </div>
            <div style="font-size: 0.68rem; color: {COLORS['text_dim']};">
                Built for Razorpay AI Buildathon • Autonomous Revenue Recovery • Synthetic Data Mode
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
