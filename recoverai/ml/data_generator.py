"""
RecoverAI — Synthetic Data Generator
=====================================
Generates realistic synthetic payment data for ML training and demo purposes.
All data is clearly synthetic — no real customer information is used.

Key design principles:
  - Reproducible via configurable seed
  - Recovery outcome depends on multiple features with controlled noise
  - Explicit separation of ML features vs outcome/leakage fields
  - Deterministic demo scenarios for buildathon presentation
  - Configurable via GenerationConfig (no hardcoded values)
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


# ─── Column Classification ────────────────────────────────────────────────────

IDENTIFIER_COLUMNS = ["customer_id", "payment_id"]

FEATURE_COLUMNS = [
    "amount",
    "currency",
    "payment_method",
    "payment_method_type",
    "device_type",
    "is_subscription",
    "subscription_type",
    "subscription_age_days",
    "customer_age",
    "customer_region",
    "previous_successful_payments",
    "previous_failed_payments",
    "previous_retry_count",
    "days_since_last_payment",
    "customer_lifetime_value",
    "average_transaction_value",
    "payment_frequency",
    "last_successful_payment_days",
    "historical_recovery_rate",
    "retry_count",
    "failure_reason",
    "failure_category",
    "failure_temporary",
    "payment_gateway_status",
]

TARGET_COLUMN = "actual_recovery_outcome"

LEAKAGE_COLUMNS = [
    "simulated_recovery_probability",
    "actual_recovery_outcome",
    "recovered_after_failure",
    "recovery_time_hours",
    "recovered_amount",
]

OUTCOME_COLUMNS = [
    "recovered_after_failure",
    "recovery_time_hours",
    "recovered_amount",
]

METADATA_COLUMNS = [
    "timestamp",
    "payment_success",
    "demo_scenario",
]


# ─── Configuration ────────────────────────────────────────────────────────────

class GenerationConfig(BaseModel):
    """Fully configurable data generation parameters."""

    seed: int = 42
    num_customers: int = 5000
    num_payments: int = 50000
    date_start: str = "2024-01-01"
    date_end: str = "2026-08-01"
    currency: str = "INR"

    # Distribution weights
    region_weights: dict[str, float] = Field(default_factory=lambda: {
        "IN": 0.60, "US": 0.12, "UK": 0.08, "SEA": 0.12, "EU": 0.08,
    })
    segment_weights: dict[str, float] = Field(default_factory=lambda: {
        "free_trial": 0.15, "basic": 0.40, "premium": 0.30, "enterprise": 0.15,
    })
    payment_method_weights: dict[str, float] = Field(default_factory=lambda: {
        "credit_card": 0.25, "debit_card": 0.25, "upi": 0.25,
        "net_banking": 0.15, "wallet": 0.10,
    })
    device_type_weights: dict[str, float] = Field(default_factory=lambda: {
        "mobile": 0.55, "desktop": 0.35, "tablet": 0.10,
    })

    # Amount ranges by segment (min, max, mean for log-normal)
    segment_amount_params: dict[str, dict[str, float]] = Field(default_factory=lambda: {
        "free_trial": {"min": 0.0, "max": 0.0, "mean": 0.0},
        "basic": {"min": 99.0, "max": 2999.0, "mean": 499.0},
        "premium": {"min": 499.0, "max": 9999.0, "mean": 1999.0},
        "enterprise": {"min": 4999.0, "max": 99999.0, "mean": 14999.0},
    })

    # CLV multiplier by segment
    segment_clv_multiplier: dict[str, float] = Field(default_factory=lambda: {
        "free_trial": 0.0, "basic": 1.0, "premium": 3.0, "enterprise": 10.0,
    })

    # Failure parameters
    base_failure_rate: float = 0.30
    failure_type_weights: dict[str, float] = Field(default_factory=lambda: {
        "insufficient_funds": 0.22,
        "expired_card": 0.14,
        "invalid_payment_details": 0.08,
        "bank_declined": 0.12,
        "network_failure": 0.10,
        "temporary_gateway_failure": 0.08,
        "authentication_failure": 0.07,
        "payment_timeout": 0.06,
        "limit_exceeded": 0.05,
        "customer_cancelled": 0.08,
    })

    # Whether each failure type is temporary
    failure_temporary_map: dict[str, bool] = Field(default_factory=lambda: {
        "insufficient_funds": True,
        "expired_card": False,
        "invalid_payment_details": False,
        "bank_declined": True,
        "network_failure": True,
        "temporary_gateway_failure": True,
        "authentication_failure": False,
        "payment_timeout": True,
        "limit_exceeded": True,
        "customer_cancelled": False,
    })

    # Failure category mapping
    failure_category_map: dict[str, str] = Field(default_factory=lambda: {
        "insufficient_funds": "payment_issue",
        "expired_card": "card_issue",
        "invalid_payment_details": "card_issue",
        "bank_declined": "bank_issue",
        "network_failure": "technical_issue",
        "temporary_gateway_failure": "technical_issue",
        "authentication_failure": "auth_issue",
        "payment_timeout": "technical_issue",
        "limit_exceeded": "payment_issue",
        "customer_cancelled": "customer_issue",
    })

    # Recovery factor weights (for simulated probability computation)
    recovery_weights: dict[str, float] = Field(default_factory=lambda: {
        "failure_type": 0.30,
        "customer_history": 0.15,
        "amount": 0.10,
        "payment_method": 0.10,
        "subscription_age": 0.10,
        "retry_count": 0.10,
        "customer_value": 0.15,
    })

    # Base recovery rate by failure type (used as factor, not as final probability)
    failure_recovery_factor: dict[str, float] = Field(default_factory=lambda: {
        "insufficient_funds": 0.45,
        "expired_card": 0.15,
        "invalid_payment_details": 0.10,
        "bank_declined": 0.50,
        "network_failure": 0.80,
        "temporary_gateway_failure": 0.85,
        "authentication_failure": 0.25,
        "payment_timeout": 0.70,
        "limit_exceeded": 0.35,
        "customer_cancelled": 0.10,
    })

    # Recovery noise
    recovery_noise_std: float = 0.12

    # Demo scenario count per type
    demo_scenario_count: int = 8

    # Payment method sub-types
    payment_method_subtypes: dict[str, list[str]] = Field(default_factory=lambda: {
        "credit_card": ["visa", "mastercard", "amex", "rupay"],
        "debit_card": ["visa_debit", "mastercard_debit", "rupay_debit"],
        "upi": ["gpay", "phonepe", "paytm_upi", "bhim"],
        "net_banking": ["sbi", "hdfc", "icici", "axis", "kotak"],
        "wallet": ["paytm", "mobikwik", "freecharge", "amazonpay"],
    })


# ─── Name Generation ──────────────────────────────────────────────────────────

FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Vikram", "Ananya", "Arjun", "Kavya",
    "Rohit", "Meera", "Nikhil", "Deepika", "Saurabh", "Nisha", "Karan",
    "Pooja", "Aditya", "Ritika", "Manish", "Divya", "Suresh", "Anjali",
    "Rajesh", "Swati", "Vivek", "Shruti", "Sandeep", "Pallavi", "Gaurav",
    "Neha", "James", "Sarah", "Michael", "Emma", "David", "Olivia",
    "John", "Sophia", "Robert", "Isabella", "William", "Mia", "Thomas",
    "Emily", "Daniel", "Ava", "Chen", "Wei", "Yuki", "Aiko",
]

LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Gupta", "Mehta", "Joshi",
    "Verma", "Reddy", "Nair", "Iyer", "Rao", "Choudhary", "Mishra",
    "Banerjee", "Das", "Agarwal", "Malhotra", "Kapoor", "Bhat",
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Wilson",
    "Taylor", "Anderson", "Thomas", "Martin", "Lee", "Wang", "Chen",
    "Kim", "Tanaka", "Sato", "Muller", "Schmidt",
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _sigmoid(x: np.ndarray) -> np.ndarray:
    """Numerically stable sigmoid."""
    return np.where(x >= 0, 1 / (1 + np.exp(-x)), np.exp(x) / (1 + np.exp(x)))


def _normalize_weights(weights: dict[str, float]) -> tuple[list[str], np.ndarray]:
    """Return (keys, normalized_probabilities) from a weight dict."""
    keys = list(weights.keys())
    vals = np.array([weights[k] for k in keys], dtype=np.float64)
    return keys, vals / vals.sum()


# ─── Core Generator ──────────────────────────────────────────────────────────

class SyntheticDataGenerator:
    """Generates reproducible synthetic payment data for RecoverAI."""

    def __init__(self, config: GenerationConfig | None = None) -> None:
        self.config = config or GenerationConfig()
        self.rng = np.random.default_rng(self.config.seed)
        self._customers_df: pd.DataFrame | None = None
        self._payments_df: pd.DataFrame | None = None

    # ── Public API ────────────────────────────────────────────────────────

    def generate(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Generate customers and payments DataFrames.

        Returns:
            (customers_df, payments_df)
        """
        self._customers_df = self._generate_customers()
        self._payments_df = self._generate_payments()
        self._inject_demo_scenarios()
        return self._customers_df, self._payments_df

    def save(self, output_dir: str | Path) -> dict[str, Path]:
        """Save generated data to CSV and config/report to JSON.

        Args:
            output_dir: Directory to write files into.

        Returns:
            Dict of file type → Path.
        """
        if self._customers_df is None or self._payments_df is None:
            raise RuntimeError("Call generate() before save().")

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        paths: dict[str, Path] = {}

        # CSVs
        cust_path = out / "customers.csv"
        pay_path = out / "payments.csv"
        self._customers_df.to_csv(cust_path, index=False)
        self._payments_df.to_csv(pay_path, index=False)
        paths["customers_csv"] = cust_path
        paths["payments_csv"] = pay_path

        # Generation config
        config_path = out / "generation_config.json"
        config_path.write_text(
            self.config.model_dump_json(indent=2), encoding="utf-8"
        )
        paths["generation_config"] = config_path

        # Data quality report
        report = self._build_quality_report()
        report_path = out / "data_quality_report.json"
        report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        paths["data_quality_report"] = report_path

        return paths

    def validate(self) -> dict[str, bool]:
        """Run all validation checks. Returns dict of check_name → passed."""
        if self._payments_df is None or self._customers_df is None:
            raise RuntimeError("Call generate() before validate().")

        pay = self._payments_df
        cust = self._customers_df
        valid_failure_reasons = set(self.config.failure_type_weights.keys())
        valid_methods = set(self.config.payment_method_weights.keys())
        valid_segments = set(self.config.segment_weights.keys())

        results: dict[str, bool] = {}

        # 1. No duplicate payment IDs
        results["no_duplicate_payment_ids"] = pay["payment_id"].is_unique

        # 2. No duplicate customer IDs
        results["no_duplicate_customer_ids"] = cust["customer_id"].is_unique

        # 3. Valid foreign keys
        cust_ids = set(cust["customer_id"])
        results["no_invalid_foreign_keys"] = pay["customer_id"].isin(cust_ids).all()

        # 4. No negative amounts
        results["no_negative_amounts"] = (pay["amount"] >= 0).all()

        # 5. No impossible dates
        date_start = pd.Timestamp(self.config.date_start)
        date_end = pd.Timestamp(self.config.date_end) + pd.Timedelta(days=1)
        timestamps = pd.to_datetime(pay["timestamp"])
        results["no_impossible_dates"] = (
            (timestamps >= date_start) & (timestamps <= date_end)
        ).all()

        # 6. Valid categoricals
        failed = pay[pay["payment_success"] == False]  # noqa: E712
        results["no_invalid_failure_reasons"] = (
            failed["failure_reason"].isin(valid_failure_reasons).all()
            if len(failed) > 0
            else True
        )
        results["no_invalid_payment_methods"] = pay["payment_method"].isin(valid_methods).all()
        results["no_invalid_segments"] = (
            pay["subscription_type"].dropna().isin(valid_segments).all()
        )

        # 7. Consistent status
        successful = pay[pay["payment_success"] == True]  # noqa: E712
        results["no_inconsistent_status_success"] = (
            successful["failure_reason"].isna().all() if len(successful) > 0 else True
        )
        results["no_inconsistent_status_failure"] = (
            failed["failure_reason"].notna().all() if len(failed) > 0 else True
        )

        # 8. No negative retry / recovery values
        results["no_negative_retry_count"] = (pay["retry_count"] >= 0).all()
        recovery_times = pay["recovery_time_hours"].dropna()
        results["no_negative_recovery_times"] = (
            (recovery_times >= 0).all() if len(recovery_times) > 0 else True
        )

        results["all_passed"] = all(results.values())
        return results

    # ── Customer Generation ───────────────────────────────────────────────

    def _generate_customers(self) -> pd.DataFrame:
        """Generate the customer table."""
        n = self.config.num_customers
        regions, region_probs = _normalize_weights(self.config.region_weights)
        segments, segment_probs = _normalize_weights(self.config.segment_weights)

        # Random selections
        region_choices = self.rng.choice(regions, size=n, p=region_probs)
        segment_choices = self.rng.choice(segments, size=n, p=segment_probs)

        # Created at: spread over the date range
        start_ts = pd.Timestamp(self.config.date_start).timestamp()
        end_ts = pd.Timestamp(self.config.date_end).timestamp()
        # Customers created in first 70% of the range (so they have payment history)
        cust_end_ts = start_ts + 0.7 * (end_ts - start_ts)
        created_timestamps = self.rng.uniform(start_ts, cust_end_ts, size=n)
        created_dates = pd.to_datetime(created_timestamps, unit="s")

        # Names
        first_idx = self.rng.integers(0, len(FIRST_NAMES), size=n)
        last_idx = self.rng.integers(0, len(LAST_NAMES), size=n)
        names = [f"{FIRST_NAMES[fi]} {LAST_NAMES[li]}" for fi, li in zip(first_idx, last_idx)]

        # Customer IDs
        customer_ids = [f"C{i:05d}" for i in range(1, n + 1)]

        # Emails
        emails = [
            f"{name.lower().replace(' ', '.')}+{cid}@example.com"
            for name, cid in zip(names, customer_ids)
        ]

        # CLV placeholder (will be computed after payments are generated)
        # For now set base CLV by segment
        clv_base = np.array([
            self.config.segment_clv_multiplier.get(s, 1.0) for s in segment_choices
        ])
        clv = clv_base * self.rng.lognormal(mean=7.5, sigma=0.8, size=n)
        clv = np.round(clv, 2)

        # Age in days (from created_at to date_end)
        end_dt = pd.Timestamp(self.config.date_end)
        age_days = ((end_dt - created_dates).total_seconds() / 86400).astype(int).values

        df = pd.DataFrame({
            "customer_id": customer_ids,
            "name": names,
            "email": emails,
            "region": region_choices,
            "segment": segment_choices,
            "created_at": created_dates,
            "lifetime_value": clv,
            "age_days": age_days,
        })
        return df

    # ── Payment Generation ────────────────────────────────────────────────

    def _generate_payments(self) -> pd.DataFrame:
        """Generate the payments table with all features and outcomes."""
        cust = self._customers_df
        if cust is None:
            raise RuntimeError("Customers must be generated first.")

        cfg = self.config
        n_payments = cfg.num_payments
        n_customers = len(cust)

        # Determine number of payments per customer (Poisson-like)
        avg_per_cust = n_payments / n_customers  # ~10
        payments_per_cust = self.rng.poisson(lam=avg_per_cust, size=n_customers)
        # Ensure at least 1 payment per customer
        payments_per_cust = np.maximum(payments_per_cust, 1)

        # Adjust to hit target total approximately
        total = payments_per_cust.sum()
        if total > n_payments * 1.1:
            # Scale down proportionally
            scale = n_payments / total
            payments_per_cust = np.maximum((payments_per_cust * scale).astype(int), 1)
        elif total < n_payments * 0.9:
            # Add more payments to random customers
            deficit = n_payments - payments_per_cust.sum()
            extra_idx = self.rng.choice(n_customers, size=max(deficit, 0), replace=True)
            for idx in extra_idx:
                payments_per_cust[idx] += 1

        # ── Precise adjustment to hit EXACT target ──────────────────────
        total = int(payments_per_cust.sum())
        if total < n_payments:
            # Add payments to random customers to fill the deficit
            deficit = n_payments - total
            fill_idx = self.rng.choice(n_customers, size=deficit, replace=True)
            for idx in fill_idx:
                payments_per_cust[idx] += 1
        elif total > n_payments:
            # Remove payments from customers with >1, one at a time
            surplus = total - n_payments
            # Candidates: customers with more than 1 payment
            candidates = np.where(payments_per_cust > 1)[0]
            self.rng.shuffle(candidates)
            removed = 0
            i = 0
            while removed < surplus and i < len(candidates):
                idx = candidates[i]
                if payments_per_cust[idx] > 1:
                    payments_per_cust[idx] -= 1
                    removed += 1
                i += 1
            # If still surplus (unlikely), cycle again
            while removed < surplus:
                candidates = np.where(payments_per_cust > 1)[0]
                if len(candidates) == 0:
                    break  # Can't remove more without leaving 0-payment customers
                idx = self.rng.choice(candidates)
                payments_per_cust[idx] -= 1
                removed += 1

        assert int(payments_per_cust.sum()) == n_payments, \
            f"Payment count mismatch: {payments_per_cust.sum()} != {n_payments}"

        # Build payment records
        records: list[dict] = []
        methods, method_probs = _normalize_weights(cfg.payment_method_weights)
        devices, device_probs = _normalize_weights(cfg.device_type_weights)

        for cust_idx in range(n_customers):
            cust_row = cust.iloc[cust_idx]
            num_pay = int(payments_per_cust[cust_idx])
            cust_records = self._generate_customer_payments(cust_row, num_pay, methods, method_probs, devices, device_probs)
            records.extend(cust_records)

        df = pd.DataFrame(records)

        # Assign globally unique payment IDs
        df = df.reset_index(drop=True)
        df["payment_id"] = [f"P{i:06d}" for i in range(1, len(df) + 1)]

        # Reorder columns
        col_order = [
            "payment_id", "customer_id", "timestamp", "amount", "currency",
            "payment_method", "payment_method_type", "device_type",
            "is_subscription", "subscription_type", "subscription_age_days",
            "payment_success", "failure_reason", "failure_category",
            "failure_temporary", "payment_gateway_status",
            "customer_age", "customer_region",
            "previous_successful_payments", "previous_failed_payments",
            "previous_retry_count", "days_since_last_payment",
            "customer_lifetime_value", "average_transaction_value",
            "payment_frequency", "last_successful_payment_days",
            "historical_recovery_rate", "retry_count",
            "simulated_recovery_probability", "actual_recovery_outcome",
            "recovered_after_failure", "recovery_time_hours", "recovered_amount",
            "demo_scenario",
        ]
        df = df[col_order]
        return df

    def _generate_customer_payments(
        self,
        cust_row: pd.Series,
        num_payments: int,
        methods: list[str],
        method_probs: np.ndarray,
        devices: list[str],
        device_probs: np.ndarray,
    ) -> list[dict]:
        """Generate all payment records for a single customer."""
        cfg = self.config
        customer_id = cust_row["customer_id"]
        segment = cust_row["segment"]
        region = cust_row["region"]
        created_at = pd.Timestamp(cust_row["created_at"])
        clv = cust_row["lifetime_value"]

        # Time range for this customer's payments
        cust_start = created_at
        cust_end = pd.Timestamp(cfg.date_end)
        time_range_s = (cust_end - cust_start).total_seconds()
        if time_range_s <= 0:
            time_range_s = 86400  # 1 day minimum

        is_subscription = segment != "free_trial"
        amount_params = cfg.segment_amount_params.get(segment, {"min": 99, "max": 999, "mean": 299})

        # Generate timestamps (sorted)
        offsets = np.sort(self.rng.uniform(0, time_range_s, size=num_payments))
        timestamps = [cust_start + timedelta(seconds=float(o)) for o in offsets]

        # Payment methods for this customer (some customers prefer specific methods)
        # Add slight customer preference bias
        cust_method_bias = self.rng.dirichlet(method_probs * 10 + 1)
        cust_methods = self.rng.choice(methods, size=num_payments, p=cust_method_bias)

        # Device types
        cust_devices = self.rng.choice(devices, size=num_payments, p=device_probs)

        # Amounts
        if segment == "free_trial":
            amounts = np.zeros(num_payments)
        else:
            amt_min = amount_params["min"]
            amt_max = amount_params["max"]
            amt_mean = amount_params["mean"]
            log_mean = np.log(max(amt_mean, 1.0))
            raw_amounts = self.rng.lognormal(mean=log_mean, sigma=0.5, size=num_payments)
            amounts = np.clip(raw_amounts, amt_min, amt_max)
            amounts = np.round(amounts, 2)

        # Track history as we go
        success_count = 0
        fail_count = 0
        retry_total = 0
        recovery_count = 0
        recovery_attempts = 0
        last_payment_ts: Optional[pd.Timestamp] = None
        last_success_ts: Optional[pd.Timestamp] = None
        total_amount = 0.0

        records: list[dict] = []

        for i in range(num_payments):
            ts = timestamps[i]
            amount = float(amounts[i])
            method = cust_methods[i]
            device = cust_devices[i]

            # Subscription age
            sub_age_days = (ts - created_at).days

            # Customer age at payment time
            cust_age = sub_age_days

            # Days since last payment
            if last_payment_ts is not None:
                days_since_last = max((ts - last_payment_ts).days, 0)
            else:
                days_since_last = 0

            # Last successful payment days ago
            if last_success_ts is not None:
                last_success_days = max((ts - last_success_ts).days, 0)
            else:
                last_success_days = sub_age_days  # never succeeded yet

            # Average transaction value
            avg_txn = total_amount / max(success_count + fail_count, 1)

            # Payment frequency (payments per 30 days)
            history_days = max(sub_age_days, 1)
            pay_freq = (success_count + fail_count) / (history_days / 30.0) if history_days > 0 else 0

            # Historical recovery rate
            hist_recovery = recovery_count / max(recovery_attempts, 1)

            # ── Determine success/failure ──
            failure_prob = self._compute_failure_probability(
                method, amount, segment, region, sub_age_days, fail_count,
            )
            payment_success = bool(self.rng.random() >= failure_prob)

            # For successful payments
            failure_reason: Optional[str] = None
            failure_category: Optional[str] = None
            failure_temporary: Optional[bool] = None
            gateway_status: Optional[str] = None
            sim_recovery_prob: Optional[float] = None
            actual_recovery: Optional[bool] = None
            recovered_after: Optional[bool] = None
            recovery_time: Optional[float] = None
            recovered_amount: Optional[float] = None
            retry_count = 0

            if not payment_success and segment != "free_trial":
                # Assign failure reason
                failure_reason = self._pick_failure_reason(method, amount, sub_age_days)
                failure_category = cfg.failure_category_map.get(failure_reason, "unknown")
                failure_temporary = cfg.failure_temporary_map.get(failure_reason, False)
                gateway_status = "failed"

                # Retry count for this payment (0-4)
                retry_count = int(self.rng.integers(0, 5))

                # ── Compute simulated recovery probability ──
                sim_recovery_prob = self._compute_recovery_probability(
                    failure_reason=failure_reason,
                    success_count=success_count,
                    fail_count=fail_count,
                    amount=amount,
                    method=method,
                    sub_age_days=sub_age_days,
                    retry_count=retry_count,
                    clv=clv,
                )

                # ── Sample actual outcome ──
                actual_recovery = bool(self.rng.random() < sim_recovery_prob)
                recovered_after = actual_recovery
                recovery_attempts += 1

                if actual_recovery:
                    recovery_count += 1
                    recovered_amount = amount
                    # Recovery time depends on failure type and retries
                    base_hours = {"network_failure": 1, "temporary_gateway_failure": 2,
                                  "payment_timeout": 4, "insufficient_funds": 48,
                                  "bank_declined": 24, "limit_exceeded": 72,
                                  "authentication_failure": 96, "expired_card": 168,
                                  "invalid_payment_details": 192, "customer_cancelled": 240}
                    base_h = base_hours.get(failure_reason, 48)
                    recovery_time = float(max(
                        base_h * (0.5 + self.rng.random()) + retry_count * 12, 1.0
                    ))
                else:
                    recovered_amount = 0.0
                    recovery_time = None

                fail_count += 1
            elif payment_success:
                gateway_status = "captured"
                success_count += 1
                last_success_ts = ts
                total_amount += amount
            else:
                # free_trial with "failure" — just make it success
                payment_success = True
                gateway_status = "captured"
                success_count += 1
                last_success_ts = ts

            last_payment_ts = ts
            retry_total += retry_count

            # Payment method subtype
            subtypes = cfg.payment_method_subtypes.get(method, [method])
            method_type = self.rng.choice(subtypes)

            records.append({
                "customer_id": customer_id,
                "timestamp": ts.isoformat(),
                "amount": amount,
                "currency": cfg.currency,
                "payment_method": method,
                "payment_method_type": method_type,
                "device_type": device,
                "is_subscription": is_subscription,
                "subscription_type": segment,
                "subscription_age_days": sub_age_days,
                "payment_success": payment_success,
                "failure_reason": failure_reason,
                "failure_category": failure_category,
                "failure_temporary": failure_temporary,
                "payment_gateway_status": gateway_status,
                "customer_age": cust_age,
                "customer_region": region,
                "previous_successful_payments": success_count - (1 if payment_success else 0),
                "previous_failed_payments": fail_count - (0 if payment_success else 1),
                "previous_retry_count": retry_total - retry_count,
                "days_since_last_payment": days_since_last,
                "customer_lifetime_value": round(clv, 2),
                "average_transaction_value": round(avg_txn, 2),
                "payment_frequency": round(pay_freq, 4),
                "last_successful_payment_days": last_success_days,
                "historical_recovery_rate": round(hist_recovery, 4),
                "retry_count": retry_count,
                "simulated_recovery_probability": round(sim_recovery_prob, 6) if sim_recovery_prob is not None else None,
                "actual_recovery_outcome": actual_recovery,
                "recovered_after_failure": recovered_after,
                "recovery_time_hours": round(recovery_time, 2) if recovery_time is not None else None,
                "recovered_amount": recovered_amount,
                "demo_scenario": None,
            })

        return records

    # ── Failure Probability ───────────────────────────────────────────────

    def _compute_failure_probability(
        self,
        method: str,
        amount: float,
        segment: str,
        region: str,
        sub_age_days: int,
        prev_failures: int,
    ) -> float:
        """Compute probability of payment failure based on context."""
        base = self.config.base_failure_rate

        # Method factor
        method_factors = {
            "credit_card": -0.03, "debit_card": 0.0, "upi": -0.05,
            "net_banking": 0.05, "wallet": -0.02,
        }
        base += method_factors.get(method, 0.0)

        # Higher amounts fail more
        if amount > 10000:
            base += 0.08
        elif amount > 5000:
            base += 0.04

        # New customers fail more
        if sub_age_days < 30:
            base += 0.06
        elif sub_age_days < 90:
            base += 0.02

        # Customers with failure history
        if prev_failures > 3:
            base += 0.05

        # Free trial never fails (no payment)
        if segment == "free_trial":
            return 0.0

        return float(np.clip(base, 0.05, 0.65))

    # ── Failure Reason Selection ──────────────────────────────────────────

    def _pick_failure_reason(self, method: str, amount: float, sub_age_days: int) -> str:
        """Select a failure reason with contextual weighting."""
        cfg = self.config
        weights = dict(cfg.failure_type_weights)  # copy

        # Higher amounts → more insufficient_funds
        if amount > 5000:
            weights["insufficient_funds"] *= 1.8
            weights["limit_exceeded"] *= 1.5

        # Card methods → more expired_card
        if method in ("credit_card", "debit_card"):
            weights["expired_card"] *= 2.0
            weights["invalid_payment_details"] *= 1.5
        else:
            weights["expired_card"] *= 0.3
            weights["invalid_payment_details"] *= 0.3

        # Older subscriptions → more expired_card
        if sub_age_days > 365:
            weights["expired_card"] *= 1.5

        # UPI → more authentication failures
        if method == "upi":
            weights["authentication_failure"] *= 1.8

        reasons, probs = _normalize_weights(weights)
        return str(self.rng.choice(reasons, p=probs))

    # ── Recovery Probability (Multi-Factor) ───────────────────────────────

    def _compute_recovery_probability(
        self,
        failure_reason: str,
        success_count: int,
        fail_count: int,
        amount: float,
        method: str,
        sub_age_days: int,
        retry_count: int,
        clv: float,
    ) -> float:
        """Compute simulated recovery probability from multiple factors + noise.

        This probability is used ONLY to generate the target variable.
        It is NEVER used as an ML input feature.
        """
        cfg = self.config
        w = cfg.recovery_weights

        # Factor 1: Failure type (0-1)
        f_failure = cfg.failure_recovery_factor.get(failure_reason, 0.3)

        # Factor 2: Customer history (0-1)
        total_payments = success_count + fail_count
        if total_payments > 0:
            f_history = min(success_count / max(total_payments, 1), 1.0)
        else:
            f_history = 0.5

        # Factor 3: Amount (inverse — higher amount, slightly lower recovery)
        if amount > 20000:
            f_amount = 0.3
        elif amount > 5000:
            f_amount = 0.5
        elif amount > 1000:
            f_amount = 0.7
        else:
            f_amount = 0.85

        # Factor 4: Payment method
        method_recovery = {
            "credit_card": 0.65, "debit_card": 0.55, "upi": 0.70,
            "net_banking": 0.50, "wallet": 0.60,
        }
        f_method = method_recovery.get(method, 0.5)

        # Factor 5: Subscription age (longer tenure → higher recovery)
        if sub_age_days > 365:
            f_sub_age = 0.75
        elif sub_age_days > 180:
            f_sub_age = 0.65
        elif sub_age_days > 60:
            f_sub_age = 0.50
        else:
            f_sub_age = 0.35

        # Factor 6: Retry count (more retries → diminishing returns)
        if retry_count == 0:
            f_retry = 0.70
        elif retry_count <= 2:
            f_retry = 0.50
        else:
            f_retry = 0.25

        # Factor 7: Customer value (high CLV → slightly higher recovery effort success)
        log_clv = np.log1p(max(clv, 0))
        f_value = float(np.clip(log_clv / 12.0, 0.1, 0.9))

        # Weighted combination (logit space for better calibration)
        # Scale by 3.0 to widen the sigmoid output spread from the narrow
        # [-1, 1] range to [-3, 3], giving probabilities spanning ~0.05–0.95
        raw = 3.0 * (
            w["failure_type"] * (f_failure * 2 - 1)
            + w["customer_history"] * (f_history * 2 - 1)
            + w["amount"] * (f_amount * 2 - 1)
            + w["payment_method"] * (f_method * 2 - 1)
            + w["subscription_age"] * (f_sub_age * 2 - 1)
            + w["retry_count"] * (f_retry * 2 - 1)
            + w["customer_value"] * (f_value * 2 - 1)
        )

        # Add controlled noise (scaled to match the logit magnitude)
        noise = float(self.rng.normal(0, cfg.recovery_noise_std * 3.0))
        prob = float(_sigmoid(np.array([raw + noise]))[0])

        return float(np.clip(prob, 0.02, 0.98))

    # ── Demo Scenarios ────────────────────────────────────────────────────

    def _inject_demo_scenarios(self) -> None:
        """Tag specific records with demo scenario labels."""
        if self._payments_df is None:
            return

        df = self._payments_df
        failed = df[df["payment_success"] == False].copy()  # noqa: E712
        if len(failed) == 0:
            return

        n = min(self.config.demo_scenario_count, len(failed) // 7)
        if n < 1:
            n = 1

        # Sort failed payments for deterministic selection
        failed_sorted = failed.sort_values("payment_id").reset_index()

        scenarios = {
            "HIGH_RECOVERY_CASE": failed_sorted[
                (failed_sorted["simulated_recovery_probability"].notna()) &
                (failed_sorted["simulated_recovery_probability"] > 0.75) &
                (failed_sorted["actual_recovery_outcome"].fillna(False).astype(bool))
            ],
            "MEDIUM_RECOVERY_CASE": failed_sorted[
                (failed_sorted["simulated_recovery_probability"].notna()) &
                (failed_sorted["simulated_recovery_probability"].between(0.35, 0.65))
            ],
            "LOW_RECOVERY_CASE": failed_sorted[
                (failed_sorted["simulated_recovery_probability"].notna()) &
                (failed_sorted["simulated_recovery_probability"] < 0.30)
            ],
            "HIGH_VALUE_CUSTOMER": failed_sorted[
                failed_sorted["customer_lifetime_value"] > failed_sorted["customer_lifetime_value"].quantile(0.95)
            ],
            "MULTIPLE_RETRY_CASE": failed_sorted[
                failed_sorted["retry_count"] >= 3
            ],
            "TEMPORARY_FAILURE_CASE": failed_sorted[
                failed_sorted["failure_reason"].isin(["temporary_gateway_failure", "network_failure"])
            ],
            "PERMANENT_FAILURE_CASE": failed_sorted[
                failed_sorted["failure_reason"].isin(["expired_card", "customer_cancelled"])
            ],
        }

        tagged_indices: set[int] = set()
        for scenario_name, candidates in scenarios.items():
            # Exclude already-tagged
            available = candidates[~candidates["index"].isin(tagged_indices)]
            if len(available) == 0:
                continue
            selected = available.head(n)
            for _, row in selected.iterrows():
                orig_idx = row["index"]
                df.at[orig_idx, "demo_scenario"] = scenario_name
                tagged_indices.add(orig_idx)

    # ── Quality Report ────────────────────────────────────────────────────

    def _build_quality_report(self) -> dict:
        """Build the data quality report dict."""
        if self._payments_df is None or self._customers_df is None:
            raise RuntimeError("Data not generated yet.")

        pay = self._payments_df
        cust = self._customers_df
        failed = pay[pay["payment_success"] == False]  # noqa: E712

        validation = self.validate()

        # Distributions
        failure_dist = (
            failed["failure_reason"].value_counts().to_dict() if len(failed) > 0 else {}
        )
        method_dist = pay["payment_method"].value_counts().to_dict()
        segment_dist = pay["subscription_type"].value_counts().to_dict()

        # Recovery rates
        failed_with_outcome = failed[failed["actual_recovery_outcome"].notna()]
        overall_recovery = (
            float(failed_with_outcome["actual_recovery_outcome"].mean())
            if len(failed_with_outcome) > 0 else 0.0
        )

        recovery_by_failure = {}
        if len(failed_with_outcome) > 0:
            for reason in failed_with_outcome["failure_reason"].unique():
                subset = failed_with_outcome[failed_with_outcome["failure_reason"] == reason]
                recovery_by_failure[reason] = round(float(subset["actual_recovery_outcome"].mean()), 4)

        recovery_by_method = {}
        if len(failed_with_outcome) > 0:
            for method in failed_with_outcome["payment_method"].unique():
                subset = failed_with_outcome[failed_with_outcome["payment_method"] == method]
                recovery_by_method[method] = round(float(subset["actual_recovery_outcome"].mean()), 4)

        # Amount stats
        amounts = pay[pay["amount"] > 0]["amount"]
        amount_stats = {
            "min": round(float(amounts.min()), 2) if len(amounts) > 0 else 0,
            "max": round(float(amounts.max()), 2) if len(amounts) > 0 else 0,
            "mean": round(float(amounts.mean()), 2) if len(amounts) > 0 else 0,
            "median": round(float(amounts.median()), 2) if len(amounts) > 0 else 0,
            "std": round(float(amounts.std()), 2) if len(amounts) > 0 else 0,
            "p25": round(float(amounts.quantile(0.25)), 2) if len(amounts) > 0 else 0,
            "p75": round(float(amounts.quantile(0.75)), 2) if len(amounts) > 0 else 0,
        }

        # Date range
        timestamps = pd.to_datetime(pay["timestamp"])
        date_range = {
            "earliest": str(timestamps.min().date()),
            "latest": str(timestamps.max().date()),
        }

        # Null counts
        null_counts = pay.isnull().sum().to_dict()

        return {
            "generation_timestamp": datetime.now().isoformat(),
            "seed": self.config.seed,
            "row_count": len(pay),
            "customer_count": len(cust),
            "unique_customers": int(cust["customer_id"].nunique()),
            "unique_payments": int(pay["payment_id"].nunique()),
            "successful_payments": int(pay["payment_success"].sum()),
            "failed_payments": int((~pay["payment_success"]).sum()),
            "null_counts": {k: int(v) for k, v in null_counts.items()},
            "duplicate_payment_ids": int(pay["payment_id"].duplicated().sum()),
            "duplicate_customer_ids": int(cust["customer_id"].duplicated().sum()),
            "distributions": {
                "failure_reason": {k: int(v) for k, v in failure_dist.items()},
                "payment_method": {k: int(v) for k, v in method_dist.items()},
                "customer_segment": {k: int(v) for k, v in segment_dist.items()},
            },
            "recovery_rates": {
                "overall": round(overall_recovery, 4),
                "by_failure_type": recovery_by_failure,
                "by_payment_method": recovery_by_method,
            },
            "amount_statistics": amount_stats,
            "date_range": date_range,
            "validation_results": validation,
            "feature_columns": FEATURE_COLUMNS,
            "leakage_columns": LEAKAGE_COLUMNS,
            "target_column": TARGET_COLUMN,
            "demo_scenarios_tagged": int(pay["demo_scenario"].notna().sum()),
        }
