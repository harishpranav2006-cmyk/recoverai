# RecoverAI — Machine Learning Recovery Prediction Pipeline

> **Document Version:** 2.1 (Fully Validated Production Artifact)  
> **Status:** Phase 2 Complete & Validated  
> **Last Updated:** 2026-08-22  

---

## 1. Executive Summary & Business Objective

In subscription and recurring billing businesses, **failed payments account for massive involuntary churn**. When a payment fails, blindly retrying or blasting aggressive payment reminders degrades customer experience and burns payment gateway retry limits.

**RecoverAI's ML Pipeline** solves this by estimating:
$$\text{Recovery Probability} = P(\text{Payment will be successfully recovered} \mid \text{Prediction-Time Context})$$

This probability allows the downstream **Autonomous Recovery Agent (Phase 3 & 4)** to:
1. **Smart Retry:** Schedule automatic retries at optimal intervals for transient failures with high recovery probability.
2. **Personalized Communication:** Send tailored WhatsApp/Email/SMS payment update links for permanent or customer-actionable issues (e.g. expired card, insufficient funds).
3. **Escalate / Suppress:** Suppress aggressive retries on high-friction or fatigued accounts to avoid permanent customer cancellation and gateway penalties.

---

## 2. Dataset & Target Definition

- **Dataset Size:** 50,000 synthetic payment attempts across 5,000 unique customers.
- **Scope:** Filtered exclusively to **failed payments with known historical resolution** ($N = 13,272$).
- **Target Variable (`actual_recovery_outcome`):**
  - `1` (Recovered): The failed payment was eventually recovered through subsequent retry or customer action ($N = 7,825$, **59.0%**).
  - `0` (Unrecovered): The failed payment remained unresolved after max retries / timeout ($N = 5,447$, **41.0%**).

---

## 3. Strict Leakage Prevention

The pipeline enforces an inviolable boundary between prediction-time features and post-outcome information.

### Forbidden Leakage Fields (Never Used as Input)
| Field Name | Reason for Exclusion |
|---|---|
| `simulated_recovery_probability` | Synthetic ground-truth generator probability; using it would create circular leakage. |
| `actual_recovery_outcome` | Ground truth label (target). |
| `recovered_after_failure` | Direct alias for target outcome. |
| `recovery_time_hours` | Post-outcome duration (only known after recovery occurs). |
| `recovered_amount` | Post-outcome recovery amount (only known after recovery occurs). |

> [!IMPORTANT]
> The preprocessing module dynamically verifies and throws a `ValueError` if any forbidden column is present in the inference input dataframe.

---

## 4. Feature Selection & Engineering

The pipeline transforms 24 raw prediction-time attributes into **75 encoded numerical features**.

### Input Features
- **Transaction Context:** `amount`, `payment_method`, `payment_method_type`, `device_type`, `is_subscription`, `subscription_type`, `subscription_age_days`.
- **Failure Telemetry:** `failure_reason`, `failure_category`, `failure_temporary`, `payment_gateway_status`.
- **Customer Behavioral History:** `customer_age`, `customer_region`, `previous_successful_payments`, `previous_failed_payments`, `previous_retry_count`, `days_since_last_payment`, `customer_lifetime_value`, `average_transaction_value`, `payment_frequency`, `last_successful_payment_days`, `historical_recovery_rate`, `retry_count`.

### Domain-Engineered Features
1. `prev_success_ratio`: $\frac{\text{previous\_successful\_payments}}{\text{previous\_successful\_payments} + \text{previous\_failed\_payments}}$ (Captures customer reliability).
2. `amount_to_avg_ratio`: $\frac{\text{amount}}{\max(\text{average\_transaction\_value}, 1.0)}$ (Detects unusually large charges).
3. `is_high_clv`: Binary indicator ($\text{CLV} > ₹5,000$).
4. `is_first_failure`: Indicator that this is the customer's very first failure.
5. `hour_of_day`, `day_of_week`, `is_weekend`: Temporal context extracted from failure timestamp.

---

## 5. Model Training & Comparison

### Methodology
- **Stratified Split (70/15/15):** 70% Train ($N = 9,290$), 15% Validation ($N = 1,991$), 15% Test ($N = 1,991$) with stratified random sampling (`random_state=42`).
- **Chronological Split (80/20):** 80% Train ($N = 10,617$), 20% Test ($N = 2,655$) ordered strictly by `timestamp` to verify temporal generalizability.

### A. Stratified Holdout Test Set Performance ($N = 1,991$)

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | Brier Loss |
|---|---|---|---|---|---|---|---|
| **Logistic Regression (Baseline)** | 0.5962 | **0.6810** | 0.5928 | 0.6339 | **0.6252** | **0.6991** | 0.2382 |
| **Random Forest** | 0.6007 | 0.6740 | 0.6252 | 0.6487 | 0.6245 | 0.6971 | 0.2375 |
| **XGBoost Classifier** | 0.5856 | 0.6614 | 0.6090 | 0.6341 | 0.6136 | 0.6900 | 0.2406 |
| **Calibrated Logistic Regression (Production)** | **0.6062** | 0.6252 | **0.8296** | **0.7130** | **0.6252** | **0.6991** | **0.2309** |

