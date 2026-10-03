from pathlib import Path
import sys

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from xgboost import XGBClassifier

# --------------------------------------------------
# Project root
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(BASE_DIR))


# --------------------------------------------------
# Imports from our own module
# --------------------------------------------------

from features.url_features import extract_url_features
from explain.shap_explainer import (
    generate_human_explanations,
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

MODEL_PATH = BASE_DIR / "models" / "xgb_model.json"

MODEL_VERSION = "xgboost-url-v1"

FEATURE_COLUMNS = [
    "url_length",
    "domain_length",
    "dot_count",
    "subdomain_count",
    "digit_count",
    "letter_count",
    "hyphen_count",
    "at_count",
    "special_char_count",
    "query_param_count",
    "fragment_count",
    "has_ip",
    "has_punycode",
    "is_shortened",
    "suspicious_tld",
]


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="PHISHGUARD-X URL Analysis API",
    version="1.0.0",
)


# --------------------------------------------------
# Request model
# --------------------------------------------------

class URLRequest(BaseModel):
    url: str


# --------------------------------------------------
# Load model once when server starts
# --------------------------------------------------

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"XGBoost model not found: {MODEL_PATH}"
    )

model = XGBClassifier()
model.load_model(MODEL_PATH)


# --------------------------------------------------
# URL analysis
# --------------------------------------------------

def analyze_url(url: str) -> dict:

    # Extract features
    features = extract_url_features(url)

    # Prepare model input
    X = pd.DataFrame(
        [[features[column] for column in FEATURE_COLUMNS]],
        columns=FEATURE_COLUMNS,
    )

    # Prediction probability
    phishing_probability = float(
        model.predict_proba(X)[0][1]
    )

    prediction = (
        "phishing"
        if phishing_probability >= 0.5
        else "legitimate"
    )

    risk_score = round(
        phishing_probability * 100
    )

    # SHAP explanation
    # IMPORTANT: SHAP's TreeExplainer uses joblib which forks OS processes.
    # On macOS, forking after torch has been imported causes a kernel-level
    # deadlock that no timeout mechanism can interrupt.
    # Solution: skip SHAP when torch is already loaded (integrated pipeline).
    # SHAP still works normally when the URL service runs standalone.
    explanations = []
    if "torch" not in sys.modules:
        try:
            from explain.shap_explainer import get_shap_explanation
            shap_df = get_shap_explanation(url)
            explanations = generate_human_explanations(shap_df)
        except Exception:
            explanations = []

    return {
        "url": url,
        "prediction": prediction,
        "probability": round(
            phishing_probability,
            4
        ),
        "risk_score": risk_score,
        "model_version": MODEL_VERSION,
        "features": features,
        "explanation": explanations,
    }


# --------------------------------------------------
# API endpoint
# --------------------------------------------------

@app.post("/analyze-url")
def analyze_url_endpoint(request: URLRequest):

    try:

        return analyze_url(request.url)

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"URL analysis failed: {error}"
        )


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "model": MODEL_VERSION
    }