# RecoverAI — Data Dictionary

> **All data is synthetic.** No real customer information is used.
> This document describes every field in the generated dataset, its type,
> whether it is available at prediction time, and its role in the ML pipeline.

---

## Column Roles

| Role | Meaning | Used as ML Input? |
|---|---|---|
| **identifier** | Primary/foreign key — not a feature | ❌ |
| **ML feature** | Available at prediction time, safe to use | ✅ |
| **target** | What the ML model predicts | ❌ (this is the label) |
| **outcome** | Post-decision data, forbidden as input | ❌ |
| **leakage** | Would artificially inflate accuracy | ❌ **NEVER** |
| **metadata** | Timestamps, labels, auxiliary info | ❌ |

---

## Customers Table (`customers.csv`)

| Column | Description | Datatype | Prediction-Time? | Role |
|---|---|---|---|---|
| `customer_id` | Unique customer identifier (e.g. `C00001`) | string | ✅ | identifier |
| `name` | Synthetic customer name | string | N/A | metadata |
| `email` | Synthetic email address | string | N/A | metadata |
| `region` | Customer region: IN, US, UK, SEA, EU | categorical | ✅ | ML feature |
| `segment` | Subscription segment: free_trial, basic, premium, enterprise | categorical | ✅ | ML feature |
| `created_at` | Account creation timestamp | datetime | ✅ | metadata |
| `lifetime_value` | Estimated customer lifetime value (₹) | float | ✅ | ML feature |
| `age_days` | Days since account creation (at dataset generation time) | int | ✅ | ML feature |

---

## Payments Table (`payments.csv`)

### Identifiers

| Column | Description | Datatype | Prediction-Time? | Role |
|---|---|---|---|---|
| `payment_id` | Unique payment identifier (e.g. `P000001`) | string | ✅ | identifier |
| `customer_id` | FK to customers table | string | ✅ | identifier |

### Payment Details (ML Features)

| Column | Description | Datatype | Prediction-Time? | Role |
|---|---|---|---|---|
| `amount` | Payment amount in INR | float | ✅ | ML feature |
| `currency` | Currency code (always `INR` in v1) | string | ✅ | ML feature |
| `payment_method` | Payment method: credit_card, debit_card, upi, net_banking, wallet | categorical | ✅ | ML feature |
| `payment_method_type` | Sub-type (e.g. visa, gpay, sbi) | categorical | ✅ | ML feature |
| `device_type` | Device: mobile, desktop, tablet | categorical | ✅ | ML feature |
| `is_subscription` | Whether this is a subscription payment | bool | ✅ | ML feature |
| `subscription_type` | Subscription tier: free_trial, basic, premium, enterprise | categorical | ✅ | ML feature |
| `subscription_age_days` | Days since customer signed up (at payment time) | int | ✅ | ML feature |
| `retry_count` | Number of retries already attempted for this payment | int | ✅ | ML feature |

### Failure Information (ML Features — available when payment fails)

| Column | Description | Datatype | Prediction-Time? | Role |
|---|---|---|---|---|
| `failure_reason` | Specific failure reason (e.g. `insufficient_funds`) | categorical | ✅ | ML feature |
| `failure_category` | Broad category: payment_issue, card_issue, bank_issue, technical_issue, auth_issue, customer_issue | categorical | ✅ | ML feature |
| `failure_temporary` | Whether the failure is expected to be temporary | bool | ✅ | ML feature |
| `payment_gateway_status` | Gateway response: captured, failed | categorical | ✅ | ML feature |

### Customer History Features (ML Features — computed at payment time)