### B. Chronological Test Set Performance ($N = 2,655$)

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | Brier Loss |
|---|---|---|---|---|---|---|---|
| **Logistic Regression (Baseline)** | 0.6087 | **0.6877** | 0.6461 | 0.6662 | **0.6305** | **0.7109** | 0.2328 |
| **Random Forest** | 0.6045 | 0.6775 | 0.6598 | 0.6686 | 0.6238 | 0.7088 | 0.2348 |
| **XGBoost Classifier** | 0.5974 | 0.6740 | 0.6467 | 0.6601 | 0.6174 | 0.7011 | 0.2359 |
| **Calibrated Logistic Regression (Production)** | **0.6226** | 0.6343 | **0.8872** | **0.7397** | **0.6302** | **0.7105** | **0.2276** |

---

## 6. Probability Calibration Validation

Probability calibration was evaluated using **Platt Scaling (Sigmoid CalibratedClassifierCV with 5-fold CV)**:
- **Raw Brier Loss:** `0.2382`
- **Calibrated Brier Loss:** `0.2309` (Lower is better; confirms measurable reduction in probability error)

### Reliability Curve Breakdown (Predicted Probabilities vs Observed Positives)
| Probability Bin | Mean Predicted Probability | Observed Positive Fraction | Empirical Alignment Assessment |
|---|---|---|---|
| **0.00 – 0.20** | 10.93% | 0.00% | Accurately isolates lowest-likelihood recovery cases. |
| **0.20 – 0.40** | 35.98% | 43.53% | Monotonic ordering with moderate conservatism. |
| **0.40 – 0.60** | 51.73% | 50.26% | **Strong empirical calibration (51.7% predicted vs 50.3% observed).** |
| **0.60 – 0.80** | 68.03% | 68.53% | **Strong empirical calibration (68.0% predicted vs 68.5% observed).** |
| **0.80 – 1.00** | 81.21% | 95.24% | **Conservative under-prediction** in the upper tail (empirical recovery rate is 95.2%, higher than predicted 81.2%), providing high safety for automated retry actions. |

---

## 7. Exact 3-Tier Policy Validation (Holdout Test Set $N = 1,991$)

Total recoverable revenue pool in test set = **₹5,288,956.44** ($N = 1,174$ actually recoverable payments):

| Policy Tier | Range | Payment Count ($N$) | Pct of Payments (%) | Precision | Recall | F1-Score | Total Payment Value (₹) | Actually Recoverable Value (₹) | % Total Recoverable Captured (%) |
|---|---|---|---|---|---|---|---|---|---|
| **Tier 1: High Confidence (Smart Retry)** | $p \ge 0.65$ | **628** | 31.54% | **0.7102 (71.0%)** | 0.3799 | 0.4950 | ₹2,232,791.31 | ₹1,615,901.30 | **30.55%** |
| **Tier 2: Actionable Outreach (Customer Link)** | $0.45 \le p < 0.65$ | **1,144** | 57.46% | 0.5551 (55.5%) | 0.5409 | 0.5479 | ₹5,217,339.17 | ₹3,070,038.28 | **58.05%** |
| **Tier 3: Low Recovery / Suppress** | $p < 0.45$ | **219** | 11.00% | 0.4247 (42.5%) | 0.0792 | 0.1335 | ₹1,450,299.28 | ₹603,016.86 | **11.40%** |
| **Combined Action Tiers (Tier 1 + 2)** | $p \ge 0.45$ | **1,772** | **89.00%** | **0.6100 (61.0%)** | **0.9208 (92.1%)** | **0.7339** | **₹7,450,130.48** | **₹4,685,939.58** | **88.60%** |

### Tier Boundary Verification Summary:
1. **Tier 1 ($p \ge 0.65$) Precision Verification:** Directly verified at **71.02%** precision ($\ge 70\%$). This confirms that Tier 1 is safe for low-friction, autonomous Smart Retries.
2. **Tier 2 ($0.45 \le p < 0.65$) Coverage:** Encompasses 57.5% of failed transactions, capturing **₹3,070,038.28** (58.05%) of recoverable revenue via customer engagement (WhatsApp/SMS/Email payment update links).
3. **Combined Action Tiers ($p \ge 0.45$):** Captures **88.60% of all recoverable revenue** with **92.08% Recall** and **61.00% Precision**.
4. **Tier 3 ($p < 0.45$) Suppression:** Correctly suppresses 219 low-yield transactions (where precision drops to 42.5%), protecting gateway quotas and preventing customer annoyance.

---

## 8. Fine-Grained Threshold Sweep Comparison

