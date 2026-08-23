"""
RecoverAI — Decision & Strategy Engine Pydantic Schemas
======================================================
Defines type-safe request/response contracts for agent decisions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RecoveryTier(str, Enum):
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    ACTIONABLE_OUTREACH = "ACTIONABLE_OUTREACH"
    SUPPRESS_OR_ESCALATE = "SUPPRESS_OR_ESCALATE"


class RecoveryStrategy(str, Enum):
    SMART_RETRY = "SMART_RETRY"
    CUSTOMER_OUTREACH = "CUSTOMER_OUTREACH"
    PAYMENT_METHOD_UPDATE = "PAYMENT_METHOD_UPDATE"
    RETENTION_INCENTIVE = "RETENTION_INCENTIVE"
    VIP_ACCOUNT_ESCALATION = "VIP_ACCOUNT_ESCALATION"
    SUPPRESSION = "SUPPRESSION"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class RecommendedAction(str, Enum):
    RETRY_AFTER_DELAY = "RETRY_AFTER_DELAY"
    DISPATCH_PAYMENT_LINK = "DISPATCH_PAYMENT_LINK"
    REQUEST_PAYMENT_METHOD_UPDATE = "REQUEST_PAYMENT_METHOD_UPDATE"
    SEND_RETENTION_LINK = "SEND_RETENTION_LINK"
    ESCALATE_TO_ACCOUNT_MANAGER = "ESCALATE_TO_ACCOUNT_MANAGER"
    FLAG_FOR_CS_REVIEW = "FLAG_FOR_CS_REVIEW"
    APPLY_GRACE_PERIOD_AND_SUPPRESS = "APPLY_GRACE_PERIOD_AND_SUPPRESS"


class ReasonCode(str, Enum):
    # Positive / High Confidence Drivers
    HIGH_RECOVERY_PROBABILITY = "HIGH_RECOVERY_PROBABILITY"
    STRONG_PAYMENT_HISTORY = "STRONG_PAYMENT_HISTORY"
    LOW_RETRY_COUNT = "LOW_RETRY_COUNT"
    TRANSIENT_GATEWAY_ERROR = "TRANSIENT_GATEWAY_ERROR"
    TRANSIENT_NETWORK_FAILURE = "TRANSIENT_NETWORK_FAILURE"
    HIGH_LIFETIME_VALUE_ACCOUNT = "HIGH_LIFETIME_VALUE_ACCOUNT"
    LONG_TENURE_SUBSCRIPTION = "LONG_TENURE_SUBSCRIPTION"
    FIRST_TIME_PAYMENT_FAILURE = "FIRST_TIME_PAYMENT_FAILURE"

    # Actionable Outreach Drivers
    MODERATE_RECOVERY_PROBABILITY = "MODERATE_RECOVERY_PROBABILITY"
    EXPIRED_CARD_DETECTED = "EXPIRED_CARD_DETECTED"
    INVALID_PAYMENT_CREDENTIALS = "INVALID_PAYMENT_CREDENTIALS"
    INSUFFICIENT_FUNDS_DETECTED = "INSUFFICIENT_FUNDS_DETECTED"
    CUSTOMER_CANCELLED_FLOW = "CUSTOMER_CANCELLED_FLOW"
    DAILY_LIMIT_EXCEEDED = "DAILY_LIMIT_EXCEEDED"
    BANK_DECLINE_REQUIRES_CUSTOMER = "BANK_DECLINE_REQUIRES_CUSTOMER"

    # Low Recovery / Suppression Drivers
    LOW_RECOVERY_PROBABILITY = "LOW_RECOVERY_PROBABILITY"
    MAX_RETRY_FATIGUE_REACHED = "MAX_RETRY_FATIGUE_REACHED"
    CHRONIC_FAILURE_HISTORY = "CHRONIC_FAILURE_HISTORY"
    VIP_ENTERPRISE_HIGH_TOUCH = "VIP_ENTERPRISE_HIGH_TOUCH"
    LOW_ACCOUNT_ENGAGEMENT = "LOW_ACCOUNT_ENGAGEMENT"

    # Additional Recovery / Safety Reason Codes
    RETRY_LIMIT_REACHED = "RETRY_LIMIT_REACHED"
    TEMPORARY_FAILURE = "TEMPORARY_FAILURE"
    PERMANENT_FAILURE = "PERMANENT_FAILURE"
    HIGH_CUSTOMER_VALUE = "HIGH_CUSTOMER_VALUE"
    LOW_CUSTOMER_VALUE = "LOW_CUSTOMER_VALUE"
    ALTERNATIVE_PAYMENT_RECOMMENDED = "ALTERNATIVE_PAYMENT_RECOMMENDED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    RETRY_ELIGIBLE = "RETRY_ELIGIBLE"
    RETRY_BLOCKED = "RETRY_BLOCKED"
    PAYMENT_ALREADY_RECOVERED = "PAYMENT_ALREADY_RECOVERED"
    HIGH_VALUE_PAYMENT_REVIEW = "HIGH_VALUE_PAYMENT_REVIEW"


class DecisionResponse(BaseModel):
    """
    Standard decision output contract for RecoverAI.
    """
    model_config = ConfigDict(use_enum_values=True)

    payment_id: str
    recovery_probability: float = Field(..., ge=0.0, le=1.0)
    tier: RecoveryTier
    strategy: RecoveryStrategy
    recommended_action: RecommendedAction
    delay_hours: Optional[float] = None
    reason_codes: List[ReasonCode] = Field(default_factory=list)
    explanation: Optional[str] = None
    customer_message_required: bool
    human_review_required: bool
    channel_recommendation: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
