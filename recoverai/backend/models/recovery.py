"""Recovery-related ORM models: cases, actions, outcomes, retries, messages."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, DateTime, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class RecoveryCase(Base):
    """A recovery case opened for a failed payment."""

    __tablename__ = "recovery_cases"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    payment_id: Mapped[str] = mapped_column(String(20), ForeignKey("payments.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(20), ForeignKey("customers.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="open")  # open, in_progress, recovered, failed, escalated
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    recovery_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    recovered_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class RecoveryAction(Base):
    """An action taken as part of a recovery case."""

    __tablename__ = "recovery_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(20), ForeignKey("recovery_cases.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(50))  # retry_payment, send_reminder, etc.
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)


class RecoveryOutcome(Base):
    """Final outcome of a recovery case."""

    __tablename__ = "recovery_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(20), ForeignKey("recovery_cases.id"), index=True)
    success: Mapped[bool] = mapped_column(Boolean)
    amount_recovered: Mapped[float] = mapped_column(Float, default=0.0)
    recovery_time_hours: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    strategy_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    @property
    def status(self) -> str:
        return "RECOVERED" if self.success else "FAILED"


class RetryAttempt(Base):
    """A single retry attempt for a payment."""

    __tablename__ = "retry_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[str] = mapped_column(String(20), ForeignKey("payments.id"), index=True)
    case_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("recovery_cases.id"), nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    success: Mapped[bool] = mapped_column(Boolean)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    simulated: Mapped[bool] = mapped_column(Boolean, default=True)


class Message(Base):
    """A customer communication message."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(20), ForeignKey("recovery_cases.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(20), ForeignKey("customers.id"))
    channel: Mapped[str] = mapped_column(String(20))  # email, sms, push
    tone: Mapped[str] = mapped_column(String(20))  # professional, friendly, concise
    content: Mapped[str] = mapped_column(Text)
    generated_by: Mapped[str] = mapped_column(String(20))  # llm, mock, template
    timestamp: Mapped[datetime] = mapped_column(DateTime)
