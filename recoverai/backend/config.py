"""RecoverAI — Application configuration via environment variables."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central application settings loaded from environment / .env file."""

    # --- LLM ---
    llm_provider: Literal["openai", "mock"] = "mock"
    openai_api_key: str = ""

    # --- Database ---
    database_url: str = "sqlite:///./recoverai.db"

    # --- Application & API ---
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    cors_allowed_origins: str = "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://localhost:8000,https://share.streamlit.io,*"
    default_page_size: int = 25
    max_page_size: int = 100
    max_batch_size: int = 50
    demo_mode: bool = True
    app_host: str = Field(default_factory=lambda: os.getenv("HOST", os.getenv("APP_HOST", "0.0.0.0")))
    app_port: int = Field(default_factory=lambda: int(os.getenv("PORT", os.getenv("APP_PORT", "8000"))))
    log_level: str = "INFO"

    # --- ML ---
    model_path: str = "ml/artifacts/model.joblib"
    preprocessor_path: str = "ml/artifacts/preprocessor.joblib"
    shap_path: str = "ml/artifacts/shap_explainer.joblib"

    # --- Recovery Policy & Decision Engine ---
    high_confidence_threshold: float = 0.65
    outreach_threshold: float = 0.45
    max_retry_attempts: int = 3
    min_retry_delay_hours: float = 4.0
    high_value_payment_threshold: float = 15000.0
    vip_clv_threshold: float = 10000.0

    # --- Failure-Specific Retry Delays (Hours) ---
    network_failure_delay: float = 4.0
    temporary_gateway_failure_delay: float = 4.0
    payment_timeout_delay: float = 4.0
    insufficient_funds_delay: float = 24.0
    bank_declined_delay: float = 24.0
    default_retry_delay: float = 24.0

    # --- Data Generation ---
    data_seed: int = 42
    num_customers: int = 5000
    num_payments: int = 50000

    # --- Paths ---
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def is_llm_available(self) -> bool:
        """True when a real LLM provider is configured with a key."""
        if self.llm_provider == "mock":
            return False
        if self.llm_provider == "openai" and not self.openai_api_key:
            return False
        return True


# Singleton — import this wherever settings are needed.
settings = Settings()
