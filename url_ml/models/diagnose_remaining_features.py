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

    df = pd.read_csv(DATA_PATH)

    # ---------------------------------------------
    # 1. Important feature means
    # ---------------------------------------------

    features = [
        "suspicious_tld",
        "digit_count",
        "subdomain_count",
        "url_length",
        "domain_length",
        "dot_count",
        "letter_count",
        "hyphen_count",
    ]

    print("\n========================================")
    print("FEATURE MEANS BY CLASS")
    print("========================================")

    print(
        df.groupby("label")[features]
        .mean()
        .T
    )

    # ---------------------------------------------
    # 2. Suspicious TLD distribution
    # ---------------------------------------------

    print("\n========================================")
    print("SUSPICIOUS TLD DISTRIBUTION")
    print("========================================")

    print(
        pd.crosstab(
            df["suspicious_tld"],
            df["label"]
        )
    )

    print("\nNormalized:")

    print(
        pd.crosstab(
            df["suspicious_tld"],
            df["label"],
            normalize="index"
        )
    )

    # ---------------------------------------------
    # 3. Digit count statistics
    # ---------------------------------------------

    print("\n========================================")
    print("DIGIT COUNT BY CLASS")
    print("========================================")

    print(
        df.groupby("label")["digit_count"]
        .describe()
    )

    # ---------------------------------------------
    # 4. Simple digit-only baseline
    # ---------------------------------------------

    median_digit = df["digit_count"].median()

    digit_prediction = (
        df["digit_count"] > median_digit
    ).astype(int)

    accuracy = (
        digit_prediction == df["label"]
    ).mean()

    print("\n========================================")
    print("DIGIT-COUNT-ONLY BASELINE")
    print("========================================")

    print(f"Median digit count: {median_digit}")
    print(f"Accuracy: {accuracy:.4f}")


if __name__ == "__main__":
    main()