"""
RecoverAI — System Health & Diagnostics Page (Fintech High-Contrast Dark Theme)
==============================================================================
Real-time infrastructure diagnostics, ML model metadata, simulation status, and API documentation portals.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
import streamlit as st

from dashboard.api_client import api_client
from dashboard.config import COLORS, SIMULATION_NOTICE


def render_system_page() -> None:
    """Renders backend health, model artifacts, and API reference links."""
    st.markdown(
        f"""
        <div style="margin-bottom: 24px; animation: fadeInUp 0.5s ease-out both;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 900; letter-spacing: -0.5px;">
                <span style="background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-size: 200% 200%; animation: gradientShift 4s ease-in-out infinite;">
                    ⚙️ System Diagnostics & Infrastructure
                </span>
            </h1>
            <div style="color: {COLORS['text_dim']}; font-size: 0.92rem; font-weight: 500; margin-top: 6px;">
                Real-time health probes, ML model artifact validation, and developer documentation links.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Fetch System Health & ML Status with Latency Measurement
    t0 = time.perf_counter()
    with st.spinner("Checking infrastructure status..."):
        health_data, h_err = api_client.get_health()
        ml_data, m_err = api_client.get_ml_status()
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)

    if not isinstance(health_data, dict):
        health_data = {}
    if not isinstance(ml_data, dict):
        ml_data = {}

    # Action Bar
    st.markdown(
        """
        <div style="background: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 12px 18px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #E5E7EB; font-weight: 700; font-size: 0.88rem;">🩺 Infrastructure Diagnostics Suite</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_p1, c_p2 = st.columns([3, 1])
    with c_p1:
        st.markdown(f"<span style='color: #4ADE80; font-weight: 700;'>✓ Live Probe Latency: {latency_ms} ms</span>", unsafe_allow_html=True)
    with c_p2:
        if st.button("🔄 Re-Check Health", key="btn_sys_refresh", use_container_width=True):
            st.rerun()

    # 2. System Status Overview Cards
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        api_ok = health_data is not None and health_data.get("status") in ["healthy", "alive", "ready"]
        st.markdown(
            f"""
            <div style="background: #111827; border: 1px solid #1F2937; border-radius: 12px; padding: 18px; text-align: center; box-shadow: 0 4px 14px rgba(0,0,0,0.4);">
                <div style="font-size: 1.6rem; margin-bottom: 6px;">{'🟢' if api_ok else '🔴'}</div>
                <div style="font-weight: 800; color: #FFFFFF; font-size: 1.05rem;">REST API</div>
                <div style="font-size: 0.82rem; color: {'#4ADE80' if api_ok else '#F87171'}; font-weight: 700; margin-top: 4px;">{'ONLINE (/api/v1)' if api_ok else 'OFFLINE'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s2:
        db_raw = (health_data or {}).get("database")
        db_ok = db_raw in ["connected", "healthy"] or (isinstance(db_raw, dict) and db_raw.get("status") == "connected")
        st.markdown(
            f"""
            <div style="background: #111827; border: 1px solid #1F2937; border-radius: 12px; padding: 18px; text-align: center; box-shadow: 0 4px 14px rgba(0,0,0,0.4);">
                <div style="font-size: 1.6rem; margin-bottom: 6px;">{'🟢' if db_ok else '🔴'}</div>
                <div style="font-weight: 800; color: #FFFFFF; font-size: 1.05rem;">Database</div>
                <div style="font-size: 0.82rem; color: {'#4ADE80' if db_ok else '#F87171'}; font-weight: 700; margin-top: 4px;">{'SQLite (50K Records)' if db_ok else 'DISCONNECTED'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s3:
        ml_raw = (health_data or {}).get("ml_model")
        ml_ok = ml_raw in ["available", "loaded"] or (isinstance(ml_raw, dict) and ml_raw.get("status") == "loaded")
        st.markdown(
            f"""
            <div style="background: #111827; border: 1px solid #1F2937; border-radius: 12px; padding: 18px; text-align: center; box-shadow: 0 4px 14px rgba(0,0,0,0.4);">
                <div style="font-size: 1.6rem; margin-bottom: 6px;">{'🟢' if ml_ok else '🔴'}</div>
                <div style="font-weight: 800; color: #FFFFFF; font-size: 1.05rem;">ML Model</div>
                <div style="font-size: 0.82rem; color: {'#4ADE80' if ml_ok else '#F87171'}; font-weight: 700; margin-top: 4px;">{'Calibrated Logistic' if ml_ok else 'UNAVAILABLE'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s4:
        st.markdown(
            """
            <div style="background: #111827; border: 1px solid #1F2937; border-radius: 12px; padding: 18px; text-align: center; box-shadow: 0 4px 14px rgba(0,0,0,0.4);">
                <div style="font-size: 1.6rem; margin-bottom: 6px;">🛡️</div>
                <div style="font-weight: 800; color: #FFFFFF; font-size: 1.05rem;">Sandbox</div>
                <div style="font-size: 0.82rem; color: #38BDF8; font-weight: 700; margin-top: 4px;">SIMULATED MODE</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 3. Model Architecture & Explainability Specs
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px; animation: fadeInUp 0.5s ease-out both;">
            <span style="font-size: 1.25rem;">🧠</span>
            <span style="font-weight: 800; font-size: 1.15rem; color: #FFFFFF;">Production ML Inference Specs</span>
            <div style="flex: 1; height: 1px; background: linear-gradient(90deg, {COLORS['primary']}40, transparent); margin-left: 8px;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if ml_data:
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.markdown(
                f"""
                <div style="background: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 20px; font-size: 0.92rem; line-height: 1.6; color: #FFFFFF;">
                    <div><span style="color: #E5E7EB;">Model Architecture:</span> <b style="color: #FFFFFF;">{ml_data.get('model_type', 'Calibrated Logistic Regression')}</b></div>
                    <div><span style="color: #E5E7EB;">Model Version:</span> <code>{ml_data.get('model_version', '1.0.0')}</code></div>
                    <div><span style="color: #E5E7EB;">Features Used:</span> <b style="color: #38BDF8;">{ml_data.get('num_features', 75)} features</b> (zero data leakage)</div>
                    <div><span style="color: #E5E7EB;">Probability Calibration:</span> <b style="color: #4ADE80;">Sigmoid (CalibratedClassifierCV)</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_col2:
            st.markdown(
                """
                <div style="background: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 20px; font-size: 0.92rem; line-height: 1.6; color: #FFFFFF;">
                    <div><span style="color: #E5E7EB;">Explainability Engine:</span> <b style="color: #C084FC;">SHAP LinearExplainer</b></div>
                    <div><span style="color: #E5E7EB;">High Confidence Tier (T1):</span> <b style="color: #4ADE80;">p ≥ 0.65 (71.02% Precision)</b></div>
                    <div><span style="color: #E5E7EB;">Actionable Outreach Tier (T2):</span> <b style="color: #FBBF24;">0.45 ≤ p < 0.65</b></div>
                    <div><span style="color: #E5E7EB;">Low Recovery Tier (T3):</span> <b style="color: #FB7185;">p < 0.45 (Suppressed)</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # 4. Interactive API Documentation Links
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px; animation: fadeInUp 0.6s ease-out both;">
            <span style="font-size: 1.25rem;">📖</span>
            <span style="font-weight: 800; font-size: 1.15rem; color: #FFFFFF;">Developer API Documentation & OpenAPI Portals</span>
            <div style="flex: 1; height: 1px; background: linear-gradient(90deg, {COLORS['primary']}40, transparent); margin-left: 8px;"></div>
        </div>
        <div style="color: {COLORS['text_dim']}; font-size: 0.92rem; margin-bottom: 16px;">
            Access live interactive documentation generated directly from FastAPI type annotations.
        </div>
        """,
        unsafe_allow_html=True,
    )

    doc_col1, doc_col2, doc_col3 = st.columns(3)
    with doc_col1:
        st.markdown(
            """
            <a href="http://localhost:8000/docs" target="_blank" style="text-decoration: none;">
                <div style="background: #111827; border: 1px solid #1E3A8A; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.2);">
                    <div style="font-size: 1.9rem; margin-bottom: 6px;">⚡</div>
                    <div style="font-weight: 800; color: #38BDF8; font-size: 1.15rem;">Swagger UI</div>
                    <div style="font-size: 0.82rem; color: #E5E7EB; margin-top: 4px;">Interactive API Explorer (/docs)</div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )
    with doc_col2:
        st.markdown(
            """
            <a href="http://localhost:8000/redoc" target="_blank" style="text-decoration: none;">
                <div style="background: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 4px 14px rgba(0,0,0,0.3);">
                    <div style="font-size: 1.9rem; margin-bottom: 6px;">📘</div>
                    <div style="font-weight: 800; color: #FFFFFF; font-size: 1.15rem;">ReDoc UI</div>
                    <div style="font-size: 0.82rem; color: #E5E7EB; margin-top: 4px;">Structured Documentation (/redoc)</div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )
    with doc_col3:
        st.markdown(
            """
            <a href="http://localhost:8000/openapi.json" target="_blank" style="text-decoration: none;">
                <div style="background: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 4px 14px rgba(0,0,0,0.3);">
                    <div style="font-size: 1.9rem; margin-bottom: 6px;">📄</div>
                    <div style="font-weight: 800; color: #E5E7EB; font-size: 1.15rem;">OpenAPI Schema</div>
                    <div style="font-size: 0.82rem; color: #9CA3AF; margin-top: 4px;">Raw JSON Schema (/openapi.json)</div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 5. Raw Health Response JSON
    with st.expander("🔍 **Raw Health Probe Response (`GET /api/v1/health`)**", expanded=False):
        st.json(health_data or {"error": h_err})


if __name__ in ("__main__", "__mp_main__"):
    render_system_page()
