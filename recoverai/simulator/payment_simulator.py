"""
RecoverAI — Payment Gateway Simulator
======================================
Deterministic, configurable simulated payment gateway for autonomous recovery execution.

Key Properties:
- 100% SIMULATED (Zero real financial transactions or live bank API connections).
- Deterministic simulation reproducibility via configurable random seed (default: 42).
- Probabilistic outcome generation grounded in Phase 2 calibrated recovery probabilities,
  failure category friction, retry attempt number, delay elapsed, and transaction context.
- Explicit status classifications: SUCCESS, FAILED, RETRYABLE_FAILURE, PERMANENT_FAILURE.
- Strict data isolation: NEVER feeds future simulated outcomes backward into ML prediction.
"""

from __future__ import annotations

import hashlib
import logging
import random
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from backend.config import settings

logger = logging.getLogger(__name__)


class GatewayStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    PERMANENT_FAILURE = "PERMANENT_FAILURE"


# Realistic simulated gateway response codes
GATEWAY_RESPONSES = {
    GatewayStatus.SUCCESS: [
        {"code": "00", "message": "Transaction Approved / Paid (SIMULATED)"},
        {"code": "S100", "message": "Auto-debit successful on scheduled retry (SIMULATED)"},
        {"code": "S102", "message": "UPI Mandate executed successfully (SIMULATED)"},
    ],
    GatewayStatus.RETRYABLE_FAILURE: [
        {"code": "R503", "message": "Issuer bank network timed out during retry (SIMULATED)"},
        {"code": "R504", "message": "Temporary debit volume throttle from bank (SIMULATED)"},
        {"code": "R501", "message": "Card processing server busy (SIMULATED)"},
    ],
    GatewayStatus.FAILED: [
        {"code": "F402", "message": "Insufficient balance on customer account (SIMULATED)"},
        {"code": "F403", "message": "Transaction declined by cardholder bank (SIMULATED)"},
        {"code": "F405", "message": "Daily transaction limit exceeded (SIMULATED)"},
    ],
    GatewayStatus.PERMANENT_FAILURE: [
        {"code": "P404", "message": "Card has expired or was blocked by customer (SIMULATED)"},
        {"code": "P401", "message": "Invalid card details / token revoked (SIMULATED)"},
        {"code": "P409", "message": "Subscription cancelled by customer (SIMULATED)"},
    ],
}


class PaymentSimulator:
    """
    Simulates gateway authorization attempts deterministically based on ML recovery
    estimates and execution context.
    """

    def __init__(self, seed: int = 42) -> None:
        self.default_seed = seed

    def simulate_attempt(
        self,
        payment_id: str,
        amount: float,
        failure_reason: str,
        recovery_probability: float,
        attempt_number: int = 1,
        delay_hours: float = 0.0,
        payment_method: str = "card",
        is_method_updated: bool = False,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes a simulated payment retry attempt.
        """
        active_seed = seed if seed is not None else self.default_seed

        # Generate deterministic pseudo-random float in [0, 1) for this specific attempt
        seed_string = f"{payment_id}_{attempt_number}_{active_seed}_{delay_hours}_{is_method_updated}"
        hash_digest = hashlib.md5(seed_string.encode()).hexdigest()
        rng_value = int(hash_digest[:8], 16) / 0xFFFFFFFF

        failure_clean = (failure_reason or "").lower().strip()

        # 1. Base recovery likelihood from Phase 2 ML prediction
        effective_prob = float(recovery_probability)

        # 2. Permanent failure physics
        if failure_clean in ["expired_card", "invalid_payment_details"]:
            if is_method_updated:
                # If customer updated payment method, high chance of success
                effective_prob = max(effective_prob, 0.88)
            else:
                # Blind retry of expired card always fails permanently
                effective_prob = 0.0

        elif failure_clean == "customer_cancelled":
            if is_method_updated:
                effective_prob = max(effective_prob, 0.70)
            else:
                effective_prob = 0.05

        # 3. Dynamic adjustment based on delay elapsed
        elif failure_clean in ["insufficient_funds", "limit_exceeded"]:
            if delay_hours >= 24.0:
                # Giving customer/bank 24 hours increases recovery chance
                effective_prob = min(effective_prob * 1.15, 0.92)
            elif delay_hours < 4.0:
                # Immediate retry of insufficient balance rarely works
                effective_prob = effective_prob * 0.40

        elif failure_clean in ["network_failure", "temporary_gateway_failure", "payment_timeout"]:
            if delay_hours >= 4.0:
                # Network resolved after transient delay
                effective_prob = min(effective_prob * 1.25, 0.95)

        # 4. Decay across repeated attempts (fatigue factor)
        attempt_penalty = max(0, attempt_number - 1) * 0.08
        effective_prob = max(0.0, effective_prob - attempt_penalty)

        # 5. Determine Gateway Outcome
        is_success = rng_value < effective_prob

        if is_success:
            status = GatewayStatus.SUCCESS
            resp_pool = GATEWAY_RESPONSES[GatewayStatus.SUCCESS]
            resp = resp_pool[int(hash_digest[8:10], 16) % len(resp_pool)]
        else:
            if failure_clean in ["expired_card", "invalid_payment_details"] and not is_method_updated:
                status = GatewayStatus.PERMANENT_FAILURE
                resp_pool = GATEWAY_RESPONSES[GatewayStatus.PERMANENT_FAILURE]
            elif failure_clean in ["network_failure", "temporary_gateway_failure", "payment_timeout"]:
                status = GatewayStatus.RETRYABLE_FAILURE
                resp_pool = GATEWAY_RESPONSES[GatewayStatus.RETRYABLE_FAILURE]
            else:
                status = GatewayStatus.FAILED
                resp_pool = GATEWAY_RESPONSES[GatewayStatus.FAILED]
            resp = resp_pool[int(hash_digest[8:10], 16) % len(resp_pool)]

        attempt_id = f"ATT_{payment_id}_{attempt_number}"

        return {
            "payment_id": payment_id,
            "attempt_id": attempt_id,
            "attempt_number": attempt_number,
            "status": status.value,
            "success": is_success,
            "amount": float(amount),
            "gateway_response_code": resp["code"],
            "gateway_message": resp["message"],
            "simulated_probability_used": round(effective_prob, 4),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "simulated": True,
        }


# Global Simulator Singleton
_GLOBAL_SIMULATOR: Optional[PaymentSimulator] = None


def get_payment_simulator(seed: int = 42) -> PaymentSimulator:
    global _GLOBAL_SIMULATOR
    if _GLOBAL_SIMULATOR is None:
        _GLOBAL_SIMULATOR = PaymentSimulator(seed=seed)
    return _GLOBAL_SIMULATOR


def simulate_payment_attempt(
    payment_id: str,
    amount: float,
    failure_reason: str,
    recovery_probability: float,
    attempt_number: int = 1,
    delay_hours: float = 0.0,
    payment_method: str = "card",
    is_method_updated: bool = False,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Public entry point for deterministic simulated payment gateway execution.
    """
    simulator = get_payment_simulator(seed=seed or 42)
    return simulator.simulate_attempt(
        payment_id=payment_id,
        amount=amount,
        failure_reason=failure_reason,
        recovery_probability=recovery_probability,
        attempt_number=attempt_number,
        delay_hours=delay_hours,
        payment_method=payment_method,
        is_method_updated=is_method_updated,
        seed=seed,
    )
