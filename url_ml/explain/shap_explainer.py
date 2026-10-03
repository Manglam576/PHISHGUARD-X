from pathlib import Path
import sys

import pandas as pd
import shap
from xgboost import XGBClassifier


# --------------------------------------------------
# Project root
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(BASE_DIR))


# --------------------------------------------------
# Model
# --------------------------------------------------

MODEL_PATH = BASE_DIR / "models" / "xgb_model.json"


# --------------------------------------------------
# Features used by XGBoost
# --------------------------------------------------

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


def get_shap_explanation(url: str):
    """
    Generate SHAP feature contributions for one URL.
    """

    # Import our existing feature extractor
    from features.url_features import (
        extract_url_features
    )

    # ----------------------------------------------
    # Extract URL features
    # ----------------------------------------------

    features = extract_url_features(url)

    X = pd.DataFrame(
        [[features[column] for column in FEATURE_COLUMNS]],
        columns=FEATURE_COLUMNS
    )

    # ----------------------------------------------
    # Load model
    # ----------------------------------------------

    model = load_model()

    # ----------------------------------------------
    # Create SHAP explainer
    # ----------------------------------------------

    explainer = shap.TreeExplainer(model)

    shap_values = explainer.shap_values(X)

    # SHAP returns an array for binary classification
    contributions = shap_values[0]

    # ----------------------------------------------
    # Combine feature names + SHAP values
    # ----------------------------------------------

    explanation_df = pd.DataFrame({
        "feature": FEATURE_COLUMNS,
        "value": X.iloc[0].values,
        "shap_value": contributions
    })

    # Most influential features first
    explanation_df["abs_shap"] = (
        explanation_df["shap_value"].abs()
    )

    explanation_df = explanation_df.sort_values(
        by="abs_shap",
        ascending=False
    )

    return explanation_df
def generate_human_explanations(
    explanation_df: pd.DataFrame,
    top_n: int = 5
) -> list[str]:
    """
    Convert SHAP feature contributions into
    human-readable explanations.
    """

    explanations = []

    # Only consider features that push
    # the prediction toward phishing.
    positive = explanation_df[
        explanation_df["shap_value"] > 0
    ].head(top_n)

    for _, row in positive.iterrows():

        feature = row["feature"]
        value = row["value"]

        if feature == "url_length":
            explanations.append(
                f"Unusually long URL (length: {int(value)})"
            )

        elif feature == "domain_length":
            explanations.append(
                f"Long domain name (length: {int(value)})"
            )

        elif feature == "digit_count":
            explanations.append(
                f"Contains {int(value)} digit(s)"
            )

        elif feature == "subdomain_count":
            explanations.append(
                f"Contains {int(value)} subdomain(s)"
            )

        elif feature == "dot_count":
            explanations.append(
                f"Contains {int(value)} dot(s)"
            )

        elif feature == "hyphen_count":
            explanations.append(
                f"Contains {int(value)} hyphen(s)"
            )

        elif feature == "suspicious_tld":
            explanations.append(
                "Uses a suspicious TLD"
            )

        elif feature == "has_ip":
            explanations.append(
                "Uses an IP address instead of a domain name"
            )

        elif feature == "has_punycode":
            explanations.append(
                "Uses punycode in the domain"
            )

        elif feature == "is_shortened":
            explanations.append(
                "Uses a known URL-shortening service"
            )

        elif feature == "at_count":
            explanations.append(
                "Contains an @ symbol"
            )

        elif feature == "special_char_count":
            explanations.append(
                f"Contains {int(value)} unusual special character(s)"
            )

        elif feature == "query_param_count":
            explanations.append(
                f"Contains {int(value)} query parameter(s)"
            )

    return explanations


if __name__ == "__main__":

    test_url = (
        "https://secure-login.example.com/"
        "account?id=123"
    )

    print("\nURL:")
    print(test_url)

    explanation = get_shap_explanation(
        test_url
    )

    print("\n==========================================")
    print("TOP SHAP CONTRIBUTIONS")
    print("==========================================")

    print(
        explanation.head(10).to_string(
            index=False
        )
    )

    human_explanations = generate_human_explanations(
        explanation
    )

    print("\n==========================================")
    print("HUMAN-READABLE EXPLANATION")
    print("==========================================")

    for reason in human_explanations:
        print(f"- {reason}")