| Column | Description | Datatype | Prediction-Time? | Role |
|---|---|---|---|---|
| `customer_age` | Days since customer account creation (at payment time) | int | ✅ | ML feature |
| `customer_region` | Customer's region (denormalized from customer table) | categorical | ✅ | ML feature |
| `previous_successful_payments` | Count of successful payments before this one | int | ✅ | ML feature |
| `previous_failed_payments` | Count of failed payments before this one | int | ✅ | ML feature |
| `previous_retry_count` | Total retry attempts before this payment | int | ✅ | ML feature |
| `days_since_last_payment` | Days since customer's previous payment | int | ✅ | ML feature |
| `customer_lifetime_value` | CLV estimate at payment time (₹) | float | ✅ | ML feature |
| `average_transaction_value` | Mean transaction amount up to this point (₹) | float | ✅ | ML feature |
| `payment_frequency` | Payments per 30 days up to this point | float | ✅ | ML feature |
| `last_successful_payment_days` | Days since last successful payment | int | ✅ | ML feature |
| `historical_recovery_rate` | Past recovery success rate for this customer | float | ✅ | ML feature |

### Status (Metadata)

| Column | Description | Datatype | Prediction-Time? | Role |
|---|---|---|---|---|
| `timestamp` | Payment attempt timestamp | datetime | ✅ | metadata |
| `payment_success` | Whether the payment succeeded | bool | ✅ | metadata (filter) |

### Outcome & Leakage Fields (⚠️ NEVER use as ML input)

| Column | Description | Datatype | Prediction-Time? | Role |
|---|---|---|---|---|
| `simulated_recovery_probability` | Synthetic ground-truth probability used to generate the target. Computed from a multi-factor formula with noise. | float | ❌ | **leakage** |
| `actual_recovery_outcome` | Binary 0/1 — did recovery succeed? Sampled from `bernoulli(simulated_recovery_probability)`. | bool | ❌ | **target** |
| `recovered_after_failure` | Same as `actual_recovery_outcome` (kept for readability) | bool | ❌ | **outcome** |
| `recovery_time_hours` | Hours from failure to successful recovery (null if not recovered) | float | ❌ | **outcome** |
| `recovered_amount` | Amount recovered in ₹ (0 if not recovered) | float | ❌ | **outcome** |

### Demo (Metadata)

| Column | Description | Datatype | Prediction-Time? | Role |
|---|---|---|---|---|
| `demo_scenario` | Tag for buildathon demo scenarios (null for most records) | string (nullable) | N/A | metadata |

---

## Leakage Prevention Rules

1. **`simulated_recovery_probability`** is the synthetic ground-truth used to *generate* the binary target. It must **NEVER** be used as an ML input feature — doing so would be circular.

2. **`actual_recovery_outcome`** is the **target variable** (label). The ML model predicts this. It must not appear in the feature set.

3. **`recovered_after_failure`**, **`recovery_time_hours`**, and **`recovered_amount`** are post-outcome fields that are only known *after* recovery. They must not be used as input features.

4. The ML preprocessing module (Phase 2) will assert:
   ```python
   assert not set(LEAKAGE_COLUMNS) & set(features_used), "Leakage detected!"
   ```

---

## Demo Scenario Tags

| Tag | Description |
|---|---|
| `HIGH_RECOVERY_CASE` | Recovery probability > 0.80, actually recovered |
| `MEDIUM_RECOVERY_CASE` | Recovery probability between 0.35–0.65 |
| `LOW_RECOVERY_CASE` | Recovery probability < 0.20 |
| `HIGH_VALUE_CUSTOMER` | Customer in top 5% by lifetime value |
| `MULTIPLE_RETRY_CASE` | 3+ retry attempts |
| `TEMPORARY_FAILURE_CASE` | Failure type: temporary_gateway_failure or network_failure |
| `PERMANENT_FAILURE_CASE` | Failure type: expired_card or customer_cancelled |

---

## Recovery Probability Generation (How the target is created)

The `simulated_recovery_probability` is computed as:

```
raw = w1·failure_type_factor + w2·customer_history_factor + w3·amount_factor
    + w4·payment_method_factor + w5·subscription_age_factor
    + w6·retry_count_factor + w7·customer_value_factor

simulated_recovery_probability = sigmoid(raw + noise)
actual_recovery_outcome = Bernoulli(simulated_recovery_probability)
```

This ensures recovery depends on multiple features with controlled noise, making the dataset non-trivially learnable without any single feature deterministically determining the target.
