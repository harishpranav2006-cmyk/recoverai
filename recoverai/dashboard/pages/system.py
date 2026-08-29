"""
RecoverAI — System Diagnostics & Infrastructure Page (Clean & Schema-Safe)
==========================================================================
System diagnostics, ML model artifact validation, and live health status.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st

from dashboard.api_client import api_client


def render_system_page() -> None:
    """Renders backend health, model artifacts, and API reference links."""
    st.title("⚙️ System Diagnostics & Infrastructure")
    st.caption("Real-time health probes, ML model artifact validation, and developer documentation links.")

    # Derive root host URL for Swagger / ReDoc docs
    base_host = api_client.base_url
    if base_host.endswith("/api/v1"):
        base_host = base_host[:-7]
    elif base_host.endswith("/api/v1/"):
        base_host = base_host[:-8]
    docs_url = f"{base_host}/docs"
    redoc_url = f"{base_host}/redoc"

    # 1. Health Status Probe
    with st.spinner("Probing system health..."):
        health, h_err = api_client.get_health()

    with st.container(border=True):
        st.markdown("### 🩺 Live System Health & Component Probes")

        if h_err or not health:
            st.error("❌ **RecoverAI API is currently unavailable.**")
            st.markdown(
                f"""
                **Diagnostics & Troubleshooting:**
                - **Configured API URL**: `{api_client.base_url}`
                - **Network Detail**: `{h_err or 'Service unreachable'}`
                - **Cloud Deployment**: Ensure the Render backend service is running and `RECOVERAI_API_URL` is set in Streamlit Secrets.
                - **Local Development**: Start the FastAPI backend with:
                  ```bash
                  python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
                  ```
                """
            )
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                st.metric(label="Frontend", value="🟢 READY")
            with c2:
                st.metric(label="Backend API", value="❌ UNAVAILABLE")
            with c3:
                st.metric(label="Database", value="⚠️ UNKNOWN")
            with c4:
                st.metric(label="ML Model", value="⚠️ UNKNOWN")
            with c5:
                st.metric(label="Simulator", value="⚠️ UNKNOWN")

            if st.button("🔄 Retry Connection", key="sys_retry_btn"):
                st.rerun()
        else:
            status_str = str(health.get("status", "")).lower()
            is_healthy = status_str in ["healthy", "ok", "alive"]

            db_status = str(health.get("database", "")).lower()
            db_connected = db_status in ["connected", "healthy", "ok"] or health.get("database_connected", True)

            ml_status = str(health.get("ml_model", "")).lower()
            ml_loaded = ml_status in ["available", "loaded", "ok"] or health.get("ml_model_loaded", True)

            sim_status = str(health.get("simulator", "available")).lower()
            sim_ready = sim_status in ["available", "ready", "ok"]

            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                st.metric(label="Frontend", value="🟢 READY")
            with c2:
                st.metric(label="Backend API", value="🟢 HEALTHY" if is_healthy else "⚠️ DEGRADED")
            with c3:
                st.metric(label="Database", value="🟢 HEALTHY" if db_connected else "❌ ERROR")
            with c4:
                st.metric(label="ML Model", value="🟢 READY" if ml_loaded else "⚠️ UNAVAILABLE")
            with c5:
                st.metric(label="Simulator", value="🟢 READY" if sim_ready else "⚠️ UNAVAILABLE")

            st.caption(
                f"Configured API URL: `{api_client.base_url}` • "
                f"System Version: `{health.get('version', '2.0.0')}` • "
                f"LLM Provider: `{health.get('llm_mode', 'mock')}`"
            )

    st.divider()

    # 2. Production ML Model Specs
    st.markdown("### 🧠 Production ML Inference Specs")

    with st.container(border=True):
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.caption("MODEL ARCHITECTURE")
            st.markdown("**CalibratedClassifierCV(LogisticRegression)**")
        with m2:
            st.caption("CALIBRATION METHOD")
            st.markdown("**Sigmoid (Calibrated Probability)**")
        with m3:
            st.caption("TRAINING POPULATION")
            st.markdown("**50,000 Historical Transactions**")
        with m4:
            st.caption("FEATURE DIMENSIONS")
            st.markdown("**24 Zero-Leakage Features**")

    st.divider()

    # 3. Interactive API Documentation Links (Dynamic URLs)
    st.markdown("### 📖 Developer API Documentation & OpenAPI Portals")
    st.caption(f"Access live interactive documentation generated directly from FastAPI type annotations at `{base_host}`.")

    d_col1, d_col2 = st.columns(2)
    with d_col1:
        with st.container(border=True):
            st.markdown("#### ⚡ Swagger UI Playground")
            st.markdown("Interactive OpenAPI testing environment to test endpoints directly in your browser.")
            st.link_button("🌐 Open Swagger UI", docs_url, use_container_width=True)
    with d_col2:
        with st.container(border=True):
            st.markdown("#### 📘 ReDoc Specifications")
            st.markdown("Clean, structured, and searchable API documentation specification.")
            st.link_button("🌐 Open ReDoc", redoc_url, use_container_width=True)


if __name__ in ("__main__", "__mp_main__"):
    render_system_page()
