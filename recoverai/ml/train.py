"""
RecoverAI — Model Training & Evaluation Pipeline
=================================================
Trains baseline Logistic Regression, Random Forest, and XGBoost models
on failed payment recovery data. Performs model comparison, probability
calibration, SHAP explainer initialization, and artifact serialization.

Usage:
    python ml/train.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ml.explainability import RecoveryExplainer
from ml.preprocessing import (
    ALL_INPUT_FEATURES,
    LEAKAGE_COLUMNS,
    TARGET_COLUMN,
    RecoveryDataPreprocessor,
    validate_prediction_input,
)

# Setup logging & console
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
console = Console(force_terminal=True, force_jupyter=False)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_and_validate_data(csv_path: Path) -> pd.DataFrame:
    """
    Loads payment records and filters to failed payments with valid outcomes.
    """
    console.print(f"  [dim]Loading dataset from: {csv_path}[/dim]")
    df = pd.read_csv(csv_path, low_memory=False)
    
    # Recovery prediction applies strictly to failed payments
    failed = df[df["payment_success"] == False].copy()  # noqa: E712
    failed = failed[failed[TARGET_COLUMN].notna()].copy()
    
    # Cast target to binary integer
    failed[TARGET_COLUMN] = failed[TARGET_COLUMN].astype(int)
    
    console.print(f"  Total failed payments with outcome: [bold cyan]{len(failed):,}[/bold cyan]")
    pos_count = int(failed[TARGET_COLUMN].sum())
    neg_count = len(failed) - pos_count
    console.print(
        f"  Target distribution: [green]Recovered={pos_count:,} ({pos_count/len(failed):.1%})[/green] | "
        f"[yellow]Unrecovered={neg_count:,} ({neg_count/len(failed):.1%})[/yellow]"
    )
    
    return failed


def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_name: str,
) -> Dict[str, Any]:
    """
    Computes comprehensive classification and probability calibration metrics.
    """
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_proba)
    pr_auc = average_precision_score(y_test, y_proba)
    brier = brier_score_loss(y_test, y_proba)
    ll = log_loss(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred).tolist()

    return {
        "model_name": model_name,
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(roc_auc), 4),
        "pr_auc": round(float(pr_auc), 4),
        "brier_score": round(float(brier), 4),
        "log_loss": round(float(ll), 4),
        "confusion_matrix": cm,
    }


def train_pipeline(
    data_path: Optional[Path] = None,
    artifacts_dir: Optional[Path] = None,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Executes full ML training, evaluation, comparison, and serialization.
    """
    if data_path is None:
        data_path = project_root / "data" / "synthetic" / "payments.csv"
    if artifacts_dir is None:
        artifacts_dir = project_root / "ml" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit(
        "[bold cyan]RecoverAI — ML Recovery Prediction Training Pipeline[/bold cyan]\n"
        "[dim]Model comparison, calibration, SHAP explainability & artifact generation[/dim]",
        border_style="cyan",
    ))

    # 1. Load Data
    data = load_and_validate_data(data_path)

    # 2. Strict Leakage Assertion
    console.print("  [bold yellow]Validating against data leakage...[/bold yellow]")
    input_cols = [c for c in data.columns if c not in LEAKAGE_COLUMNS and c != TARGET_COLUMN]
    X_raw = data[input_cols].copy()
    y = data[TARGET_COLUMN].values

    # 3. Train / Validation / Test Split (70% / 15% / 15%)
    console.print(f"  Splitting dataset (70% train / 15% val / 15% test, random_state={random_state})...")
    X_train_raw, X_temp, y_train, y_temp = train_test_split(
        X_raw, y, test_size=0.30, random_state=random_state, stratify=y
    )
    X_val_raw, X_test_raw, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=random_state, stratify=y_temp
    )

    console.print(f"    Train set: [bold]{len(X_train_raw):,}[/bold] samples")
    console.print(f"    Val set:   [bold]{len(X_val_raw):,}[/bold] samples")
    console.print(f"    Test set:  [bold]{len(X_test_raw):,}[/bold] samples")

    # 4. Preprocessing Fit & Transform
    console.print("  Fitting preprocessor on training data...")
    preprocessor = RecoveryDataPreprocessor()
    X_train = preprocessor.fit_transform(X_train_raw)
    X_val = preprocessor.transform(X_val_raw)
    X_test = preprocessor.transform(X_test_raw)
    feature_names = preprocessor.get_feature_names()
    console.print(f"  Transformed feature vector dimensionality: [bold green]{X_train.shape[1]}[/bold green] features")

    # 5. Model Training & Comparison
    console.print("\n[bold]Training Candidate Models...[/bold]")
    models: Dict[str, Any] = {}
    eval_results: Dict[str, Dict[str, Any]] = {}

    # Model 1: Logistic Regression (Baseline)
    with console.status("[bold green]Training Model 1: Logistic Regression..."):
        lr = LogisticRegression(
            max_iter=1000,
            C=1.0,
            class_weight="balanced",
            random_state=random_state,
        )
        lr.fit(X_train, y_train)
        models["logistic_regression"] = lr
        eval_results["logistic_regression"] = evaluate_model(lr, X_test, y_test, "Logistic Regression (Baseline)")

    # Model 2: Random Forest
    with console.status("[bold green]Training Model 2: Random Forest..."):
        rf = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        )
        rf.fit(X_train, y_train)
        models["random_forest"] = rf
        eval_results["random_forest"] = evaluate_model(rf, X_test, y_test, "Random Forest")

    # Model 3: XGBoost Classifier
    with console.status("[bold green]Training Model 3: XGBoost Classifier..."):
        pos_scale = (len(y_train) - y_train.sum()) / max(y_train.sum(), 1)
        xgb = XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            scale_pos_weight=pos_scale,
            eval_metric="logloss",
            random_state=random_state,
            n_jobs=-1,
        )
        xgb.fit(X_train, y_train)
        models["xgboost"] = xgb
        eval_results["xgboost"] = evaluate_model(xgb, X_test, y_test, "XGBoost Classifier")

    # 6. Model Comparison Table
    _print_comparison_table(eval_results)

    # 7. Model Selection
    # Select XGBoost or highest ROC-AUC/F1 model
    best_key = max(eval_results, key=lambda k: (eval_results[k]["roc_auc"], eval_results[k]["f1_score"]))
    best_raw_model = models[best_key]
    console.print(f"\n  [bold green]★ Selected Best Model:[/bold green] [bold cyan]{eval_results[best_key]['model_name']}[/bold cyan]")

    # 8. Probability Calibration Evaluation
    console.print("\n  [bold yellow]Evaluating Probability Calibration...[/bold yellow]")
    calibrated_model = CalibratedClassifierCV(
        estimator=models[best_key],
        method="sigmoid",
        cv=5,
    )
    calibrated_model.fit(X_train, y_train)
    calib_metrics = evaluate_model(calibrated_model, X_test, y_test, f"{eval_results[best_key]['model_name']} (Calibrated)")
    
    console.print(f"    Raw Brier Score:        {eval_results[best_key]['brier_score']:.4f}")
    console.print(f"    Calibrated Brier Score: {calib_metrics['brier_score']:.4f}")
    
    # Choose calibrated model if Brier score improved or maintained
    final_model = calibrated_model if calib_metrics["brier_score"] <= eval_results[best_key]["brier_score"] else best_raw_model
    final_metrics = calib_metrics if final_model == calibrated_model else eval_results[best_key]

    # 9. SHAP Explainability Engine
    console.print("\n  [bold yellow]Initializing SHAP Explainer...[/bold yellow]")
    sample_background = X_train[:300]
    explainer = RecoveryExplainer(model=best_raw_model, feature_names=feature_names, background_data=sample_background)
    global_importance = explainer.get_global_feature_importance(sample_background, top_k=15)
    
    _print_importance_table(global_importance)

    # 10. Temporal Validation Check
    console.print("\n  [dim]Conducting Chronological Validation Split Check...[/dim]")
    temporal_metrics = _evaluate_temporal_split(data, input_cols, random_state)
    console.print(f"    Chronological Split Test ROC-AUC: [bold]{temporal_metrics['roc_auc']:.4f}[/bold], F1: [bold]{temporal_metrics['f1_score']:.4f}[/bold]")

    # 11. Save Artifacts
    console.print("\n[bold]Saving Model Artifacts...[/bold]")
    model_path = artifacts_dir / "model.joblib"
    prep_path = artifacts_dir / "preprocessor.joblib"
    feat_path = artifacts_dir / "feature_columns.json"
    meta_path = artifacts_dir / "model_metadata.json"
    rep_path = artifacts_dir / "evaluation_report.json"
    shap_path = artifacts_dir / "shap_explainer.joblib"

    joblib.dump(final_model, model_path)
    joblib.dump(preprocessor, prep_path)
    joblib.dump(explainer, shap_path)

    feature_manifest = {
        "raw_features": input_cols,
        "transformed_features": feature_names,
        "num_features": len(feature_names),
        "categorical_features": [c for c in input_cols if c in preprocessor.pipeline.named_steps["column_transformer"].transformers[0][2]],
    }
    feat_path.write_text(json.dumps(feature_manifest, indent=2))

    metadata = {
        "model_name": eval_results[best_key]["model_name"],
        "model_type": str(type(final_model).__name__),
        "training_timestamp": datetime.now().isoformat(),
        "random_seed": random_state,
        "dataset_rows": len(data),
        "train_samples": len(X_train_raw),
        "val_samples": len(X_val_raw),
        "test_samples": len(X_test_raw),
        "num_features": len(feature_names),
        "is_calibrated": final_model == calibrated_model,
        "best_metrics": final_metrics,
        "temporal_validation_metrics": temporal_metrics,
    }
    meta_path.write_text(json.dumps(metadata, indent=2))

    report = {
        "model_comparison": eval_results,
        "selected_model": best_key,
        "final_metrics": final_metrics,
        "global_feature_importance": global_importance,
        "temporal_validation": temporal_metrics,
    }
    rep_path.write_text(json.dumps(report, indent=2))

    console.print(f"  [green]✓[/green] Model saved to:        {model_path}")
    console.print(f"  [green]✓[/green] Preprocessor saved to: {prep_path}")
    console.print(f"  [green]✓[/green] SHAP Explainer saved:  {shap_path}")
    console.print(f"  [green]✓[/green] Feature Manifest:      {feat_path}")
    console.print(f"  [green]✓[/green] Metadata & Report:     {meta_path}, {rep_path}")
    console.print("\n[bold green]✓ Phase 2 ML Training Pipeline Completed Successfully![/bold green]\n")

    return report


