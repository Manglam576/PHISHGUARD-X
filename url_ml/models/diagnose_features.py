from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "url_features.csv"
)


def main():

    print("Loading dataset...")

    df = pd.read_csv(DATA_PATH)

    print(f"Dataset shape: {df.shape}")

    # --------------------------------------------------
    # 1. Compare important features by class
    # --------------------------------------------------

    important_features = [
        "has_https",
        "path_length",
        "suspicious_tld",
        "digit_count",
        "url_length",
        "subdomain_count",
        "dot_count",
        "hyphen_count",
        "domain_length",
        "letter_count",
    ]

    print("\n========================================")
    print("FEATURE MEANS BY CLASS")
    print("========================================")

    print(
        df.groupby("label")[important_features]
        .mean()
        .T
    )

    # --------------------------------------------------
    # 2. HTTPS distribution
    # --------------------------------------------------

    print("\n========================================")
    print("HTTPS DISTRIBUTION")
    print("========================================")

    https_table = pd.crosstab(
        df["has_https"],
        df["label"],
        normalize="index"
    )

    print(https_table)

    print("\nRaw counts:")

    print(
        pd.crosstab(
            df["has_https"],
            df["label"]
        )
    )

    # --------------------------------------------------
    # 3. Path length statistics
    # --------------------------------------------------

    print("\n========================================")
    print("PATH LENGTH BY CLASS")
    print("========================================")

    print(
        df.groupby("label")["path_length"]
        .describe()
    )

    # --------------------------------------------------
    # 4. Very short path analysis
    # --------------------------------------------------

    print("\n========================================")
    print("PATH LENGTH = 0")
    print("========================================")

    path_zero = df[df["path_length"] == 0]

    print(
        path_zero["label"]
        .value_counts()
    )

    print("\nPercentages:")

    print(
        path_zero["label"]
        .value_counts(
            normalize=True
        )
    )

    # --------------------------------------------------
    # 5. HTTPS only baseline
    # --------------------------------------------------

    print("\n========================================")
    print("HTTPS-ONLY BASELINE")
    print("========================================")

    # Since label 1 = phishing:
    # has_https = 1 predicts legitimate
    # has_https = 0 predicts phishing

    predictions = (
        df["has_https"] == 0
    ).astype(int)

    accuracy = (
        predictions == df["label"]
    ).mean()

    print(
        f"Accuracy using ONLY has_https: "
        f"{accuracy:.4f}"
    )


if __name__ == "__main__":
    main()