"""
RecoverAI — Exact 3-Tier Policy Validation Script
=================================================
Evaluates exact tier boundaries (p >= 0.65, 0.45 <= p < 0.65, p < 0.45)
as well as fine-grained sweeps around 0.45 and 0.65 on the holdout test set.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

from ml.preprocessing import LEAKAGE_COLUMNS, TARGET_COLUMN, RecoveryDataPreprocessor

os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def evaluate_tier_policy():
    csv_path = project_root / "data" / "synthetic" / "payments.csv"
    df = pd.read_csv(csv_path, low_memory=False)

    failed = df[df["payment_success"] == False].copy()
    failed = failed[failed[TARGET_COLUMN].notna()].copy()
    failed[TARGET_COLUMN] = failed[TARGET_COLUMN].astype(int)

    input_cols = [c for c in failed.columns if c not in LEAKAGE_COLUMNS and c != TARGET_COLUMN]
    X_raw = failed[input_cols].copy()
    y = failed[TARGET_COLUMN].values
    amounts = failed["amount"].values

    # Stratified split matching training
    X_train_raw, X_temp, y_train, y_temp, amt_train, amt_temp = train_test_split(
        X_raw, y, amounts, test_size=0.30, random_state=42, stratify=y
    )
    X_val_raw, X_test_raw, y_val, y_test, amt_val, amt_test = train_test_split(
        X_temp, y_temp, amt_temp, test_size=0.50, random_state=42, stratify=y_temp
    )

    # Load artifacts
    model = joblib.load(project_root / "ml" / "artifacts" / "model.joblib")
    preprocessor = joblib.load(project_root / "ml" / "artifacts" / "preprocessor.joblib")

    X_test_trans = preprocessor.transform(X_test_raw)
    probs = model.predict_proba(X_test_trans)[:, 1]

    total_test_samples = len(y_test)
    total_failed_val = float(np.sum(amt_test))
    total_recovered_val = float(np.sum(amt_test[y_test == 1]))
    total_recovered_count = int(np.sum(y_test == 1))

    print(f"Test Samples: {total_test_samples:,}")
    print(f"Total Failed Value: ₹{total_failed_val:,.2f}")
    print(f"Total Recoverable Value: ₹{total_recovered_val:,.2f} ({total_recovered_count:,} payments)")
    print("-" * 70)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Exact 3-Tier Policy Evaluation
    # Tier 1: p >= 0.65
    # Tier 2: 0.45 <= p < 0.65
    # Tier 3: p < 0.45
    # ──────────────────────────────────────────────────────────────────────────
    tier1_mask = probs >= 0.65
    tier2_mask = (probs >= 0.45) & (probs < 0.65)
    tier3_mask = probs < 0.45

    def get_tier_metrics(mask, name):
        count = int(np.sum(mask))
        pct_count = (count / total_test_samples) * 100
        
        y_in_tier = y_test[mask]
        amt_in_tier = amt_test[mask]
        
        actual_rec_count = int(np.sum(y_in_tier == 1))
        precision = actual_rec_count / count if count > 0 else 0.0
        recall = actual_rec_count / total_recovered_count if total_recovered_count > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        tot_val = float(np.sum(amt_in_tier))
        rec_val_captured = float(np.sum(amt_in_tier[y_in_tier == 1]))
        pct_rec_val = (rec_val_captured / total_recovered_val) * 100 if total_recovered_val > 0 else 0.0
        
        return {
            "tier_name": name,
            "payment_count": count,
            "pct_of_all_payments": round(pct_count, 2),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "total_payment_value_inr": round(tot_val, 2),
            "actually_recoverable_value_inr": round(rec_val_captured, 2),
            "pct_total_recoverable_revenue_captured": round(pct_rec_val, 2),
        }

    t1_stats = get_tier_metrics(tier1_mask, "Tier 1: High Confidence (p >= 0.65)")
    t2_stats = get_tier_metrics(tier2_mask, "Tier 2: Actionable Outreach (0.45 <= p < 0.65)")
    t3_stats = get_tier_metrics(tier3_mask, "Tier 3: Low Recovery / Suppress (p < 0.45)")

    # Cumulative stats for action tiers (Tier 1 + Tier 2 = p >= 0.45)
    action_mask = probs >= 0.45
    action_stats = get_tier_metrics(action_mask, "Combined Action Tiers (p >= 0.45)")

    # Cumulative stats for Tier 1 as binary cutoff (p >= 0.65)
    cum_t1_pred = (probs >= 0.65).astype(int)
    cum_t1_prec = precision_score(y_test, cum_t1_pred, zero_division=0)
    cum_t1_rec = recall_score(y_test, cum_t1_pred, zero_division=0)
    cum_t1_f1 = f1_score(y_test, cum_t1_pred, zero_division=0)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Fine-Grained Threshold Sweep around 0.45 and 0.65 to find >70% precision
    # ──────────────────────────────────────────────────────────────────────────
    threshold_sweep = []
    for t in [0.40, 0.42, 0.45, 0.48, 0.50, 0.55, 0.60, 0.65, 0.68, 0.70, 0.72, 0.75]:
        pred_t = (probs >= t).astype(int)
        prec = precision_score(y_test, pred_t, zero_division=0)
        rec = recall_score(y_test, pred_t, zero_division=0)
        f1 = f1_score(y_test, pred_t, zero_division=0)
        cnt = int(np.sum(pred_t))
        val_tot = float(np.sum(amt_test[pred_t == 1]))
        val_rec = float(np.sum(amt_test[(pred_t == 1) & (y_test == 1)]))
        pct_rec = (val_rec / total_recovered_val) * 100
        
        threshold_sweep.append({
            "threshold": t,
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "count": cnt,
            "pct_payments": round(cnt / total_test_samples * 100, 1),
            "total_val_inr": round(val_tot, 2),
            "recovered_val_inr": round(val_rec, 2),
            "pct_revenue_captured": round(pct_rec, 2),
        })

    report = {
        "tier1": t1_stats,
        "tier2": t2_stats,
        "tier3": t3_stats,
        "combined_action_tiers": action_stats,
        "threshold_sweep": threshold_sweep,
    }
    return report


if __name__ == "__main__":
    rep = evaluate_tier_policy()
    print(json.dumps(rep, indent=2))
