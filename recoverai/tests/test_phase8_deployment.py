"""
RecoverAI — Phase 8 Cloud Deployment & Production Readiness Tests
=================================================================
Validates database auto-initialization, dynamic PORT/HOST resolution,
configurable API URLs, Render configuration, and CORS compatibility.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from backend.config import Settings, settings
from backend.init_db import REQUIRED_ML_ARTIFACTS, verify_ml_artifacts, initialize_database
from backend.main import app
from dashboard.config import get_api_base_url, get_api_timeout_seconds


class TestPhase8DeploymentReadiness:
    """Test suite covering Phase 8 cloud readiness and deployment configuration."""

    @pytest.fixture
    def root_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def test_ml_artifacts_presence(self) -> None:
        """Verifies that all required ML artifacts are present on disk for cloud deployment."""
        status = verify_ml_artifacts()
        for artifact_name in REQUIRED_ML_ARTIFACTS:
            assert artifact_name in status, f"Artifact {artifact_name} must be in status dictionary"
            assert status[artifact_name] is True, f"ML artifact {artifact_name} must exist on disk"

    def test_database_initialization_idempotence(self) -> None:
        """Ensures initialize_database runs safely without duplicating data or crashing."""
        c, p = initialize_database()
        assert c > 0, "Customers count must be greater than zero"
        assert p > 0, "Payments count must be greater than zero"

        # Running a second time should be idempotent and return immediately
        c2, p2 = initialize_database()
        assert c2 == c
        assert p2 == p

    def test_port_resolution_from_environment(self) -> None:
        """Verifies that Settings reads the PORT environment variable passed by Render."""
        with patch.dict(os.environ, {"PORT": "10000"}):
            s = Settings()
            assert s.app_port == 10000

    def test_host_resolution_from_environment(self) -> None:
        """Verifies that Settings reads the HOST environment variable."""
        with patch.dict(os.environ, {"HOST": "0.0.0.0"}):
            s = Settings()
            assert s.app_host == "0.0.0.0"

    def test_api_base_url_resolution_priority(self) -> None:
        """Tests the resolution priority of get_api_base_url (env var vs fallback)."""
        # Fallback when no env var is set
        with patch.dict(os.environ, {}, clear=True):
            url = get_api_base_url()
            assert url == "http://localhost:8000/api/v1"

        # Environment variable override
        with patch.dict(os.environ, {"RECOVERAI_API_URL": "https://recoverai-api.onrender.com/api/v1"}):
            url = get_api_base_url()
            assert url == "https://recoverai-api.onrender.com/api/v1"

        # Alternate env var API_BASE_URL
        with patch.dict(os.environ, {"API_BASE_URL": "https://custom-api.example.com/api/v1/"}, clear=True):
            url = get_api_base_url()
            assert url == "https://custom-api.example.com/api/v1"

    def test_api_timeout_resolution(self) -> None:
        """Tests timeout resolution from environment."""
        with patch.dict(os.environ, {"API_TIMEOUT_SECONDS": "25"}):
            timeout = get_api_timeout_seconds()
            assert timeout == 25

    def test_render_yaml_validity(self, root_dir: Path) -> None:
        """Validates that render.yaml exists and contains all required specifications."""
        render_yaml = root_dir / "render.yaml"
        assert render_yaml.exists(), "render.yaml must exist at project root"

        content = render_yaml.read_text(encoding="utf-8")
        assert "type: web" in content
        assert "name: recoverai-api" in content
        assert "runtime: docker" in content or "python" in content
        assert "/api/v1/health/live" in content
        assert "DATABASE_URL" in content
        assert "CORS_ALLOWED_ORIGINS" in content

    def test_streamlit_secrets_example_exists(self, root_dir: Path) -> None:
        """Validates that secrets.toml.example exists and documents RECOVERAI_API_URL."""
        secrets_file = root_dir / ".streamlit" / "secrets.toml.example"
        assert secrets_file.exists()

        content = secrets_file.read_text(encoding="utf-8")
        assert "RECOVERAI_API_URL" in content

    def test_health_endpoints_accessible(self) -> None:
        """Verifies that all required health endpoints return 200 OK."""
        client = TestClient(app)

        r_health = client.get("/api/v1/health")
        assert r_health.status_code == 200
        data = r_health.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["database"] == "connected"
        assert data["ml_model"] == "available"

        r_live = client.get("/api/v1/health/live")
        assert r_live.status_code == 200
        assert r_live.json()["alive"] is True

        r_ready = client.get("/api/v1/health/ready")
        assert r_ready.status_code == 200
        assert r_ready.json()["ready"] is True

    def test_docs_and_openapi_accessible(self) -> None:
        """Verifies that OpenAPI documentation endpoints are available."""
        client = TestClient(app)

        r_docs = client.get("/docs")
        assert r_docs.status_code == 200

        r_openapi = client.get("/openapi.json")
        assert r_openapi.status_code == 200
        schema = r_openapi.json()
        assert "openapi" in schema
        assert schema["info"]["title"] == "RecoverAI — Autonomous AI Revenue Recovery API"
