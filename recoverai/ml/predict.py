"""
RecoverAI — Inference & Prediction Interface
=============================================
Provides clean, high-performance prediction functions for estimating
payment recovery probabilities and generating SHAP explanation factors.

Safety:
- Strictly rejects any inputs containing leakage columns.
- Validates field constraints and handles missing values robustly.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd

from ml.explainability import RecoveryExplainer
from ml.preprocessing import (
    ALL_INPUT_FEATURES,
    LEAKAGE_COLUMNS,
    RecoveryDataPreprocessor,
    validate_prediction_input,
)

logger = logging.getLogger(__name__)

# Default artifact paths
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


class RecoveryPredictor:
    """
    Production-ready inference engine for RecoverAI.
    Loads trained models, preprocessor, and explainer.
    """

    def __init__(self, artifacts_dir: Optional[Path] = None) -> None:
        self.artifacts_dir = artifacts_dir or ARTIFACTS_DIR
        self._model: Optional[Any] = None
        self._preprocessor: Optional[RecoveryDataPreprocessor] = None
        self._explainer: Optional[RecoveryExplainer] = None
        self._metadata: Optional[Dict[str, Any]] = None
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        model_path = self.artifacts_dir / "model.joblib"
        prep_path = self.artifacts_dir / "preprocessor.joblib"
        meta_path = self.artifacts_dir / "model_metadata.json"
        shap_path = self.artifacts_dir / "shap_explainer.joblib"

        if not model_path.exists() or not prep_path.exists():
            raise FileNotFoundError(
                f"Model artifacts not found in {self.artifacts_dir}. Please run 'python ml/train.py' first."
            )

        self._model = joblib.load(model_path)
        self._preprocessor = joblib.load(prep_path)
        
        if shap_path.exists():
            try:
                self._explainer = joblib.load(shap_path)
            except Exception as e:
                logger.warning(f"Could not load SHAP explainer: {e}")
                self._explainer = None

        if meta_path.exists():
            self._metadata = json.loads(meta_path.read_text())
        else:
            self._metadata = {"model_name": "RecoverAI-Model-v1"}

    @property
    def model_version(self) -> str:
        return self._metadata.get("model_name", "recoverai-v1") if self._metadata else "recoverai-v1"

    def predict_one(
        self,
        payment_data: Dict[str, Any],
        include_explanation: bool = True,
    ) -> Dict[str, Any]:
        """
        Predicts recovery probability for a single payment record.
        """
        df = pd.DataFrame([payment_data])
        results = self.predict_batch(df, include_explanation=include_explanation)
        return results[0]

    def predict_batch(
        self,
        df: pd.DataFrame,
        include_explanation: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Predicts recovery probabilities for a batch of payment records.
        """
        # Strict leakage check
        validate_prediction_input(df, allow_target=False)

        # Extract payment IDs if present
        payment_ids = (
            df["payment_id"].tolist()
            if "payment_id" in df.columns
            else [f"P_INF_{i:04d}" for i in range(len(df))]
        )

        # Preprocess features
        X_trans = self._preprocessor.transform(df)

        # Generate probabilities
        probabilities = self._model.predict_proba(X_trans)[:, 1]
        binary_predictions = (probabilities >= 0.50).astype(int)

        output: List[Dict[str, Any]] = []

        for i in range(len(df)):
            prob = float(probabilities[i])
            pred = int(binary_predictions[i])
            pid = str(payment_ids[i])

            explanation_factors: List[Dict[str, Any]] = []
            if include_explanation and self._explainer is not None:
                explanation_factors = self._explainer.explain_instance(X_trans[i], top_k=5)

            record = {
                "payment_id": pid,
                "recovery_probability": round(prob, 4),
                "model_version": self.model_version,
                "prediction": pred,
                "confidence": "HIGH" if prob > 0.75 or prob < 0.25 else "MODERATE",
            }
            if include_explanation:
                record["factors"] = explanation_factors

            output.append(record)

        return output


# Global Singleton Predictor Instance
_GLOBAL_PREDICTOR: Optional[RecoveryPredictor] = None


def get_predictor() -> RecoveryPredictor:
    """Returns the singleton predictor instance."""
    global _GLOBAL_PREDICTOR
    if _GLOBAL_PREDICTOR is None:
        _GLOBAL_PREDICTOR = RecoveryPredictor()
    return _GLOBAL_PREDICTOR


def predict_recovery_probability(
    payment_data: Union[Dict[str, Any], pd.DataFrame, List[Dict[str, Any]]],
    include_explanation: bool = True,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Main entry point for recovery probability predictions.
    
    Args:
        payment_data: Single payment dictionary, list of dictionaries, or pandas DataFrame.
        include_explanation: Whether to compute SHAP factor contributions.
        
    Returns:
        Structured prediction dictionary or list of dictionaries.
    """
    predictor = get_predictor()

    if isinstance(payment_data, dict):
        return predictor.predict_one(payment_data, include_explanation=include_explanation)
    elif isinstance(payment_data, pd.DataFrame):
        return predictor.predict_batch(payment_data, include_explanation=include_explanation)
    elif isinstance(payment_data, list):
        df = pd.DataFrame(payment_data)
        return predictor.predict_batch(df, include_explanation=include_explanation)
    else:
        raise TypeError(f"Unsupported input type for payment_data: {type(payment_data)}")


def predict_payment_recovery(payment_id: str, include_explanation: bool = True) -> Dict[str, Any]:
    """
    Convenience function to fetch payment features by ID and compute recovery prediction.
    """
    from agent.tools import get_payment_details
    payment_dict = get_payment_details(payment_id)
    res = predict_recovery_probability(payment_dict, include_explanation=include_explanation)
    if isinstance(res, list):
        return res[0]
    return res

