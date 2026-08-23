"""
RecoverAI — Customer Endpoints (v1)
===================================
Provides customer listing, detailed profile aggregation, and payment history.
"""

from __future__ import annotations

import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models.customer import Customer
from backend.models.payment import Payment
from backend.schemas.common import PaginatedResponse
from backend.schemas.customer import (
    CustomerDetailResponse,
    CustomerHistoryItem,
    CustomerHistoryResponse,
    CustomerResponse,
)

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=PaginatedResponse[CustomerResponse], summary="List Customers")
def list_customers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by customer name or email"),
    segment: Optional[str] = Query(None, description="Filter by customer segment (basic, premium, enterprise, free_trial)"),
    region: Optional[str] = Query(None, description="Filter by region (north, south, east, west)"),
    sort_by: str = Query("created_at", description="Field to sort by (lifetime_value, age_days, created_at, name)"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[CustomerResponse]:
    """
    Returns a paginated list of customers matching the provided search and segment filters.
    """
    query = db.query(Customer)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Customer.name.ilike(search_pattern),
                Customer.email.ilike(search_pattern),
                Customer.id.ilike(search_pattern),
            )
        )

    if segment:
        query = query.filter(Customer.segment == segment)

    if region:
        query = query.filter(Customer.region == region)

    # Validated sorting
    allowed_sort_fields = {
        "lifetime_value": Customer.lifetime_value,
        "age_days": Customer.age_days,
        "created_at": Customer.created_at,
        "name": Customer.name,
        "id": Customer.id,
    }
    sort_col = allowed_sort_fields.get(sort_by, Customer.created_at)
    query = query.order_by(sort_col.asc() if sort_order.lower() == "asc" else sort_col.desc())

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    offset = (page - 1) * page_size
    customers = query.offset(offset).limit(page_size).all()

    items = [
        CustomerResponse(
            id=c.id,
            name=c.name,
            email=c.email,
            region=c.region,
            segment=c.segment,
            lifetime_value=float(c.lifetime_value),
            age_days=c.age_days,
            created_at=c.created_at,
        )
        for c in customers
    ]

    return PaginatedResponse[CustomerResponse](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get("/{customer_id}", response_model=CustomerDetailResponse, summary="Get Customer Details")
def get_customer_details(customer_id: str, db: Session = Depends(get_db)) -> CustomerDetailResponse:
    """
    Retrieves full customer profile and aggregated payment statistics.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found.",
        )

    payments = db.query(Payment).filter(Payment.customer_id == customer_id).all()
    total_tx = len(payments)
    successful_tx = sum(1 for p in payments if p.payment_success)
    failed_tx = sum(1 for p in payments if not p.payment_success)
    recovered_tx = sum(1 for p in payments if not p.payment_success and p.recovered_after_failure)
    recovery_rate = (recovered_tx / failed_tx) if failed_tx > 0 else 0.0
    total_spend = sum(float(p.amount) for p in payments if p.payment_success or p.recovered_after_failure)
    unrecovered_debt = sum(
        float(p.amount) for p in payments if not p.payment_success and not p.recovered_after_failure
    )

    is_vip = float(customer.lifetime_value) >= settings.vip_clv_threshold or customer.segment == "enterprise"

    return CustomerDetailResponse(
        id=customer.id,
        name=customer.name,
        email=customer.email,
        region=customer.region,
        segment=customer.segment,
        lifetime_value=float(customer.lifetime_value),
        age_days=customer.age_days,
        created_at=customer.created_at,
        is_vip=is_vip,
        total_transactions=total_tx,
        successful_payments=successful_tx,
        failed_payments=failed_tx,
        recovered_payments=recovered_tx,
        historical_recovery_rate=round(recovery_rate, 4),
        total_spend=round(total_spend, 2),
        unrecovered_debt=round(unrecovered_debt, 2),
    )


@router.get("/{customer_id}/history", response_model=CustomerHistoryResponse, summary="Get Customer Payment History")
def get_customer_history(customer_id: str, db: Session = Depends(get_db)) -> CustomerHistoryResponse:
    """
    Returns the chronological payment history for a customer.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found.",
        )

    payments = (
        db.query(Payment)
        .filter(Payment.customer_id == customer_id)
        .order_by(Payment.timestamp.desc())
        .all()
    )

    total_payments = len(payments)
    successful_payments = sum(1 for p in payments if p.payment_success)
    failed_payments = sum(1 for p in payments if not p.payment_success)

    items = [
        CustomerHistoryItem(
            payment_id=p.id,
            timestamp=p.timestamp,
            amount=float(p.amount),
            currency=p.currency,
            payment_method=p.payment_method,
            payment_success=p.payment_success,
            failure_reason=p.failure_reason,
            recovered_after_failure=p.recovered_after_failure,
            recovered_amount=float(p.recovered_amount) if p.recovered_amount is not None else None,
            retry_count=p.retry_count,
        )
        for p in payments
    ]

    return CustomerHistoryResponse(
        customer_id=customer.id,
        customer_name=customer.name,
        total_payments=total_payments,
        successful_payments=successful_payments,
        failed_payments=failed_payments,
        payments=items,
    )
