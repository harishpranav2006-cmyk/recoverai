"""Shared test fixtures for RecoverAI test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure project root is on path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ml.data_generator import SyntheticDataGenerator, GenerationConfig


@pytest.fixture
def small_config() -> GenerationConfig:
    """A small config for fast tests (500 customers, 5000 payments)."""
    return GenerationConfig(
        seed=42,
        num_customers=500,
        num_payments=5000,
    )


@pytest.fixture
def small_generator(small_config: GenerationConfig) -> SyntheticDataGenerator:
    """A generator with small config, data already generated."""
    gen = SyntheticDataGenerator(small_config)
    gen.generate()
    return gen
