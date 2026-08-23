"""
RecoverAI — Customer Outreach Simulator
========================================
Deterministic simulated customer communication dispatcher across Email, SMS, and WhatsApp.

Key Properties:
- 100% SIMULATED (Zero real customer SMS/emails dispatched).
- Simulates channel delivery, message receipt, and downstream customer actions
  (e.g., clicking payment link, updating card details).
- Deterministic simulation reproducibility via configurable random seed (default: 42).
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class OutreachStatus(str, Enum):
    SIMULATED_SENT = "SIMULATED_SENT"
    DELIVERED = "DELIVERED"
    FAILED_DELIVERY = "FAILED_DELIVERY"


class CustomerActionResult(str, Enum):
    PAYMENT_LINK_CLICKED = "PAYMENT_LINK_CLICKED"
    CARD_DETAILS_UPDATED = "CARD_DETAILS_UPDATED"
    PLAN_REACTIVATED = "PLAN_REACTIVATED"
    NO_CUSTOMER_ACTION = "NO_CUSTOMER_ACTION"


class OutreachSimulator:
    """
    Simulates customer notification delivery and behavioral engagement.
    """

    def __init__(self, seed: int = 42) -> None:
        self.default_seed = seed

    def simulate_outreach(
        self,
        payment_id: str,
        customer_id: str,
        channel: str,
        message_content: str,
        strategy: str = "CUSTOMER_OUTREACH",
        customer_clv: float = 0.0,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Simulates customer message dispatch and interaction.
        """
        active_seed = seed if seed is not None else self.default_seed
        channel_clean = channel.upper().strip()

        # Deterministic seed hashing
        seed_string = f"{payment_id}_{customer_id}_{channel_clean}_{strategy}_{active_seed}"
        hash_digest = hashlib.md5(seed_string.encode()).hexdigest()
        rng_delivery = int(hash_digest[:4], 16) / 0xFFFF
        rng_action = int(hash_digest[4:8], 16) / 0xFFFF

        # Channel Delivery Simulation (WhatsApp & SMS have high deliverability)
        delivery_rate = 0.98 if channel_clean in ["WHATSAPP", "SMS"] else 0.92
        is_delivered = rng_delivery < delivery_rate

        # Customer Action Simulation
        if not is_delivered:
            status = OutreachStatus.FAILED_DELIVERY
            action = CustomerActionResult.NO_CUSTOMER_ACTION
            action_took_place = False
        else:
            status = OutreachStatus.DELIVERED
            # Engagement rate is higher for WhatsApp and high CLV customers
            base_engagement = 0.65 if channel_clean == "WHATSAPP" else 0.50
            if customer_clv >= 5000:
                base_engagement += 0.15

            action_took_place = rng_action < base_engagement

            if action_took_place:
                if strategy == "PAYMENT_METHOD_UPDATE":
                    action = CustomerActionResult.CARD_DETAILS_UPDATED
                elif strategy == "RETENTION_INCENTIVE":
                    action = CustomerActionResult.PLAN_REACTIVATED
                else:
                    action = CustomerActionResult.PAYMENT_LINK_CLICKED
            else:
                action = CustomerActionResult.NO_CUSTOMER_ACTION

        message_id = f"MSG_{payment_id}_{channel_clean[:3]}"

        return {
            "message_id": message_id,
            "payment_id": payment_id,
            "customer_id": customer_id,
            "channel": channel_clean,
            "status": status.value,
            "delivered": is_delivered,
            "customer_action": action.value,
            "customer_action_taken": action_took_place,
            "message_snippet": message_content[:120] + "..." if len(message_content) > 120 else message_content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "simulated": True,
        }


# Global Singleton
_GLOBAL_OUTREACH: Optional[OutreachSimulator] = None


def get_outreach_simulator(seed: int = 42) -> OutreachSimulator:
    global _GLOBAL_OUTREACH
    if _GLOBAL_OUTREACH is None:
        _GLOBAL_OUTREACH = OutreachSimulator(seed=seed)
    return _GLOBAL_OUTREACH


def simulate_customer_outreach(
    payment_id: str,
    customer_id: str,
    channel: str,
    message: str,
    strategy: str = "CUSTOMER_OUTREACH",
    customer_clv: float = 0.0,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Public entry point for simulated customer notification dispatch.
    """
    simulator = get_outreach_simulator(seed=seed or 42)
    return simulator.simulate_outreach(
        payment_id=payment_id,
        customer_id=customer_id,
        channel=channel,
        message_content=message,
        strategy=strategy,
        customer_clv=customer_clv,
        seed=seed,
    )
