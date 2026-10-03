from pathlib import Path
import json

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)

from xgboost import XGBClassifier


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "processed" / "url_features.csv"
MODEL_DIR = BASE_DIR / "models"

MODEL_PATH = MODEL_DIR / "xgb_model.json"
METRICS_PATH = MODEL_DIR / "training_metrics.json"


# --------------------------------------------------
# Configuration
# --------------------------------------------------

TEST_SIZE = 0.20
RANDOM_STATE = 42


def main():

    # --------------------------------------------------
    # 1. Load dataset
    # --------------------------------------------------

    print("Loading processed dataset...")

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at:\n{DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    print(f"Dataset shape: {df.shape}")

    # --------------------------------------------------
    # 2. Separate X and y
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

    X = df[FEATURE_COLUMNS]
    
    y = df["label"]

    print(f"\nNumber of features: {X.shape[1]}")
    print(f"Number of samples: {X.shape[0]}")

    print("\nLabel distribution:")
    print(y.value_counts())

    # --------------------------------------------------
    # 3. Train / test split
    # --------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print("\nData split:")
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples:  {len(X_test)}")

    # --------------------------------------------------
    # 4. Create XGBoost model
    # --------------------------------------------------

    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    # --------------------------------------------------
    # 5. Train
    # --------------------------------------------------

    print("\nTraining XGBoost...")

    model.fit(
        X_train,
        y_train
    )

    print("Training complete.")

    # --------------------------------------------------
    # 6. Predictions
    # --------------------------------------------------

    y_pred = model.predict(X_test)

    y_probability = model.predict_proba(X_test)[:, 1]

    # --------------------------------------------------
    # 7. Evaluation
    # --------------------------------------------------

    accuracy = accuracy_score(y_test, y_pred)

    precision = precision_score(
        y_test,
        y_pred
    )

    recall = recall_score(
        y_test,
        y_pred
    )

    f1 = f1_score(
        y_test,
        y_pred
    )

    roc_auc = roc_auc_score(
        y_test,
        y_probability
    )

    print("\n================================")
    print("       MODEL EVALUATION")
    print("================================")

    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1 Score : {f1:.4f}")
    print(f"ROC-AUC  : {roc_auc:.4f}")

    # --------------------------------------------------
    # 8. Classification report
    # --------------------------------------------------

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            y_pred,
            target_names=[
                "Legitimate",
                "Phishing"
            ]
        )
    )

    # --------------------------------------------------
    # 9. Confusion matrix
    # --------------------------------------------------

    print("Confusion Matrix:")

    cm = confusion_matrix(
        y_test,
        y_pred
    )

    print(cm)

    # --------------------------------------------------
    # 10. Feature importance
    # --------------------------------------------------

    feature_importance = (
        pd.DataFrame({
            "feature": X.columns,
            "importance": model.feature_importances_
        })
        .sort_values(
            by="importance",
            ascending=False
        )
    )

    print("\nTop 10 Feature Importances:")

    print(
        feature_importance.head(10)
        .to_string(index=False)
    )

    # --------------------------------------------------
    # 11. Save model
    # --------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    model.save_model(
        MODEL_PATH
    )

    # --------------------------------------------------
    # 12. Save metrics
    # --------------------------------------------------

    metrics = {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "roc_auc": float(roc_auc),

        "test_size": TEST_SIZE,
        "random_state": RANDOM_STATE,

        "training_samples": len(X_train),
        "testing_samples": len(X_test),

        "features": list(X.columns)
    }

    with open(
        METRICS_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metrics,
            file,
            indent=4
        )

    print("\nModel saved to:")
    print(MODEL_PATH)

    print("\nMetrics saved to:")
    print(METRICS_PATH)


if __name__ == "__main__":
    main()