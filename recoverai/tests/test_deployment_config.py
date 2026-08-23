"""
RecoverAI — Deployment & Production Configuration Tests
======================================================
Tests Docker configurations, environment variables, safety flags, and container contracts.
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest

from backend.config import settings
from dashboard.config import API_BASE_URL, SIMULATION_NOTICE


class TestDeploymentConfiguration:
    """Deployment readiness, container files, and environment safety verification."""

    @pytest.fixture
    def root_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def test_simulation_safety_defaults(self) -> None:
        """Ensures that default settings enforce simulated, non-financial sandbox execution."""
        assert settings.demo_mode is True
        assert "Synthetic Data" in SIMULATION_NOTICE
        assert "Simulated Payments" in SIMULATION_NOTICE

    def test_cors_allowed_origins_parsing(self) -> None:
        """Validates that CORS allowed origins are configured and parsed safely."""
        origins = [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()]
        assert len(origins) > 0
        assert "http://localhost:8501" in origins

    def test_api_base_url_default(self) -> None:
        """Ensures API_BASE_URL points to the versioned v1 REST API."""
        assert "/api/v1" in API_BASE_URL

    def test_dockerfile_structure_and_targets(self, root_dir: Path) -> None:
        """Validates Dockerfile existence and required targets."""
        dockerfile = root_dir / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile must exist at project root"

        content = dockerfile.read_text(encoding="utf-8")
        assert "FROM python:3.11-slim" in content
        assert "AS backend" in content
        assert "AS frontend" in content
        assert "EXPOSE 8000" in content
        assert "EXPOSE 8501" in content
        assert "HEALTHCHECK" in content
        assert "USER appuser" in content

    def test_docker_compose_structure(self, root_dir: Path) -> None:
        """Validates docker-compose.yml services, ports, and healthchecks."""
        compose_file = root_dir / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml must exist at project root"

        content = compose_file.read_text(encoding="utf-8")
        assert "backend:" in content
        assert "frontend:" in content
        assert '"8000:8000"' in content
        assert '"8501:8501"' in content
        assert "recoverai.db" in content
        assert "service_healthy" in content
        assert "SIMULATION_MODE=true" in content

    def test_dockerignore_excludes_secrets_and_caches(self, root_dir: Path) -> None:
        """Validates that .dockerignore excludes virtual environments and cache directories."""
        dockerignore = root_dir / ".dockerignore"
        assert dockerignore.exists(), ".dockerignore must exist at project root"

        content = dockerignore.read_text(encoding="utf-8")
        assert ".git" in content
        assert ".venv" in content
        assert ".env" in content
        assert "__pycache__" in content

    def test_env_example_documentation(self, root_dir: Path) -> None:
        """Validates that .env.example defines all required configuration parameters."""
        env_example = root_dir / ".env.example"
        assert env_example.exists()

        content = env_example.read_text(encoding="utf-8")
        assert "DATABASE_URL" in content
        assert "API_BASE_URL" in content
        assert "CORS_ALLOWED_ORIGINS" in content
        assert "SIMULATION_MODE" in content
        assert "LLM_PROVIDER" in content
