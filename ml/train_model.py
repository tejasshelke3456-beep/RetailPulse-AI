"""
RetailPulse AI - ML: Train Churn Prediction Models
Trains Logistic Regression and Random Forest on historical customer features.
No target leakage - uses only features from <= 2025-09-01.
Saves the best model (Random Forest) to ml/churn_model.pkl
"""
import os
import sys
import sqlite3
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report, roc_auc_score,
    f1_score, confusion_matrix
)

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH    = os.path.join(BASE_DIR, "data", "ecommerce.db")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "churn_model.pkl")

FEATURE_COLS = [
    "historical_recency",
    "historical_frequency",
    "historical_monetary",
    "total_items",
    "average_order_value",
    "average_discount",
    "age",
    "region_encoded",
    "gender_encoded",
]
TARGET_COL = "is_churned"


def load_features():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT customer_id, historical_recency, historical_frequency,
               historical_monetary, total_items, average_order_value,
               average_discount, age, region, gender, is_churned
        FROM customer_features
        WHERE historical_frequency > 0
        """,
        conn,
    )
    conn.close()
    return df


def encode_features(df):
    le_region = LabelEncoder()
    le_gender = LabelEncoder()
    df = df.copy()
    df["region_encoded"] = le_region.fit_transform(df["region"].fillna("Unknown"))
    df["gender_encoded"] = le_gender.fit_transform(df["gender"].fillna("Unknown"))
    return df, le_region, le_gender


def train():
    print("-- Loading features from DB ...")
    df = load_features()
    print(f"   Rows: {len(df):,}  |  Churn rate: {df['is_churned'].mean()*100:.2f}%")

    df, le_region, le_gender = encode_features(df)

    X = df[FEATURE_COLS].fillna(0)
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline

    results = {}

    # -- Logistic Regression (with scaling) ----------------------------------
    print("\n-- Training Logistic Regression ...")
    lr_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=3000, random_state=42, class_weight="balanced", C=1.0))
    ])
    lr_pipe.fit(X_train, y_train)
    y_pred_lr  = lr_pipe.predict(X_test)
    y_prob_lr  = lr_pipe.predict_proba(X_test)[:, 1]
    f1_lr      = f1_score(y_test, y_pred_lr, average="weighted")
    auc_lr     = roc_auc_score(y_test, y_prob_lr)
    results["Logistic Regression"] = {"model": lr_pipe, "f1": f1_lr, "auc": auc_lr}
    print(f"   F1={f1_lr:.4f}  ROC-AUC={auc_lr:.4f}")
    print(classification_report(y_test, y_pred_lr))

    # -- Random Forest --------------------------------------------------------
    print("\n-- Training Random Forest ...")
    rf = RandomForestClassifier(
        n_estimators=300, max_depth=12, min_samples_leaf=3,
        random_state=42, class_weight="balanced", n_jobs=-1
    )
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    y_prob_rf = rf.predict_proba(X_test)[:, 1]
    f1_rf     = f1_score(y_test, y_pred_rf, average="weighted")
    auc_rf    = roc_auc_score(y_test, y_prob_rf)
    results["Random Forest"] = {"model": rf, "f1": f1_rf, "auc": auc_rf}
    print(f"   F1={f1_rf:.4f}  ROC-AUC={auc_rf:.4f}")
    print(classification_report(y_test, y_pred_rf))

    # -- Summary --------------------------------------------------------------
    print("\n== Model Comparison ==")
    for name, r in results.items():
        print(f"  {name:<25} F1={r['f1']:.4f}  ROC-AUC={r['auc']:.4f}")

    # -- Save best model (Random Forest) --------------------------------------
    best_model = rf
    artefact = {
        "model":          best_model,
        "feature_cols":   FEATURE_COLS,
        "le_region":      le_region,
        "le_gender":      le_gender,
        "model_name":     "Random Forest",
        "f1_score":       f1_rf,
        "roc_auc":        auc_rf,
        "lr_f1":          f1_lr,
        "lr_auc":         auc_lr,
    }
    joblib.dump(artefact, MODEL_PATH)
    print(f"\n[OK] Model saved -> {MODEL_PATH}")
    return artefact


if __name__ == "__main__":
    train()
