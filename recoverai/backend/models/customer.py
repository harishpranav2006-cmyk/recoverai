"""Customer ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Float, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Customer(Base):
    """A customer who makes payments."""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200))
    region: Mapped[str] = mapped_column(String(10))
    segment: Mapped[str] = mapped_column(String(30), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    lifetime_value: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    age_days: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships (loaded lazily by default)
    payments = relationship("Payment", back_populates="customer", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Customer {self.id} segment={self.segment} region={self.region}>"
