# RecoverAI — 5-Minute Buildathon Demonstration & Pitch Guide

This guide outlines a structured, 5-minute presentation script and demonstration workflow for the **Razorpay AI Buildathon**.

---

## ⏱️ 5-Minute Demonstration Timeline

```
0:00 ──── 0:30 ──── 1:00 ──── 1:30 ──── 2:00 ──── 2:30 ──── 3:00 ──── 3:30 ──── 4:00 ──── 4:30 ──── 5:00
Problem   Overview   KPIs     Queue   ML/SHAP  Decision  Execute  Outcome  Analytics Arch    Closing
```

---

### [0:00 – 0:30] 1. Problem Statement: Involuntary Churn & Blind Retries
- **Speaker Pitch**: *"Payment failures are the silent killer of recurring digital revenue. Today, merchants rely on naive cron-based retry schedules that retry payments blindly. This causes three fatal issues: (1) high gateway decline fees, (2) card network retry fatigue, and (3) intrusive, generic customer communication."*
- **Visual Action**: Show the problem summary and involuntary churn metrics on the screen.

---

### [0:30 – 1:00] 2. The Solution & Executive Dashboard
- **Speaker Pitch**: *"RecoverAI is an autonomous AI revenue recovery platform that replaces blind retries with precision intelligence. Here is our live Executive Dashboard connected to our 50,000 transaction dataset."*
- **Visual Action**: Open `🏠 Overview` on the Streamlit dashboard:
  - Highlight **₹61.02M in failed volume** transformed into **₹34.89M in rescued revenue** (a **57.18% net recovery rate**).
  - Walk through the **7-Step Autonomous Recovery Pipeline stepper**.

---

### [1:00 – 1:30] 3. Triage in the Recovery Queue
- **Speaker Pitch**: *"Let’s step into the shoes of a payment operations manager. In our Prioritized Recovery Queue, every failed payment is dynamically evaluated and assigned an optimal recovery strategy."*
- **Visual Action**: Navigate to `🎯 Recovery Queue`:
  - Filter by **High Confidence ($p \ge 0.65$)** or **Actionable Outreach ($0.45 \le p < 0.65$)**.
  - Select a representative payment (e.g. `P000004` or `P000227`).

---

### [1:30 – 2:00] 4. Calibrated ML Probability & SHAP Explainability
- **Speaker Pitch**: *"Why should we retry this payment? RecoverAI doesn’t use a black box. Our Calibrated Logistic Regression model evaluated 75 zero-leakage features to predict a 73.2% recovery probability. More importantly, our SHAP explainability engine explains the exact business factors: strong past payment history and transient network failure characteristics."*
- **Visual Action**: Highlight the **Recovery Probability Gauge** and the **SHAP Feature Attribution breakdown**.

---

### [2:00 – 2:30] 5. Deterministic AI Decision Engine
- **Speaker Pitch**: *"Our 14-step deterministic Decision Engine enforces hard safety boundaries. For transient network errors, it schedules a 4-hour delay. For temporary bank declines, it enforces a 24-hour delay. For expired cards, it prevents retries entirely and generates personalized customer outreach."*
- **Visual Action**: Review the **AI Decision Card** (Strategy: `SMART_RETRY`, Reason Codes, 4-Hour Delay, Autonomous Flag).

---

### [2:30 – 3:30] 6. Live Simulated Execution & State Machine
- **Speaker Pitch**: *"Now, let's trigger the recovery. Watch RecoverAI invoke our simulated payment gateway in real time."*
- **Visual Action**:
  - Click `[ ▶️ Run Simulated Recovery Workflow ]`.
  - Show the simulated gateway authorization response (`GATEWAY_SUCCESS`, `₹12,989.82 Recovered`).
  - Scroll down to the **Chronological Recovery Lifecycle Timeline** showing the full event sequence (`FAILURE` $\rightarrow$ `ML_PREDICTION` $\rightarrow$ `AI_DECISION` $\rightarrow$ `RETRY_ATTEMPT` $\rightarrow$ `FINAL_OUTCOME`).

---

### [3:30 – 4:15] 7. Financial & Cohort Analytics
- **Speaker Pitch**: *"RecoverAI gives financial leaders complete visibility into recovery yield across strategies, failure causes, and customer tiers."*
- **Visual Action**: Navigate to `📊 Analytics`:
  - Show the **Monthly Recovery Velocity Trend**.
  - Compare the **71.02% precision yield** of Smart Retries against customer outreach conversions.
  - Review **Enterprise vs. Basic Customer Segment Yields**.

---

### [4:15 – 5:00] 8. Architecture & Business Impact
- **Speaker Pitch**: *"Under the hood, RecoverAI is built as a production-grade FastAPI backend (`/api/v1`) with 175 automated tests, strict idempotency, and complete simulation sandbox safety. By integrating directly into checkout and recurring billing workflows, RecoverAI turns failed payments into guaranteed revenue."*
- **Visual Action**: Open `⚙️ System` showing green health probes and OpenAPI Swagger docs (`/docs`).

---

## 🎯 7 Benchmark Demo Scenarios Reference Table

| Scenario Name | Payment ID | Amount | Failure Reason | Prob | Strategy | Expected Simulated Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. High Confidence Smart Retry** | `P000227` | ₹12,989.82 | `network_failure` | 73.2% | `SMART_RETRY` | `RECOVERED` (₹12,989.82) |
| **2. Actionable Customer Outreach** | `P000029` | ₹2,675.84 | `expired_card` | 57.0% | `PAYMENT_METHOD_UPDATE` | `WAITING_FOR_CUSTOMER` |
| **3. Low Recovery Suppression** | `P000133` | ₹253.96 | `authentication_failure` | 31.5% | `SUPPRESSION` | `SUPPRESSED` (Cost avoided) |
| **4. Transient Network Failure** | `P000138` | ₹339.50 | `network_failure` | 67.4% | `SMART_RETRY` | `RECOVERED` (₹339.50) |
| **5. Expired Card Update** | `P000063` | ₹3,772.71 | `expired_card` | 66.2% | `PAYMENT_METHOD_UPDATE` | `WAITING_FOR_CUSTOMER` |
| **6. Retry Fatigue Limit** | `P000052` | ₹402.50 | `authentication_failure` | 57.3% | `SUPPRESSION` | `SUPPRESSED` (Limit hit) |
| **7. VIP Enterprise High Touch** | `P000200` | ₹11,674.64 | `insufficient_funds` | 75.6% | `SMART_RETRY` | `RECOVERED` (₹11,674.64) |
