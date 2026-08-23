"""
RecoverAI — ML Pipeline & Prediction Tests
==========================================
Tests preprocessing, leakage prevention, model evaluation, probability
calibration, SHAP explainability, and inference interface.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ml.explainability import RecoveryExplainer, humanize_feature_explanation
from ml.predict import get_predictor, predict_recovery_probability
from ml.preprocessing import (
    ALL_INPUT_FEATURES,
    CATEGORICAL_FEATURES,
    LEAKAGE_COLUMNS,
    NUMERICAL_FEATURES,
    TARGET_COLUMN,
    RecoveryDataPreprocessor,
    validate_prediction_input,
)


@pytest.fixture
def sample_payment_record() -> dict:
    """A realistic single payment failure record for inference testing."""
    return {
        "payment_id": "P_TEST_001",
        "customer_id": "C_TEST_001",
        "amount": 2499.0,
        "currency": "INR",
        "payment_method": "credit_card",
        "payment_method_type": "visa",
        "device_type": "mobile",
        "is_subscription": True,
        "subscription_type": "premium",
        "subscription_age_days": 180,
        "failure_reason": "temporary_gateway_failure",
        "failure_category": "technical_issue",
        "failure_temporary": True,
        "payment_gateway_status": "failed",
        "customer_age": 180,
        "customer_region": "IN",
        "previous_successful_payments": 6,
        "previous_failed_payments": 1,
        "previous_retry_count": 0,
        "days_since_last_payment": 30,
        "customer_lifetime_value": 14994.0,
        "average_transaction_value": 2499.0,
        "payment_frequency": 1.0,
        "last_successful_payment_days": 30,
        "historical_recovery_rate": 0.85,
        "retry_count": 1,
    }


# ─── 1. Leakage Prevention Tests ──────────────────────────────────────────────

class TestLeakagePrevention:
    """Verifies that no leakage columns or post-outcome fields can enter the model."""

    def test_leakage_columns_rejected_in_validation(self, sample_payment_record: dict) -> None:
        for leakage_col in LEAKAGE_COLUMNS:
            bad_record = sample_payment_record.copy()
            bad_record[leakage_col] = 0.5
            df = pd.DataFrame([bad_record])
            with pytest.raises(ValueError, match="Data leakage detected"):
                validate_prediction_input(df, allow_target=False)

    def test_target_column_rejected_at_inference(self, sample_payment_record: dict) -> None:
        bad_record = sample_payment_record.copy()
        bad_record[TARGET_COLUMN] = 1
        df = pd.DataFrame([bad_record])
        with pytest.raises(ValueError, match="Data leakage detected"):
            validate_prediction_input(df, allow_target=False)

    def test_prediction_function_rejects_leakage(self, sample_payment_record: dict) -> None:
        bad_record = sample_payment_record.copy()
        bad_record["simulated_recovery_probability"] = 0.92
        with pytest.raises(ValueError):
            predict_recovery_probability(bad_record)


# ─── 2. Preprocessing Tests ──────────────────────────────────────────────────

class TestPreprocessing:
    """Verifies feature transformation and dimensionality stability."""

    def test_preprocessor_fit_transform(self, sample_payment_record: dict) -> None:
        df = pd.DataFrame([sample_payment_record] * 10)
        preprocessor = RecoveryDataPreprocessor()
        X_trans = preprocessor.fit_transform(df)

        assert isinstance(X_trans, np.ndarray)
        assert len(X_trans) == 10
        assert X_trans.shape[1] > len(ALL_INPUT_FEATURES)  # Expanded by OneHotEncoder
        assert len(preprocessor.get_feature_names()) == X_trans.shape[1]

    def test_preprocessor_handles_unseen_categories(self, sample_payment_record: dict) -> None:
        train_df = pd.DataFrame([sample_payment_record] * 5)
        preprocessor = RecoveryDataPreprocessor()
        preprocessor.fit(train_df)

        # Unseen category
        test_record = sample_payment_record.copy()
        test_record["payment_method"] = "cryptocurrency_unknown"
        test_df = pd.DataFrame([test_record])
        
        # Should not raise, should encode unseen as zeros
        X_trans = preprocessor.transform(test_df)
        assert X_trans.shape[0] == 1
        assert not np.isnan(X_trans).any()


# ─── 3. Inference & Prediction Tests ─────────────────────────────────────────

class TestPredictionInterface:
    """Verifies prediction outputs, probability constraints, and explanations."""

    def test_single_prediction_structure(self, sample_payment_record: dict) -> None:
        result = predict_recovery_probability(sample_payment_record, include_explanation=True)

        assert isinstance(result, dict)
        assert "payment_id" in result
        assert "recovery_probability" in result
        assert "prediction" in result
        assert "model_version" in result
        assert "confidence" in result
        assert "factors" in result

        # Check probability bounds
        assert 0.0 <= result["recovery_probability"] <= 1.0
        assert result["prediction"] in [0, 1]
        assert result["confidence"] in ["HIGH", "MODERATE"]

    def test_batch_prediction(self, sample_payment_record: dict) -> None:
        records = [sample_payment_record] * 5
        results = predict_recovery_probability(records, include_explanation=False)

        assert isinstance(results, list)
        assert len(results) == 5
        for item in results:
            assert 0.0 <= item["recovery_probability"] <= 1.0

    def test_shap_factors_content(self, sample_payment_record: dict) -> None:
        result = predict_recovery_probability(sample_payment_record, include_explanation=True)
        factors = result.get("factors", [])

        assert isinstance(factors, list)
        if len(factors) > 0:
            first = factors[0]
            assert "factor" in first
            assert "feature" in first
            assert "impact" in first
            assert first["impact"] in ["+", "-"]
            assert "shap" in first


# ─── 4. Artifact Integrity Tests ─────────────────────────────────────────────

class TestArtifactIntegrity:
    """Verifies all saved artifacts exist, are readable, and contain required metadata."""

    def test_artifacts_exist(self) -> None:
        artifacts_dir = project_root / "ml" / "artifacts"
        assert (artifacts_dir / "model.joblib").exists()
        assert (artifacts_dir / "preprocessor.joblib").exists()
        assert (artifacts_dir / "feature_columns.json").exists()
        assert (artifacts_dir / "model_metadata.json").exists()
        assert (artifacts_dir / "evaluation_report.json").exists()

    def test_metadata_contains_required_fields(self) -> None:
        meta_path = project_root / "ml" / "artifacts" / "model_metadata.json"
        meta = json.loads(meta_path.read_text())

        required_keys = [
            "model_name",
            "model_type",
            "training_timestamp",
            "random_seed",
            "dataset_rows",
            "best_metrics",
            "num_features",
        ]
        for key in required_keys:
            assert key in meta, f"Missing metadata key: {key}"

    def test_evaluation_report_contains_model_comparison(self) -> None:
        rep_path = project_root / "ml" / "artifacts" / "evaluation_report.json"
        rep = json.loads(rep_path.read_text())

        assert "model_comparison" in rep
        assert "logistic_regression" in rep["model_comparison"]
        assert "random_forest" in rep["model_comparison"]
        assert "xgboost" in rep["model_comparison"]
        assert "global_feature_importance" in rep
