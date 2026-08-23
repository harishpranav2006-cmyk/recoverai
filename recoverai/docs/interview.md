# RecoverAI — Judge & Panel Interview Preparation

> **Razorpay AI Buildathon Panel Q&A Guide**  
> *Track: Autonomous AI Revenue Recovery for Recurring & High-Velocity Payment Failures*

---

## Part 1: Product & Market Strategy

### Q1: What specific problem is RecoverAI solving?
**A:** RecoverAI solves **involuntary churn and lost revenue caused by recurring payment failures**. Up to 10% of subscription revenue fails every billing cycle. Traditional recovery systems use naive cron-based retries that blindly hit credit cards—wasting merchant gateway fees, damaging bank authorization trust, and annoying customers. RecoverAI uses calibrated ML and an autonomous AI agent to predict recovery likelihood, select the optimal retry delay or outreach channel, and recover revenue automatically.

### Q2: Why is this important for merchants and platforms like Razorpay?
**A:** Involuntary churn accounts for 20% to 40% of all SaaS and subscription churn. For high-growth businesses, recovering just 15–20% more failed payments directly increases Net Revenue Retention (NRR) and Customer Lifetime Value (CLV) without any additional customer acquisition cost (CAC).

### Q3: Who are the primary users of this platform?
**A:** 
1. **Finance & Billing Operations Teams**: Monitor overall recovered revenue, recovery rates by payment method, and gateway efficiency via the Executive Dashboard.
2. **Customer Success & Support Leads**: Review high-value VIP escalations in the Recovery Queue where automated recovery was paused for white-glove outreach.
3. **Engineering & Platform Teams**: Configure retry policies, monitor API latency, and review decision audit logs.

### Q4: Why not just let merchants handle recovery themselves?
**A:** Most merchants do not have dedicated ML teams to build probability scoring engines, feature preprocessors, and channel dispatchers. A platform-level solution like RecoverAI provides enterprise-grade AI recovery out of the box.

---

## Part 2: Machine Learning & Explainability

### Q5: Why did you choose Calibrated Logistic Regression over complex deep learning or gradient boosting?
**A:** In financial risk and revenue recovery, **probability calibration and explainability are far more important than a 0.5% gain in raw accuracy**. Logistic Regression with Sigmoid calibration achieved the lowest Brier score (0.1742) and high recall (82.4%) on our chronological test split. It provides linear SHAP explainability and sub-millisecond inference latency with zero risk of gradient-boosted overfitting on noisy financial data.

### Q6: What is probability calibration and why does it matter here?
**A:** Raw ML models often output uncalibrated scores that look like probabilities but are skewed. Calibration aligns the predicted score with the empirical real-world frequency. When RecoverAI predicts $p = 0.70$, exactly 7 out of 10 payments with that score recover. This allows our 3-tier Decision Engine thresholds ($p \ge 0.65$, $0.45 \le p < 0.65$, $p < 0.45$) to make reliable economic trade-offs.

### Q7: Why didn't you select XGBoost as the production model?
**A:** In our multi-model chronological benchmark, XGBoost achieved an F1 of 0.7267 vs. Calibrated Logistic Regression's 0.7310. While XGBoost is powerful, tree ensembles require heavy TreeSHAP background samplers, take significantly more memory to serve, and produce step-function probabilities that require secondary calibration. Logistic Regression gave us superior calibration, transparent coefficients, and $<20\text{ ms}$ end-to-end API latency.

### Q8: How did you guarantee zero future data leakage?
**A:** We strictly separated the transaction dataset into pre-failure predictive features and post-failure outcome fields (`recovered_after_failure`, `recovery_time_hours`, `recovered_amount`). Our preprocessing pipeline includes an automated validation check that immediately raises a fatal `ValueError` if any outcome column is passed during training or inference.

### Q9: Why is SHAP explainability necessary in a recovery platform?
**A:** Black-box AI decisions are unacceptable in fintech. When an AI agent decides to suppress a retry or dispatch a WhatsApp link, merchant operators need to know *why*. SHAP decomposes the prediction into exact additive factor attributions (e.g. `+ Solid customer payment track record`, `- High retry attempt count`).

### Q10: How would you improve the ML model once live production data flows in?
**A:** We would implement:
1. **Dynamic Bank & BIN Health Features**: Track real-time bank gateway downtime and issuer decline surges across card BINs.
2. **Time-of-Day / Day-of-Week Seasonality**: Model optimal retry hours per customer segment.
3. **Automated Weekly Retraining**: Continually update logistic regression weights as merchant customer mixes evolve.

---

## Part 3: Agentic AI & Decision Core

### Q11: Why use an autonomous AI agent instead of just an IF/ELSE script?
**A:** An IF/ELSE script is brittle and cannot adapt to multi-dimensional context. The AI Agent uses an 8-tool loop to investigate transaction history, evaluate failure codes, inspect customer lifetime value, draft channel-appropriate communication, and record structured audit trails.

