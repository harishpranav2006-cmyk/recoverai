"""
RecoverAI — ML Preprocessing Pipeline
======================================
Defines feature extraction, strict leakage validation, categorical encoding,
and numeric transformations for recovery probability prediction.

Safety:
- Rejects any fields in LEAKAGE_COLUMNS or post-outcome values.
- Strictly accepts only prediction-time features.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

logger = logging.getLogger(__name__)


def _convert_bools_to_float(df: Any) -> np.ndarray:
    """Helper to convert boolean dataframe/array to clean float64 matrix."""
    return np.nan_to_num(np.asarray(df, dtype=float), nan=0.0)

# Canonical Prediction-Time Feature Definitions
CATEGORICAL_FEATURES: List[str] = [
    "payment_method",
    "payment_method_type",
    "device_type",
    "subscription_type",
    "failure_reason",
    "failure_category",
    "payment_gateway_status",
    "customer_region",
]

NUMERICAL_FEATURES: List[str] = [
    "amount",
    "subscription_age_days",
    "customer_age",
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
]

BOOLEAN_FEATURES: List[str] = [
    "is_subscription",
    "failure_temporary",
]

ALL_INPUT_FEATURES: List[str] = CATEGORICAL_FEATURES + NUMERICAL_FEATURES + BOOLEAN_FEATURES

LEAKAGE_COLUMNS: List[str] = [
    "simulated_recovery_probability",
    "actual_recovery_outcome",
    "recovered_after_failure",
    "recovery_time_hours",
    "recovered_amount",
]

TARGET_COLUMN: str = "actual_recovery_outcome"


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Constructs domain-specific engineered features from raw prediction-time inputs.
    Never uses future or post-outcome fields.
    """

    def __init__(self) -> None:
        self.engineered_feature_names_: List[str] = []

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "FeatureEngineer":
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_out = X.copy()

        # 1. Total payment history and success ratio
        prev_success = X_out["previous_successful_payments"] if "previous_successful_payments" in X_out.columns else pd.Series(0, index=X_out.index)
        prev_failed = X_out["previous_failed_payments"] if "previous_failed_payments" in X_out.columns else pd.Series(0, index=X_out.index)
        total_prev = prev_success + prev_failed
        X_out["prev_success_ratio"] = np.where(
            total_prev > 0,
            prev_success / np.maximum(total_prev, 1),
            0.5  # Neutral default for new customers
        )

        # 2. Amount to Average Transaction Value Ratio
        avg_txn = X_out["average_transaction_value"] if "average_transaction_value" in X_out.columns else pd.Series(0.0, index=X_out.index)
        amt = X_out["amount"] if "amount" in X_out.columns else pd.Series(0.0, index=X_out.index)
        X_out["amount_to_avg_ratio"] = np.where(
            avg_txn > 0,
            amt / np.maximum(avg_txn, 1.0),
            1.0
        )

        # 3. High value customer indicator
        clv = X_out["customer_lifetime_value"] if "customer_lifetime_value" in X_out.columns else pd.Series(0.0, index=X_out.index)
        X_out["is_high_clv"] = (clv > 5000.0).astype(float)

        # 4. First failure indicator
        X_out["is_first_failure"] = (prev_failed == 0).astype(float)

        # 5. Extract temporal features if timestamp is provided
        if "timestamp" in X_out.columns:
            ts = pd.to_datetime(X_out["timestamp"], errors="coerce")
            X_out["hour_of_day"] = ts.dt.hour.fillna(12).astype(float)
            X_out["day_of_week"] = ts.dt.dayofweek.fillna(2).astype(float)
            X_out["is_weekend"] = (X_out["day_of_week"] >= 5).astype(float)
        else:
            X_out["hour_of_day"] = 12.0
            X_out["day_of_week"] = 2.0
            X_out["is_weekend"] = 0.0

        return X_out


def validate_prediction_input(df: pd.DataFrame, allow_target: bool = False) -> None:
    """
    Strictly validates input dataframe against data leakage.
    Raises ValueError if any forbidden post-outcome columns are present.
    """
    cols = set(df.columns)
    detected_leakage = cols.intersection(set(LEAKAGE_COLUMNS))
    
    if not allow_target and TARGET_COLUMN in detected_leakage:
        raise ValueError(
            f"Data leakage detected! Target column '{TARGET_COLUMN}' found in inference input features."
        )
    
    non_target_leakage = detected_leakage - ({TARGET_COLUMN} if allow_target else set())
    if non_target_leakage:
        raise ValueError(
            f"Data leakage detected! Forbidden post-outcome columns found in input: {sorted(list(non_target_leakage))}. "
            "These fields must never be provided to the model."
        )


def build_preprocessor() -> Pipeline:
    """
    Builds the full Scikit-Learn preprocessing pipeline.
    Combines FeatureEngineering, OneHotEncoding for categoricals, and StandardScaler for numerics.
    """
    engineered_numerics = [
        "prev_success_ratio",
        "amount_to_avg_ratio",
        "hour_of_day",
        "day_of_week",
    ]
    
    engineered_booleans = [
        "is_high_clv",
        "is_first_failure",
        "is_weekend",
    ]

    all_numeric_cols = NUMERICAL_FEATURES + engineered_numerics
    all_bool_cols = BOOLEAN_FEATURES + engineered_booleans

    column_transformer = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.float64),
                CATEGORICAL_FEATURES,
            ),
            (
                "num",
                Pipeline([
                    ("scaler", StandardScaler()),
                ]),
                all_numeric_cols,
            ),
            (
                "bool",
                Pipeline([
                    ("bool_to_float", FunctionTransformer(_convert_bools_to_float)),
                ]),
                all_bool_cols,
            ),
        ],
        remainder="drop",
    )

    pipeline = Pipeline([
        ("feature_engineer", FeatureEngineer()),
        ("column_transformer", column_transformer),
    ])

    return pipeline


class RecoveryDataPreprocessor:
    """
    High-level wrapper around the preprocessing pipeline with column name tracking
    and input validation.
    """

    def __init__(self) -> None:
        self.pipeline: Pipeline = build_preprocessor()
        self.feature_names_: List[str] = []
        self.is_fitted_: bool = False

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "RecoveryDataPreprocessor":
        validate_prediction_input(X, allow_target=True)
        self.pipeline.fit(X, y)
        self.is_fitted_ = True
        self._extract_feature_names()
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted_:
            raise RuntimeError("RecoveryDataPreprocessor must be fitted before transforming data.")
        validate_prediction_input(X, allow_target=True)
        res = self.pipeline.transform(X)
        return np.asarray(res, dtype=np.float64)

    def fit_transform(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> np.ndarray:
        return self.fit(X, y).transform(X)

    def _extract_feature_names(self) -> None:
        """Extract output feature names from ColumnTransformer."""
        col_trans = self.pipeline.named_steps["column_transformer"]
        cat_encoder = col_trans.named_transformers_["cat"]
        
        cat_feature_names = list(cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES))
        num_feature_names = NUMERICAL_FEATURES + [
            "prev_success_ratio", "amount_to_avg_ratio", "hour_of_day", "day_of_week"
        ]
        bool_feature_names = BOOLEAN_FEATURES + [
            "is_high_clv", "is_first_failure", "is_weekend"
        ]
        
        self.feature_names_ = cat_feature_names + num_feature_names + bool_feature_names

    def get_feature_names(self) -> List[str]:
        return self.feature_names_