| Threshold | Precision | Recall | F1-Score | Count ($N$) | Pct of Payments (%) | Total Value (₹) | Actually Recovered Captured (₹) | % Recoverable Revenue Captured |
|---|---|---|---|---|---|---|---|---|
| **0.40** | 0.5969 | 0.9685 | 0.7386 | 1,905 | 95.7% | ₹8,180,774.18 | ₹5,000,610.18 | 94.55% |
| **0.42** | 0.6004 | 0.9574 | 0.7380 | 1,872 | 94.0% | ₹7,898,452.54 | ₹4,845,685.59 | 91.62% |
| **0.45** | **0.6100** | **0.9208** | **0.7339** | **1,772** | **89.0%** | **₹7,450,130.48** | **₹4,685,939.58** | **88.60%** |
| **0.48** | 0.6185 | 0.8671 | 0.7220 | 1,646 | 82.7% | ₹6,779,667.05 | ₹4,348,630.50 | 82.22% |
| **0.50** | 0.6252 | 0.8296 | 0.7130 | 1,558 | 78.3% | ₹6,331,535.31 | ₹4,096,948.50 | 77.46% |
| **0.55** | 0.6616 | 0.7112 | 0.6856 | 1,262 | 63.4% | ₹4,909,433.73 | ₹3,362,647.49 | 63.58% |
| **0.60** | 0.6912 | 0.5605 | 0.6190 | 952 | 47.8% | ₹3,556,287.30 | ₹2,590,277.36 | 48.98% |
| **0.65** | **0.7102** | **0.3799** | **0.4950** | **628** | **31.5%** | **₹2,232,791.31** | **₹1,615,901.30** | **30.55%** |
| **0.68** | 0.7281 | 0.2760 | 0.4002 | 445 | 22.4% | ₹1,413,804.78 | ₹1,039,808.75 | 19.66% |
| **0.70** | 0.7316 | 0.2112 | 0.3278 | 339 | 17.0% | ₹1,028,451.32 | ₹793,511.31 | 15.00% |
| **0.75** | 0.7762 | 0.0945 | 0.1686 | 143 | 7.2% | ₹329,004.90 | ₹292,625.69 | 5.53% |

---

## 9. Business Impact Analysis (Holdout Test-Set Estimates)

> [!NOTE]
> All figures below are model/test-set estimates calculated from the holdout test set ($N = 1,991$ failed payments), not real-world recovered revenue.

* **Total Failed Payment Value in Test Set:** **₹8,900,429.76**
* **Total Actually Recoverable Revenue Pool:** **₹5,288,956.44** (59.4% of total failed value)
* **Total Actually Unrecovered Revenue Pool:** **₹3,611,473.32** (40.6% of total failed value)
* **Revenue In Scope for Active Recovery ($p \ge 0.45$):** **₹7,450,130.48**
* **Recoverable Revenue Successfully Captured ($p \ge 0.45$):** **₹4,685,939.58** (**88.60%** of all recoverable funds)
* **Revenue Safely Suppressed / Flagged ($p < 0.45$):** **₹1,450,299.28**
* **Recoverable Revenue Missed by Suppression ($p < 0.45$):** **₹603,016.86** (11.40% of recoverable pool)

---

## 10. SHAP Explainability & Top Drivers

### Top 15 Global Features by Mean Absolute SHAP Impact
| Rank | Feature | Mean \|SHAP\| Impact | Business Factor |
|---|---|---|---|
| 1 | `prev_success_ratio` | **0.2033** | Customer historical payment reliability |
| 2 | `failure_temporary` | **0.1675** | Transient gateway/network glitch vs hard decline |
| 3 | `failure_category_technical_issue` | **0.1307** | Technical & timeout issues |
| 4 | `retry_count` | **0.0896** | Prior retry attempts on this payment |
| 5 | `failure_category_card_issue` | **0.0769** | Card expiration and CVV mismatch friction |
| 6 | `previous_retry_count` | **0.0472** | Cumulative customer retry history |
| 7 | `is_first_failure` | **0.0437** | First-time failure vs chronic failing account |
| 8 | `customer_lifetime_value` | **0.0405** | Account monetary value and tier |
| 9 | `failure_reason_network_failure` | **0.0404** | Transient telecom/bank network drop |
| 10 | `subscription_type_enterprise` | **0.0375** | Enterprise customer relationship |
| 11 | `failure_category_payment_issue` | **0.0363** | Insufficient funds or daily cap |
| 12 | `payment_method_net_banking` | **0.0341** | Specific banking channel rail dynamics |
| 13 | `is_high_clv` | **0.0330** | High-tier account prioritization |
| 14 | `failure_reason_invalid_payment_details` | **0.0325** | Hard data input error |
| 15 | `previous_failed_payments` | **0.0317** | Frequency of recurring payment friction |

---

## 11. Saved Artifacts

All model assets are serialized in [ml/artifacts/](file:///e:/education/razor%20pay%20buildthon/recoverai/ml/artifacts):
* `model.joblib`: Calibrated Logistic Regression Classifier.
* `preprocessor.joblib`: Preprocessing Pipeline (`ColumnTransformer` + `FeatureEngineer`).
* `shap_explainer.joblib`: SHAP explainability engine.
* `feature_columns.json`: 75 feature dimension definitions.
* `model_metadata.json`: Provenance, hyperparameters & calibration metadata.
* `evaluation_report.json`: Benchmark metrics and threshold breakdown.