### Q12: What does the LLM actually do versus deterministic code?
**A:** The LLM acts as an **investigative orchestrator and personalized communication generator**. It gathers context using structured tools and generates empathetic, channel-specific messages. The **Deterministic Decision Engine** acts as the financial safety governor, enforcing strict mathematical thresholds, retry limits, and regulatory constraints.

### Q13: Why don't you allow the LLM to make the final financial retry decision?
**A:** In fintech, non-deterministic LLM hallucinations on financial transactions are a critical liability. An LLM must never have the authority to bypass a 3-attempt retry cap or trigger an unconsented charge. The Decision Engine provides 100% deterministic, audit-guaranteed policy enforcement.

### Q14: What 8 tools does the Recovery Agent use?
**A:** 
1. `query_payment_details`
2. `get_customer_profile`
3. `predict_recovery_probability`
4. `get_failure_analysis`
5. `evaluate_decision_policy`
6. `generate_outreach_message`
7. `log_agent_decision`
8. `check_retry_safety`

### Q15: How do you prevent hallucinations and data leaks in customer communications?
**A:** Our messaging pipeline uses strict template sanitizers that scrub all internal ML probabilities, SHAP values, tier classifications, and system reason codes before any customer message is dispatched.

---

## Part 4: Fintech & Payment Operations

### Q16: How does RecoverAI prevent retry abuse and card network penalties?
**A:** Visa and Mastercard enforce strict retry guidelines (e.g. Visa Category 2 retry limits). RecoverAI enforces a hard cap of **maximum 3 retry attempts** and enforces failure-specific delay spacing (4h for network timeouts, 24h for insufficient funds).

### Q17: How do you handle permanent payment failures?
**A:** When a payment fails due to an `expired_card`, `invalid_account`, or `customer_cancelled`, the Decision Engine immediately blocks automated retries ($p = 0\%$) and routes the customer to self-serve payment method update workflows.

### Q18: How do you handle high-value payments or VIP customers?
**A:** 
- Any transaction $\ge ₹15,000$ is automatically flagged with `human_review_required: true`.
- Any customer with $\text{CLV} \ge ₹10,000$ who experiences an unrecoverable failure is escalated to white-glove human support rather than being cold-suppressed.

### Q19: How would RecoverAI integrate with Razorpay?
**A:** RecoverAI would ingest Razorpay webhook events (`payment.failed`, `subscription.halted`), evaluate recovery policies in real time, and trigger retries via Razorpay's Payments API (`/v1/payments/{id}/retry`) or dispatch Razorpay Payment Links.

### Q20: How does RecoverAI ensure idempotency?
**A:** Every recovery workflow execution checks existing recovery case records. If a payment has already been resolved or recovered, the workflow returns the cached outcome immediately without executing redundant retries or duplicating database records.

---

## Part 5: Production Architecture & Scalability

### Q21: Why was SQLite used for the prototype, and how would you migrate to production?
**A:** SQLite with WAL mode allowed us to build an entirely self-contained, zero-dependency, reproducible prototype. For live enterprise production, our SQLAlchemy ORM models can point directly to **PostgreSQL Amazon Aurora / Cloud SQL** with connection pooling via PgBouncer simply by changing the `DATABASE_URL` environment variable.

### Q22: How does the system scale to handle millions of daily webhooks?
**A:** We would place an asynchronous event queue (Kafka or AWS SQS) between the FastAPI ingestion endpoint and the Recovery Worker fleet. ML probability scoring runs in $<20\text{ ms}$, allowing worker nodes to process hundreds of recovery decisions per second per container.

### Q23: How is the system packaged and deployed?
**A:** RecoverAI is fully containerized using a multi-stage `Dockerfile` and `docker-compose.yml` that orchestrates the FastAPI REST API (port 8000) and Streamlit Dashboard (port 8501) with persistent volumes and health check dependencies.

### Q24: How would you monitor RecoverAI in a live cloud environment?
**A:** We implement `/api/v1/health`, `/api/v1/health/live`, and `/api/v1/health/ready` health probes for Kubernetes liveness/readiness checks, attach `X-Request-ID` and `X-Process-Time-Ms` headers for OpenTelemetry distributed tracing, and persist all decisions in an immutable audit ledger.

---

## Part 6: Business ROI & Economics

### Q25: How do you calculate ROI for a merchant?
**A:** 
$$\text{Net Recovered Revenue} = \text{Gross Recovered Amount} - \text{Gateway Retry Fees} - \text{Customer Outreach Costs}$$
By eliminating blind retries on permanent failures and focusing retries on Tier 1 ($p \ge 0.65$), RecoverAI maximizes net revenue while minimizing fees and customer friction.

### Q26: What is the cost of an unnecessary retry?
**A:** Each retry costs ₹2–₹5 in gateway processing fees, risks merchant card network chargeback/dispute flags, and risks bank card blocking. Suppressing unrecoverable retries saves thousands of dollars annually for high-volume merchants.

### Q27: What is the single most important KPI for this system?
**A:** **Net Recovered Revenue Captured** (percentage of recoverable failed revenue successfully captured by the platform).
