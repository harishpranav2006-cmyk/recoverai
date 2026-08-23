"""
RecoverAI — Phase 2 Final Deep Validation Script
=================================================
Calculates:
1. Full Chronological test evaluation for all 4 models.
2. Calibration curves & reliability metrics.
3. Multi-threshold analysis (0.30 - 0.80) with revenue capture.
4. Business revenue impact breakdown on test set.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from ml.preprocessing import (
    LEAKAGE_COLUMNS,
    TARGET_COLUMN,
    RecoveryDataPreprocessor,
)

os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def run_full_validation() -> dict:
    csv_path = project_root / "data" / "synthetic" / "payments.csv"
    df = pd.read_csv(csv_path, low_memory=False)

    # Filter to failed payments with outcome
    failed = df[df["payment_success"] == False].copy()
    failed = failed[failed[TARGET_COLUMN].notna()].copy()
    failed[TARGET_COLUMN] = failed[TARGET_COLUMN].astype(int)

    input_cols = [c for c in failed.columns if c not in LEAKAGE_COLUMNS and c != TARGET_COLUMN]

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Stratified Random Split (70/15/15) - Standard Test Set
    # ──────────────────────────────────────────────────────────────────────────
    X_raw = failed[input_cols].copy()
    y = failed[TARGET_COLUMN].values
    amounts = failed["amount"].values

    X_train_raw, X_temp, y_train, y_temp, amt_train, amt_temp = train_test_split(
        X_raw, y, amounts, test_size=0.30, random_state=42, stratify=y
    )
    X_val_raw, X_test_raw, y_val, y_test, amt_val, amt_test = train_test_split(
        X_temp, y_temp, amt_temp, test_size=0.50, random_state=42, stratify=y_temp
    )

    prep_strat = RecoveryDataPreprocessor()
    X_train = prep_strat.fit_transform(X_train_raw)
    X_val = prep_strat.transform(X_val_raw)
    X_test = prep_strat.transform(X_test_raw)

    # Train standard models
    lr = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced", random_state=42)
    lr.fit(X_train, y_train)

    rf = RandomForestClassifier(n_estimators=150, max_depth=10, min_samples_split=10, min_samples_leaf=4, class_weight="balanced", random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)

    pos_scale = (len(y_train) - y_train.sum()) / max(y_train.sum(), 1)
    xgb = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.05, subsample=0.85, colsample_bytree=0.85, scale_pos_weight=pos_scale, eval_metric="logloss", random_state=42, n_jobs=-1)
    xgb.fit(X_train, y_train)

    calib_lr = CalibratedClassifierCV(estimator=lr, method="sigmoid", cv=5)
    calib_lr.fit(X_train, y_train)

    calib_rf = CalibratedClassifierCV(estimator=rf, method="sigmoid", cv=5)
    calib_rf.fit(X_train, y_train)

    calib_xgb = CalibratedClassifierCV(estimator=xgb, method="sigmoid", cv=5)
    calib_xgb.fit(X_train, y_train)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Chronological Split (80% Train / 20% Test by timestamp)
    # ──────────────────────────────────────────────────────────────────────────
    failed_sorted = failed.sort_values("timestamp").reset_index(drop=True)
    split_idx = int(len(failed_sorted) * 0.80)
    
    chrono_train = failed_sorted.iloc[:split_idx]
    chrono_test = failed_sorted.iloc[split_idx:]

    prep_chrono = RecoveryDataPreprocessor()
    X_chrono_tr = prep_chrono.fit_transform(chrono_train[input_cols])
    y_chrono_tr = chrono_train[TARGET_COLUMN].values
    X_chrono_te = prep_chrono.transform(chrono_test[input_cols])
    y_chrono_te = chrono_test[TARGET_COLUMN].values

    # Train Chronological Models
    lr_chrono = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced", random_state=42)
    lr_chrono.fit(X_chrono_tr, y_chrono_tr)

    rf_chrono = RandomForestClassifier(n_estimators=150, max_depth=10, min_samples_split=10, min_samples_leaf=4, class_weight="balanced", random_state=42, n_jobs=-1)
    rf_chrono.fit(X_chrono_tr, y_chrono_tr)

    pos_scale_chrono = (len(y_chrono_tr) - y_chrono_tr.sum()) / max(y_chrono_tr.sum(), 1)
    xgb_chrono = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.05, subsample=0.85, colsample_bytree=0.85, scale_pos_weight=pos_scale_chrono, eval_metric="logloss", random_state=42, n_jobs=-1)
    xgb_chrono.fit(X_chrono_tr, y_chrono_tr)

    calib_lr_chrono = CalibratedClassifierCV(estimator=lr_chrono, method="sigmoid", cv=5)
    calib_lr_chrono.fit(X_chrono_tr, y_chrono_tr)

    def calc_metrics(m, X_t, y_t):
        p = m.predict(X_t)
        pr = m.predict_proba(X_t)[:, 1]
        return {
            "accuracy": round(float(accuracy_score(y_t, p)), 4),
            "precision": round(float(precision_score(y_t, p, zero_division=0)), 4),
            "recall": round(float(recall_score(y_t, p, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_t, p, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_t, pr)), 4),
            "pr_auc": round(float(average_precision_score(y_t, pr)), 4),
            "brier_score": round(float(brier_score_loss(y_t, pr)), 4),
        }

    chrono_results = {
        "logistic_regression": calc_metrics(lr_chrono, X_chrono_te, y_chrono_te),
        "random_forest": calc_metrics(rf_chrono, X_chrono_te, y_chrono_te),
        "xgboost": calc_metrics(xgb_chrono, X_chrono_te, y_chrono_te),
        "calibrated_logistic_regression": calc_metrics(calib_lr_chrono, X_chrono_te, y_chrono_te),
    }

    strat_results = {
        "logistic_regression": calc_metrics(lr, X_test, y_test),
        "random_forest": calc_metrics(rf, X_test, y_test),
        "xgboost": calc_metrics(xgb, X_test, y_test),
        "calibrated_logistic_regression": calc_metrics(calib_lr, X_test, y_test),
    }

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Calibration Curve & Reliability Analysis (Selected Model: Calibrated LR)
    # ──────────────────────────────────────────────────────────────────────────
    prob_uncalib = lr.predict_proba(X_test)[:, 1]
    prob_calib = calib_lr.predict_proba(X_test)[:, 1]

    fraction_of_pos_uncalib, mean_pred_uncalib = calibration_curve(y_test, prob_uncalib, n_bins=5)
    fraction_of_pos_calib, mean_pred_calib = calibration_curve(y_test, prob_calib, n_bins=5)

    calibration_details = {
        "raw_brier_score": round(float(brier_score_loss(y_test, prob_uncalib)), 4),
        "calibrated_brier_score": round(float(brier_score_loss(y_test, prob_calib)), 4),
        "uncalibrated_curve": {
            "mean_predicted_value": [round(float(v), 4) for v in mean_pred_uncalib],
            "fraction_of_positives": [round(float(v), 4) for v in fraction_of_pos_uncalib],
        },
        "calibrated_curve": {
            "mean_predicted_value": [round(float(v), 4) for v in mean_pred_calib],
            "fraction_of_positives": [round(float(v), 4) for v in fraction_of_pos_calib],
        },
    }

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Threshold Analysis on Holdout Test Set
    # ──────────────────────────────────────────────────────────────────────────
    thresholds = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
    threshold_metrics = []

    total_test_failed_revenue = float(np.sum(amt_test))
    total_test_actual_recovered_revenue = float(np.sum(amt_test[y_test == 1]))

    for t in thresholds:
        pred_t = (prob_calib >= t).astype(int)
        
        prec_t = precision_score(y_test, pred_t, zero_division=0)
        rec_t = recall_score(y_test, pred_t, zero_division=0)
        f1_t = f1_score(y_test, pred_t, zero_division=0)
        num_predicted_recoverable = int(np.sum(pred_t))
        
        # Financial impact
        pred_rec_mask = (pred_t == 1)
        actual_rec_mask = (y_test == 1)
        
        value_pred_recoverable = float(np.sum(amt_test[pred_rec_mask]))
        value_actual_recovered_in_pred = float(np.sum(amt_test[pred_rec_mask & actual_rec_mask]))
        pct_recoverable_rev_captured = (value_actual_recovered_in_pred / max(total_test_actual_recovered_revenue, 1.0)) * 100

        threshold_metrics.append({
            "threshold": t,
            "precision": round(float(prec_t), 4),
            "recall": round(float(rec_t), 4),
            "f1_score": round(float(f1_t), 4),
            "predicted_recoverable_count": num_predicted_recoverable,
            "predicted_recoverable_pct": round(float(num_predicted_recoverable / len(y_test) * 100), 1),
            "value_predicted_recoverable_inr": round(value_pred_recoverable, 2),
            "value_actual_recovered_captured_inr": round(value_actual_recovered_in_pred, 2),
            "pct_recoverable_revenue_captured": round(float(pct_recoverable_rev_captured), 2),
        })

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Business Impact Breakdown (at default operating threshold = 0.50)
    # ──────────────────────────────────────────────────────────────────────────
    pred_default = (prob_calib >= 0.50).astype(int)
    
    tp_mask = (pred_default == 1) & (y_test == 1)
    fp_mask = (pred_default == 1) & (y_test == 0)
    fn_mask = (pred_default == 0) & (y_test == 1)
    tn_mask = (pred_default == 0) & (y_test == 0)

    business_impact = {
        "test_set_sample_count": len(y_test),
        "total_failed_payment_value_inr": round(float(np.sum(amt_test)), 2),
        "total_actual_recovered_value_inr": round(float(np.sum(amt_test[y_test == 1])), 2),
        "total_actual_unrecovered_value_inr": round(float(np.sum(amt_test[y_test == 0])), 2),
        "value_predicted_recoverable_inr": round(float(np.sum(amt_test[pred_default == 1])), 2),
        "value_correctly_recovered_tp_inr": round(float(np.sum(amt_test[tp_mask])), 2),
        "value_false_positive_fp_inr": round(float(np.sum(amt_test[fp_mask])), 2),
        "value_missed_recovery_fn_inr": round(float(np.sum(amt_test[fn_mask])), 2),
        "value_correctly_suppressed_tn_inr": round(float(np.sum(amt_test[tn_mask])), 2),
        "revenue_recovery_capture_rate_pct": round(float(np.sum(amt_test[tp_mask]) / max(np.sum(amt_test[y_test == 1]), 1.0) * 100), 2),
    }

    full_report = {
        "stratified_results": strat_results,
        "chronological_results": chrono_results,
        "calibration_details": calibration_details,
        "threshold_metrics": threshold_metrics,
        "business_impact": business_impact,
    }

    return full_report


if __name__ == "__main__":
    rep = run_full_validation()
    print(json.dumps(rep, indent=2))
