"""
RecoverAI — ML Prediction Endpoints (v1)
========================================
Exposes calibrated machine learning inference and model status inspection.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from backend.config import settings
from backend.schemas.ml import MLFactor, MLPredictResponse, MLStatusResponse
from ml.predict import predict_payment_recovery

router = APIRouter(prefix="/ml", tags=["Machine Learning & Explainability"])


@router.post("/predict/{payment_id}", response_model=MLPredictResponse, summary="Predict Payment Recovery Probability")
def predict_recovery(payment_id: str) -> MLPredictResponse:
    """
    Executes leakage-safe ML inference and returns calibrated recovery probability with SHAP factors.
    """
    try:
        pred_res = predict_payment_recovery(payment_id=payment_id)
        factors = [
            MLFactor(
                feature=f.get("feature", "unknown"),
                impact=f.get("impact", "positive"),
                importance=float(f.get("importance", 0.0)),
                description=f.get("description", ""),
            )
            for f in pred_res.get("factors", [])
        ]
        return MLPredictResponse(
            payment_id=payment_id,
            recovery_probability=float(pred_res["recovery_probability"]),
            prediction=int(pred_res["prediction"]),
            model_version=pred_res.get("model_version", "1.0.0"),
            calibrated=pred_res.get("calibrated", True),
            factors=factors,
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference error: {str(exc)}")


@router.get("/status", response_model=MLStatusResponse, summary="Get ML Model Status")
def get_ml_status() -> MLStatusResponse:
    """
    Returns the production ML model status, feature count, and artifact availability.
    """
    model_file = settings.project_root / settings.model_path
    prep_file = settings.project_root / settings.preprocessor_path
    shap_file = settings.project_root / settings.shap_path
    meta_file = settings.project_root / "ml/artifacts/model_metadata.json"
    feat_file = settings.project_root / "ml/artifacts/feature_columns.json"

    model_loaded = model_file.exists() and prep_file.exists()

    features = []
    model_version = "1.0.0"
    calibrated = True

    if feat_file.exists():
        try:
            with open(feat_file, "r", encoding="utf-8") as f:
                feat_data = json.load(f)
                features = feat_data.get("transformed_features", feat_data.get("raw_features", []))
        except Exception:
            pass

    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
                model_version = meta.get("model_name", "1.0.0")
                calibrated = meta.get("is_calibrated", True)
        except Exception:
            pass

    return MLStatusResponse(
        model_loaded=model_loaded,
        model_version=model_version,
        calibrated=calibrated,
        feature_count=len(features),
        features=features,
        artifact_paths={
            "model": str(model_file),
            "preprocessor": str(prep_file),
            "shap_explainer": str(shap_file),
        },
    )
