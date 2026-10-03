from pathlib import Path
import sys

import pandas as pd
from xgboost import XGBClassifier


# Add the project root (url_ml) to Python's import path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from features.url_features import extract_url_features


BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "models" / "xgb_model.json"


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


def load_model():
    """Load the trained XGBoost model."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )

    model = XGBClassifier()
    model.load_model(MODEL_PATH)

    return model


def predict_url(url: str) -> dict:
    """
    Analyze one URL and return the URL-level prediction.
    """

    # Extract features from URL
    features = extract_url_features(url)

    # Convert dictionary to DataFrame
    X = pd.DataFrame(
        [[features[column] for column in FEATURE_COLUMNS]],
        columns=FEATURE_COLUMNS
    )

    # Load trained model
    model = load_model()

    # Probability of class 1 = phishing
    phishing_probability = float(
        model.predict_proba(X)[0][1]
    )

    # Model prediction
    prediction = int(
        phishing_probability >= 0.5
    )

    if prediction == 1:
        label = "phishing"
    else:
        label = "legitimate"

    # Convert probability to 0-100 risk score
    risk_score = round(
        phishing_probability * 100
    )

    return {
        "url": url,
        "prediction": label,
        "probability": round(
            phishing_probability,
            4
        ),
        "risk_score": risk_score,
        "features": features,
        "model_version": "xgboost-url-v1"
    }


if __name__ == "__main__":

    test_urls = [
        "https://www.google.com",
        "https://secure-login.example.com/account?id=123",
        "http://192.168.1.10/login",
    ]

    for url in test_urls:

        print("\n" + "=" * 60)
        print(f"URL: {url}")

        result = predict_url(url)

        print(
            f"Prediction: {result['prediction']}"
        )

        print(
            f"Probability: {result['probability']}"
        )

        print(
            f"Risk Score: {result['risk_score']}"
        )