"""
RecoverAI — SHAP Explainability Engine
=======================================
Generates interpretable model explanations and local feature contributions
for revenue recovery predictions without exposing raw technical internals.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import shap

logger = logging.getLogger(__name__)


FEATURE_NAME_MAPPINGS: Dict[str, str] = {
    "amount": "Payment amount",
    "customer_lifetime_value": "Customer lifetime value",
    "retry_count": "Previous retry count",
    "previous_successful_payments": "Past successful payments",
    "previous_failed_payments": "Past failed payments",
    "subscription_age_days": "Customer account age",
    "historical_recovery_rate": "Customer historical recovery rate",
    "days_since_last_payment": "Days since last transaction",
    "payment_frequency": "Payment frequency",
    "prev_success_ratio": "Customer payment reliability ratio",
    "amount_to_avg_ratio": "Transaction amount vs customer average",
    "failure_temporary": "Temporary nature of failure",
    "is_subscription": "Subscription billing relationship",
}


def humanize_feature_explanation(
    feature_name: str,
    shap_value: float,
    raw_value: Any = None,
) -> Dict[str, Any]:
    """
    Translates raw feature name and SHAP value into an intuitive business explanation.
    """
    direction = "+" if shap_value > 0 else "-"
    strength = "Strong " if abs(shap_value) > 0.25 else "Moderate " if abs(shap_value) > 0.1 else "Slight "

    # Categorical one-hot features (e.g. failure_reason_temporary_gateway_failure)
    if "failure_reason_" in feature_name:
        reason = feature_name.replace("failure_reason_", "").replace("_", " ")
        if shap_value > 0:
            desc = f"{strength}positive impact: Recoverable issue type ({reason})"
        else:
            desc = f"{strength}negative impact: Harder-to-recover failure type ({reason})"
        return {"factor": f"{direction} {desc}", "feature": "Failure Reason", "impact": direction, "shap": round(float(shap_value), 4)}

    if "payment_method_" in feature_name:
        method = feature_name.replace("payment_method_", "").replace("_", " ").title()
        if shap_value > 0:
            desc = f"{strength}positive impact: Reliable payment rail ({method})"
        else:
            desc = f"{strength}negative impact: Channel friction ({method})"
        return {"factor": f"{direction} {desc}", "feature": "Payment Method", "impact": direction, "shap": round(float(shap_value), 4)}

    if "customer_region_" in feature_name:
        reg = feature_name.replace("customer_region_", "").upper()
        desc = f"Regional recovery dynamics ({reg})"
        return {"factor": f"{direction} {strength}{desc}", "feature": "Customer Region", "impact": direction, "shap": round(float(shap_value), 4)}

    # Numeric & Engineered features
    clean_name = FEATURE_NAME_MAPPINGS.get(feature_name, feature_name.replace("_", " ").title())
    
    if feature_name == "amount":
        if shap_value > 0:
            desc = f"{strength}favorable: Manageable payment size"
        else:
            desc = f"{strength}drag: High transaction amount reduces instant recovery likelihood"
    elif feature_name in ["customer_lifetime_value", "is_high_clv"]:
        if shap_value > 0:
            desc = f"{strength}boost: High-value account with strong platform commitment"
        else:
            desc = f"{strength}drag: Lower account lifetime value"
    elif feature_name == "retry_count":
        if shap_value > 0:
            desc = f"{strength}boost: Fresh failure (low prior retry fatigue)"
        else:
            desc = f"{strength}drag: Multiple prior retries already attempted"
    elif feature_name in ["previous_successful_payments", "prev_success_ratio"]:
        if shap_value > 0:
            desc = f"{strength}boost: Solid payment track record"
        else:
            desc = f"{strength}drag: Inconsistent payment history"
    elif feature_name == "failure_temporary":
        if shap_value > 0:
            desc = f"{strength}boost: Temporary transient gateway/network issue"
        else:
            desc = f"{strength}drag: Non-temporary failure condition"
    elif feature_name == "historical_recovery_rate":
        if shap_value > 0:
            desc = f"{strength}boost: Customer has previously resolved failed payments"
        else:
            desc = f"{strength}drag: Low past recovery track record"
    else:
        effect = "increases" if shap_value > 0 else "decreases"
        desc = f"{clean_name} {effect} recovery probability"

    return {
        "factor": f"{direction} {desc}",
        "feature": clean_name,
        "impact": direction,
        "shap": round(float(shap_value), 4),
    }


class RecoveryExplainer:
    """
    SHAP-based model explainer for RecoverAI recovery predictions.
    """

    def __init__(self, model: Any, feature_names: List[str], background_data: Optional[np.ndarray] = None) -> None:
        self.model = model
        self.feature_names = feature_names
        self.background_data = background_data
        self.explainer: Optional[shap.Explainer] = None
        self._init_explainer()

    def _init_explainer(self) -> None:
        try:
            # Tree explainer for XGBoost / Random Forest
            self.explainer = shap.TreeExplainer(self.model)
        except Exception:
            try:
                # Linear explainer or general explainer with background data
                if self.background_data is not None:
                    self.explainer = shap.Explainer(self.model, self.background_data)
                else:
                    self.explainer = shap.Explainer(self.model)
            except Exception as e:
                logger.warning(f"Could not initialize SHAP Explainer: {e}")
                self.explainer = None

    def explain_instance(
        self,
        X_sample: np.ndarray,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Computes local SHAP values for a single transformed sample
        and returns the top positive and negative human-readable factors.
        """
        if self.explainer is None:
            return []

        if len(X_sample.shape) == 1:
            X_sample = X_sample.reshape(1, -1)

        try:
            shap_values = self.explainer.shap_values(X_sample)
            
            # Handle binary classification output formats
            if isinstance(shap_values, list) and len(shap_values) == 2:
                # Class 1 SHAP values
                vals = shap_values[1][0]
            elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
                vals = shap_values[0, :, 1]
            elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 2:
                vals = shap_values[0]
            else:
                vals = np.array(shap_values).flatten()

            # Rank by absolute impact
            ranked_indices = np.argsort(np.abs(vals))[::-1]
            
            explanations: List[Dict[str, Any]] = []
            seen_features: set = set()

            for idx in ranked_indices:
                if idx >= len(self.feature_names):
                    continue
                feat_name = self.feature_names[idx]
                shap_val = vals[idx]

                if abs(shap_val) < 0.005:
                    continue

                humanized = humanize_feature_explanation(feat_name, shap_val)
                # Avoid duplicate broad feature categories in top_k
                if humanized["feature"] not in seen_features:
                    seen_features.add(humanized["feature"])
                    explanations.append(humanized)

                if len(explanations) >= top_k:
                    break

            return explanations
        except Exception as e:
            logger.error(f"Error computing SHAP values: {e}")
            return []

    def get_global_feature_importance(
        self,
        X_sample: np.ndarray,
        top_k: int = 15,
    ) -> List[Dict[str, Any]]:
        """
        Computes mean absolute SHAP value across a batch of samples.
        """
        if self.explainer is None:
            return []

        try:
            shap_values = self.explainer.shap_values(X_sample)
            if isinstance(shap_values, list) and len(shap_values) == 2:
                vals = shap_values[1]
            elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
                vals = shap_values[:, :, 1]
            else:
                vals = shap_values

            mean_abs_shap = np.mean(np.abs(vals), axis=0)
            ranked_indices = np.argsort(mean_abs_shap)[::-1][:top_k]

            importance = []
            for idx in ranked_indices:
                if idx < len(self.feature_names):
                    importance.append({
                        "feature": self.feature_names[idx],
                        "mean_abs_shap": round(float(mean_abs_shap[idx]), 4),
                    })
            return importance
        except Exception as e:
            logger.error(f"Error calculating global feature importance: {e}")
            return []
