"""Agent-related ORM models: decisions and model predictions."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class AgentDecision(Base):
    """A structured decision produced by the AI recovery agent."""

    __tablename__ = "agent_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(20), ForeignKey("recovery_cases.id"), index=True)
    payment_id: Mapped[str] = mapped_column(String(20), ForeignKey("payments.id"))
    recovery_probability: Mapped[float] = mapped_column(Float)
    recommended_action: Mapped[str] = mapped_column(String(50))
    delay_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reasoning: Mapped[str] = mapped_column(Text)
    customer_message_required: Mapped[bool] = mapped_column()
    alternative_payment_required: Mapped[bool] = mapped_column()
    human_escalation_required: Mapped[bool] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column(DateTime)

    @property
    def explanation(self) -> str:
        return self.reasoning or ""

    @property
    def human_review_required(self) -> bool:
        return bool(self.human_escalation_required)

    @property
    def tier(self) -> str:
        if self.recovery_probability >= 0.65:
            return "HIGH_CONFIDENCE"
        elif self.recovery_probability >= 0.45:
            return "ACTIONABLE_OUTREACH"
        return "SUPPRESS_OR_ESCALATE"

    @property
    def strategy(self) -> str:
        if "RETRY" in self.recommended_action:
            return "SMART_RETRY"
        elif "METHOD" in self.recommended_action or "EXPIRED" in self.recommended_action:
            return "PAYMENT_METHOD_UPDATE"
        elif "OUTREACH" in self.recommended_action:
            return "CUSTOMER_OUTREACH"
        elif "SUPPRESS" in self.recommended_action:
            return "SUPPRESSION"
        elif "ESCALATE" in self.recommended_action:
            return "VIP_ACCOUNT_ESCALATION"
        return "SMART_RETRY"

    @property
    def reason_codes(self) -> list:
        codes = []
        if self.recovery_probability >= 0.65:
            codes.append("HIGH_RECOVERY_PROBABILITY")
        elif self.recovery_probability >= 0.45:
            codes.append("MODERATE_RECOVERY_PROBABILITY")
        else:
            codes.append("LOW_RECOVERY_PROBABILITY")
        return codes


class ModelPrediction(Base):
    """A prediction from the ML model, stored for audit / explainability."""

    __tablename__ = "model_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[str] = mapped_column(String(20), ForeignKey("payments.id"), index=True)
    model_version: Mapped[str] = mapped_column(String(50))
    probability: Mapped[float] = mapped_column(Float)
    top_features: Mapped[str] = mapped_column(Text)  # JSON string
    timestamp: Mapped[datetime] = mapped_column(DateTime)

    @property
    def recovery_probability(self) -> float:
        return float(self.probability)

