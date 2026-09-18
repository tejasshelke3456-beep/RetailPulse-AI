"""
RetailPulse AI - Reusable Churn Prediction Module
Loads saved model and provides predict() for single-customer inference.
"""
import os
import warnings
import joblib
import numpy as np
import pandas as pd

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "churn_model.pkl")

_artefact = None  # module-level cache


def _load():
    global _artefact
    if _artefact is None:
        _artefact = joblib.load(MODEL_PATH)
    return _artefact


def predict(features: dict) -> dict:
    """
    Predict churn for one customer.

    Parameters
    ----------
    features : dict with keys:
        historical_recency, historical_frequency, historical_monetary,
        total_items, average_order_value, average_discount,
        age, region (str), gender (str)

    Returns
    -------
    dict with: churn_probability, prediction (0/1), risk_level
    """
    art = _load()
    model     = art["model"]
    le_region = art["le_region"]
    le_gender = art["le_gender"]
    feat_cols = art["feature_cols"]

    # Safe label encoding for unseen categories
    def safe_encode(le, value):
        try:
            return le.transform([value])[0]
        except ValueError:
            return 0

    region_enc = safe_encode(le_region, features.get("region", "North"))
    gender_enc = safe_encode(le_gender, features.get("gender", "Male"))

    row = [
        float(features.get("historical_recency",   90)),
        float(features.get("historical_frequency",  5)),
        float(features.get("historical_monetary",  500)),
        float(features.get("total_items",           10)),
        float(features.get("average_order_value",  100)),
        float(features.get("average_discount",     0.1)),
        float(features.get("age",                   35)),
        float(region_enc),
        float(gender_enc),
    ]

    X_df = pd.DataFrame([row], columns=feat_cols)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        prob = float(model.predict_proba(X_df)[0][1])
        pred = int(model.predict(X_df)[0])

    if prob >= 0.70:
        risk_level = "High"
    elif prob >= 0.40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "churn_probability": round(prob, 4),
        "prediction":        pred,
        "risk_level":        risk_level,
    }


def model_info() -> dict:
    art = _load()
    return {
        "model_name": art.get("model_name", "Random Forest"),
        "f1_score":   round(art.get("f1_score", 0), 4),
        "roc_auc":    round(art.get("roc_auc",   0), 4),
        "lr_f1":      round(art.get("lr_f1",     0), 4),
        "lr_auc":     round(art.get("lr_auc",    0), 4),
    }