def _evaluate_temporal_split(
    data: pd.DataFrame,
    input_cols: List[str],
    random_state: int,
) -> Dict[str, float]:
    """
    Evaluates model performance using a chronological train/test split.
    """
    sorted_data = data.sort_values("timestamp").reset_index(drop=True)
    split_idx = int(len(sorted_data) * 0.80)
    
    train_df = sorted_data.iloc[:split_idx]
    test_df = sorted_data.iloc[split_idx:]

    prep = RecoveryDataPreprocessor()
    X_tr = prep.fit_transform(train_df[input_cols])
    y_tr = train_df[TARGET_COLUMN].values
    X_te = prep.transform(test_df[input_cols])
    y_te = test_df[TARGET_COLUMN].values

    clf = XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.05,
        random_state=random_state,
        eval_metric="logloss",
        n_jobs=-1,
    )
    clf.fit(X_tr, y_tr)
    
    preds = clf.predict(X_te)
    probs = clf.predict_proba(X_te)[:, 1]
    
    return {
        "accuracy": round(float(accuracy_score(y_te, preds)), 4),
        "roc_auc": round(float(roc_auc_score(y_te, probs)), 4),
        "f1_score": round(float(f1_score(y_te, preds, zero_division=0)), 4),
    }


def _print_comparison_table(results: Dict[str, Dict[str, Any]]) -> None:
    tbl = Table(title="Model Comparison on Holdout Test Set", box=box.ROUNDED)
    tbl.add_column("Model", style="cyan", no_wrap=True)
    tbl.add_column("Accuracy", justify="right")
    tbl.add_column("Precision", justify="right")
    tbl.add_column("Recall", justify="right")
    tbl.add_column("F1-Score", justify="right", style="bold green")
    tbl.add_column("ROC-AUC", justify="right", style="bold magenta")
    tbl.add_column("PR-AUC", justify="right")
    tbl.add_column("Brier Loss", justify="right")

    for key, m in results.items():
        tbl.add_row(
            m["model_name"],
            f"{m['accuracy']:.4f}",
            f"{m['precision']:.4f}",
            f"{m['recall']:.4f}",
            f"{m['f1_score']:.4f}",
            f"{m['roc_auc']:.4f}",
            f"{m['pr_auc']:.4f}",
            f"{m['brier_score']:.4f}",
        )
    console.print(tbl)


def _print_importance_table(importance: List[Dict[str, Any]]) -> None:
    tbl = Table(title="Top 15 Global Features by Mean |SHAP| Impact", box=box.SIMPLE_HEAVY)
    tbl.add_column("Rank", justify="right", style="dim")
    tbl.add_column("Feature", style="yellow")
    tbl.add_column("Mean |SHAP| Value", justify="right", style="bold")

    for i, item in enumerate(importance, start=1):
        tbl.add_row(str(i), item["feature"], f"{item['mean_abs_shap']:.4f}")
    console.print(tbl)


if __name__ == "__main__":
    train_pipeline()
