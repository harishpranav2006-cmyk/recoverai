"""
RecoverAI — Payment & Outreach Simulator Test Suite
===================================================
Tests:
- Deterministic simulation with seed
- Realistic gateway statuses (SUCCESS, FAILED, RETRYABLE_FAILURE, PERMANENT_FAILURE)
- Dynamic delay sensitivity & retry decay
- Permanent failure physics (expired card)
- Outreach simulator deliverability and customer action simulation
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from simulator.payment_simulator import PaymentSimulator, simulate_payment_attempt
from simulator.outreach_simulator import OutreachSimulator, simulate_customer_outreach


class TestPaymentSimulator:
    """Verifies gateway simulation mechanics."""

    def test_deterministic_seed_reproducibility(self) -> None:
        """Same input and seed must produce identical results."""
        sim1 = simulate_payment_attempt(
            payment_id="P_TEST_01",
            amount=1500.0,
            failure_reason="network_failure",
            recovery_probability=0.80,
            seed=42,
        )
        sim2 = simulate_payment_attempt(
            payment_id="P_TEST_01",
            amount=1500.0,
            failure_reason="network_failure",
            recovery_probability=0.80,
            seed=42,
        )
        assert sim1["status"] == sim2["status"]
        assert sim1["gateway_response_code"] == sim2["gateway_response_code"]
        assert sim1["simulated"] is True

    def test_expired_card_zero_probability_without_update(self) -> None:
        """Blind retry of expired card must never succeed."""
        res = simulate_payment_attempt(
            payment_id="P_EXP_01",
            amount=2000.0,
            failure_reason="expired_card",
            recovery_probability=0.90,  # Even with high base ML prob
            is_method_updated=False,
            seed=42,
        )
        assert res["success"] is False
        assert res["status"] == "PERMANENT_FAILURE"

    def test_expired_card_succeeds_when_method_updated(self) -> None:
        """Card update restores high recovery chance."""
        res = simulate_payment_attempt(
            payment_id="P_EXP_02",
            amount=2000.0,
            failure_reason="expired_card",
            recovery_probability=0.50,
            is_method_updated=True,
            seed=42,
        )
        assert res["success"] is True
        assert res["status"] == "SUCCESS"

    def test_structured_output_fields(self) -> None:
        res = simulate_payment_attempt(
            payment_id="P_FIELDS_01",
            amount=999.0,
            failure_reason="insufficient_funds",
            recovery_probability=0.75,
            delay_hours=24.0,
        )
        assert "payment_id" in res
        assert "attempt_id" in res
        assert "attempt_number" in res
        assert "status" in res
        assert "gateway_response_code" in res
        assert "gateway_message" in res
        assert "timestamp" in res
        assert res["simulated"] is True


class TestOutreachSimulator:
    """Verifies customer outreach simulation."""

    def test_deterministic_outreach_seed(self) -> None:
        res1 = simulate_customer_outreach(
            payment_id="P_OUT_01",
            customer_id="C_OUT_01",
            channel="WHATSAPP",
            message="Please update payment details",
            seed=42,
        )
        res2 = simulate_customer_outreach(
            payment_id="P_OUT_01",
            customer_id="C_OUT_01",
            channel="WHATSAPP",
            message="Please update payment details",
            seed=42,
        )
        assert res1["status"] == res2["status"]
        assert res1["customer_action"] == res2["customer_action"]
        assert res1["simulated"] is True

    def test_outreach_channels_supported(self) -> None:
        for ch in ["EMAIL", "SMS", "WHATSAPP"]:
            res = simulate_customer_outreach(
                payment_id="P_CH_01",
                customer_id="C_CH_01",
                channel=ch,
                message=f"Test message for {ch}",
                seed=42,
            )
            assert res["channel"] == ch
            assert res["status"] in ["SIMULATED_SENT", "DELIVERED", "FAILED_DELIVERY"]
            assert res["simulated"] is True
