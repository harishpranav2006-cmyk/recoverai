"""Payment and PaymentFailure ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Payment(Base):
    """A single payment attempt (successful or failed)."""

    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(20), ForeignKey("customers.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="INR")

    payment_method: Mapped[str] = mapped_column(String(30))
    payment_method_type: Mapped[str] = mapped_column(String(30))
    device_type: Mapped[str] = mapped_column(String(20))

    is_subscription: Mapped[bool] = mapped_column(Boolean, default=False)
    subscription_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    subscription_age_days: Mapped[int] = mapped_column(Integer, default=0)

    payment_success: Mapped[bool] = mapped_column(Boolean, index=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    failure_category: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    failure_temporary: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    payment_gateway_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Customer-derived features (snapshot at payment time)
    customer_age: Mapped[int] = mapped_column(Integer, default=0)
    customer_region: Mapped[str] = mapped_column(String(10))
    previous_successful_payments: Mapped[int] = mapped_column(Integer, default=0)
    previous_failed_payments: Mapped[int] = mapped_column(Integer, default=0)
    previous_retry_count: Mapped[int] = mapped_column(Integer, default=0)
    days_since_last_payment: Mapped[int] = mapped_column(Integer, default=0)
    customer_lifetime_value: Mapped[float] = mapped_column(Float, default=0.0)
    average_transaction_value: Mapped[float] = mapped_column(Float, default=0.0)
    payment_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    last_successful_payment_days: Mapped[int] = mapped_column(Integer, default=0)
    historical_recovery_rate: Mapped[float] = mapped_column(Float, default=0.0)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Outcome fields (NOT ML features)
    simulated_recovery_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_recovery_outcome: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    recovered_after_failure: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, index=True)
    recovery_time_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recovered_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Demo
    demo_scenario: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)

    # Relationships
    customer = relationship("Customer", back_populates="payments")

    def __repr__(self) -> str:
        status = "OK" if self.payment_success else f"FAIL:{self.failure_reason}"
        return f"<Payment {self.id} ₹{self.amount} {status}>"
